#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
在 atmquant.db 中创建所需的表结构
"""

import sys
from pathlib import Path
from peewee import (
    AutoField,
    CharField,
    DateTimeField,
    FloatField,
    IntegerField,
    Model,
    SqliteDatabase as PeeweeSqliteDatabase
)

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 定义数据库文件
DB_PATH = project_root.joinpath("atmquant.db")
db = PeeweeSqliteDatabase(str(DB_PATH))

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
        indexes = ((("symbol", "exchange", "interval", "datetime"), True),)

class DbTickData(Model):
    id = AutoField()
    symbol = CharField()
    exchange = CharField()
    datetime = DateTimeField()
    name = CharField()
    volume = FloatField()
    turnover = FloatField()
    open_interest = FloatField()
    last_price = FloatField()
    last_volume = FloatField()
    limit_up = FloatField()
    limit_down = FloatField()
    open_price = FloatField()
    high_price = FloatField()
    low_price = FloatField()
    pre_close = FloatField()
    bid_price_1 = FloatField()
    bid_price_2 = FloatField(null=True)
    bid_price_3 = FloatField(null=True)
    bid_price_4 = FloatField(null=True)
    bid_price_5 = FloatField(null=True)
    ask_price_1 = FloatField()
    ask_price_2 = FloatField(null=True)
    ask_price_3 = FloatField(null=True)
    ask_price_4 = FloatField(null=True)
    ask_price_5 = FloatField(null=True)
    bid_volume_1 = FloatField()
    bid_volume_2 = FloatField(null=True)
    bid_volume_3 = FloatField(null=True)
    bid_volume_4 = FloatField(null=True)
    bid_volume_5 = FloatField(null=True)
    ask_volume_1 = FloatField()
    ask_volume_2 = FloatField(null=True)
    ask_volume_3 = FloatField(null=True)
    ask_volume_4 = FloatField(null=True)
    ask_volume_5 = FloatField(null=True)
    localtime = DateTimeField(null=True)

    class Meta:
        database = db
        indexes = ((("symbol", "exchange", "datetime"), True),)

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
        indexes = ((("symbol", "exchange", "interval"), True),)

class DbTickOverview(Model):
    id = AutoField()
    symbol = CharField()
    exchange = CharField()
    count = IntegerField()
    start = DateTimeField()
    end = DateTimeField()

    class Meta:
        database = db
        indexes = ((("symbol", "exchange"), True),)

def init_db():
    """初始化数据库表结构"""
    print(f"🚀 开始初始化数据库: {DB_PATH}")
    
    try:
        db.connect()
        db.create_tables([DbBarData, DbTickData, DbBarOverview, DbTickOverview])
        print("✅ 数据库表结构创建成功!")
        print(f"📊 包含的表: {db.get_tables()}")
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
