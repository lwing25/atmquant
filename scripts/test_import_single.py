#!/usr/bin/env python3
import os
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
from peewee import *

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from vnpy.trader.constant import Interval, Exchange

DB_PATH = project_root.joinpath("atmquant.db")
db = SqliteDatabase(str(DB_PATH))

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

def test_import():
    db.connect()
    db.create_tables([DbBarData])
    
    file = "/Users/xiaoxialuo/Downloads/akshare_bars/daily/600000.SSE.csv"
    df = pd.read_csv(file)
    print(f"Read {len(df)} rows from {file}")
    
    data = []
    for _, row in df.iterrows():
        ts = pd.to_datetime(row['datetime'])
        dt = ts.to_pydatetime().replace(hour=0, minute=0, second=0, microsecond=0)
        data.append({
            "symbol": "600000",
            "exchange": "SSE",
            "datetime": dt,
            "interval": "d",
            "open_price": float(row['open']),
            "high_price": float(row['high']),
            "low_price": float(row['low']),
            "close_price": float(row['close']),
            "volume": float(row['volume']),
            "turnover": float(row['turnover']),
            "open_interest": 0.0
        })
    
    with db.atomic():
        rows = DbBarData.insert_many(data).on_conflict_replace().execute()
        print(f"Inserted {rows} rows")
    
    count = DbBarData.select().count()
    print(f"Total count in DB: {count}")
    db.close()

if __name__ == "__main__":
    test_import()
