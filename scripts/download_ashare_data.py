#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股历史数据下载器
使用akshare下载中国A股历史交易数据并存入本地数据库
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import akshare as ak
from tqdm import tqdm

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from vnpy.trader.constant import Interval, Exchange
from vnpy.trader.object import BarData
from vnpy.trader.database import get_database

def get_exchange(code: str) -> Exchange:
    """根据股票代码判断交易所"""
    if code.startswith('6') or code.startswith('9') or code.startswith('11'):
        return Exchange.SHSE
    elif code.startswith('0') or code.startswith('3') or code.startswith('12'):
        return Exchange.SZSE
    elif code.startswith('4') or code.startswith('8'):
        return Exchange.BSE
    else:
        # 默认返回上交所
        return Exchange.SHSE

def download_ashare_data(start_date: str = "20200101", limit: int = None):
    """
    下载A股历史数据
    
    Args:
        start_date: 开始日期，格式 YYYYMMDD
        limit: 限制下载的股票数量，None表示全量下载
    """
    print(f"🚀 开始从 akshare 下载 A股数据 (开始日期: {start_date})")
    
    # 1. 获取所有股票列表
    try:
        stock_list = ak.stock_zh_a_spot_em()
        print(f"✓ 成功获取股票列表，共 {len(stock_list)} 只股票")
    except Exception as e:
        print(f"❌ 获取股票列表失败: {e}")
        return

    # 限制下载数量
    if limit:
        stock_list = stock_list.head(limit)
        print(f"⚠️  由于设置了限制，仅下载前 {limit} 只股票")

    # 2. 初始化数据库
    database = get_database()
    
    # 3. 循环下载每只股票的数据
    success_count = 0
    fail_count = 0
    
    for _, row in tqdm(stock_list.iterrows(), total=len(stock_list), desc="下载进度"):
        code = row['代码']
        name = row['名称']
        exchange = get_exchange(code)
        
        try:
            # 下载日线数据
            df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start_date, adjust="qfq")
            
            if df.empty:
                continue
                
            bars = []
            for _, bar_row in df.iterrows():
                dt = pd.to_datetime(bar_row['日期'])
                # CTP/vnpy 习惯日线时间为 00:00:00
                dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
                
                bar = BarData(
                    symbol=code,
                    exchange=exchange,
                    datetime=dt,
                    interval=Interval.DAILY,
                    open_price=float(bar_row['开盘']),
                    high_price=float(bar_row['最高']),
                    low_price=float(bar_row['最低']),
                    close_price=float(bar_row['收盘']),
                    volume=float(bar_row['成交量']),
                    turnover=float(bar_row['成交额']),
                    gateway_name="DB"
                )
                bars.append(bar)
            
            # 保存到数据库
            if bars:
                database.save_bar_data(bars)
                success_count += 1
            
        except Exception as e:
            # print(f"❌ 下载 {code}({name}) 失败: {e}")
            fail_count += 1
            continue

    print("\n" + "="*50)
    print(f"✅ 下载完成!")
    print(f"📈 成功下载: {success_count} 只股票")
    print(f"⚠️  下载失败: {fail_count} 只股票")
    print(f"🗃️  数据已存入数据库")
    print("="*50)

if __name__ == "__main__":
    # 演示目的，默认只下载前10只股票的数据
    # 如果要下载全量，将 limit 设为 None
    import argparse
    
    parser = argparse.ArgumentParser(description='A股历史数据下载器')
    parser.add_argument('--limit', type=int, default=10, help='限制下载的股票数量 (默认10，设为0下载全部)')
    parser.add_argument('--start', type=str, default='20200101', help='开始日期 YYYYMMDD (默认20200101)')
    
    args = parser.parse_args()
    
    limit = args.limit if args.limit > 0 else None
    download_ashare_data(start_date=args.start, limit=limit)
