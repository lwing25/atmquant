#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导入本地股票交易数据到数据库 (性能优化版)
源目录：/Users/xiaoxialuo/Downloads/akshare_bars/daily/
目标数据库：./atmquant.db
"""

import os
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
from peewee import (
    AutoField,
    CharField,
    DateTimeField,
    FloatField,
    IntegerField,
    Model,
    SqliteDatabase as PeeweeSqliteDatabase,
    chunked
)

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from vnpy.trader.constant import Interval, Exchange

# 定义数据库连接
DB_PATH = project_root.joinpath("atmquant.db")
db = PeeweeSqliteDatabase(str(DB_PATH), pragmas={
    'journal_mode': 'wal',
    'cache_size': -1024 * 64,  # 64MB
    'synchronous': 'off'
})

class DbBarData(Model):
    id = AutoField()
    symbol = CharField()
    exchange = CharField()
    datetime = DateTimeField()
    interval = CharField()
    volume = FloatField()
    turnover = FloatField()
    open_interest = FloatField()
    open_price = FloatField()
    high_price = FloatField()
    low_price = FloatField()
    close_price = FloatField()

    class Meta:
        database = db
        table_name = "dbbardata"
        indexes = ((("symbol", "exchange", "interval", "datetime"), True),)

class DbBarOverview(Model):
    id = AutoField()
    symbol = CharField()
    exchange = CharField()
    interval = CharField()
    count = IntegerField()
    start = DateTimeField()
    end = DateTimeField()

    class Meta:
        database = db
        table_name = "dbbaroverview"
        indexes = ((("symbol", "exchange", "interval"), True),)

# 交易所映射
EXCHANGE_MAPPING = {
    "SSE": Exchange.SSE.value,
    "SZSE": Exchange.SZSE.value,
    "SHSE": Exchange.SSE.value,
    "BSE": Exchange.BSE.value,
}

def import_local_csv_data(data_dir: str):
    """
    使用 Peewee 直接导入 CSV 格式的股票数据
    """
    data_path = Path(data_dir)
    if not data_path.exists():
        print(f"❌ 目录不存在: {data_dir}")
        return

    csv_files = list(data_path.glob("*.csv"))
    if not csv_files:
        print(f"⚠️  在 {data_dir} 中未找到 CSV 文件")
        return

    print(f"🚀 开始导入数据到 {DB_PATH}，共 {len(csv_files)} 个文件")
    
    # 确保表存在
    db.connect()
    db.create_tables([DbBarData, DbBarOverview])
    
    success_count = 0
    total_bars = 0

    # 2. 循环处理每个文件
    for file in tqdm(csv_files, desc="导入进度"):
        try:
            # 解析文件名
            name_parts = file.stem.split('.')
            if len(name_parts) < 2:
                name_parts = file.stem.split('_')
            
            if len(name_parts) < 2:
                continue

            symbol = name_parts[0]
            exchange_str = name_parts[1].upper()
            exchange_value = EXCHANGE_MAPPING.get(exchange_str)
            
            if not exchange_value:
                continue

            # 读取 CSV
            df = pd.read_csv(file)
            if df.empty:
                continue

            # 转换为字典列表，用于批量插入
            data_to_insert = []
            start_dt = None
            end_dt = None
            
            for _, row in df.iterrows():
                # 转换为 Python datetime 对象，避免 Timestamp 兼容性问题
                ts = pd.to_datetime(row['datetime'])
                dt = ts.to_pydatetime()
                dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
                
                if start_dt is None or dt < start_dt:
                    start_dt = dt
                if end_dt is None or dt > end_dt:
                    end_dt = dt
                
                data_to_insert.append({
                    "symbol": symbol,
                    "exchange": exchange_value,
                    "datetime": dt,
                    "interval": Interval.DAILY.value,
                    "open_price": float(row['open']),
                    "high_price": float(row['high']),
                    "low_price": float(row['low']),
                    "close_price": float(row['close']),
                    "volume": float(row['volume']),
                    "turnover": float(row['turnover']),
                    "open_interest": 0.0
                })
            
            # 批量插入
            with db.atomic():
                for c in chunked(data_to_insert, 1000):
                    DbBarData.insert_many(c).on_conflict_replace().execute()
            
            # 更新汇总信息
            DbBarOverview.insert(
                symbol=symbol,
                exchange=exchange_value,
                interval=Interval.DAILY.value,
                count=len(data_to_insert),
                start=start_dt,
                end=end_dt
            ).on_conflict(
                conflict_target=[DbBarOverview.symbol, DbBarOverview.exchange, DbBarOverview.interval],
                preserve=[DbBarOverview.count, DbBarOverview.start, DbBarOverview.end]
            ).execute()

            success_count += 1
            total_bars += len(data_to_insert)
                
        except Exception as e:
            print(f"❌ 导入文件 {file.name} 失败: {e}")
            import traceback
            traceback.print_exc()
            continue

    db.close()
    print("\n" + "="*50)
    print(f"✅ 导入完成!")
    print(f"📈 成功处理文件: {success_count} / {len(csv_files)}")
    print(f"📊 累计导入数据: {total_bars} 条 K 线")
    print("="*50)

if __name__ == "__main__":
    SOURCE_DIR = "/Users/xiaoxialuo/Downloads/akshare_bars/daily/"
    import_local_csv_data(SOURCE_DIR)
