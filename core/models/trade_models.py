"""
交易数据模型

包含实盘交易和回测交易的统一数据模型
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Index, and_, desc, asc
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from vnpy.trader.constant import Exchange, Direction, Offset
from vnpy.trader.object import TradeData as VnpyTradeData

# 使用vnpy_mysql的基础设施
try:
    from vnpy_mysql.mysql_database import Base, engine, get_db_session, close_db_session
except ImportError:
    # 如果vnpy_mysql不可用，创建本地配置
    from vnpy.trader.setting import SETTINGS
    Base = declarative_base()
    
    # 数据库连接配置
    DATABASE_URL = f"mysql+pymysql://{SETTINGS['database.user']}:{SETTINGS['database.password']}@{SETTINGS['database.host']}:{SETTINGS['database.port']}/{SETTINGS['database.database']}?charset=utf8mb4"
    
    # 创建数据库引擎
    engine = create_engine(DATABASE_URL, echo=False)
    
    # 创建会话工厂
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    def get_db_session():
        return SessionLocal()
    
    def close_db_session(session):
        session.close()


class TradeStatus(Enum):
    """
    交易状态枚举
    未平仓1，已平仓2
    """
    UN_CLOSED = 1
    CLOSED = 2


class TradeData(Base):
    """交易记录数据模型"""
    __tablename__ = 'trade_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    # 策略名称
    strategy_name = Column(String(100), nullable=False, index=True)
    # 成交后资金量
    capital = Column(Float, nullable=False)
    # gateway engine的名称
    gateway_name = Column(String(50), nullable=False)
    # 期货合约编码
    symbol = Column(String(50), nullable=False, index=True)
    # 交易所编码
    exchange = Column(String(20), nullable=False)
    # 下单指令id
    orderid = Column(String(50), nullable=False)
    # 交易id
    tradeid = Column(String(50), nullable=False)
    # 交易方向 LONG SHORT
    direction = Column(String(10), nullable=False)
    # 平仓开仓 OPEN CLOSE 或CLOSETODAY
    offset = Column(String(20), nullable=False)
    # 成交价
    price = Column(Float, nullable=False)
    # 成交量
    volume = Column(Integer, nullable=False)
    # 已平仓手数
    closed_volume = Column(Integer, default=0)
    # 状态 1未平仓2已平仓
    status = Column(Integer, nullable=False, default=TradeStatus.UN_CLOSED.value)
    # 交易时间
    datetime = Column(DateTime, nullable=False, index=True)
    # 交易类型：实盘(REAL)或回测(BACKTEST)
    trade_type = Column(String(20), default="REAL", index=True)
    # 回测ID（如果是回测交易）
    backtest_id = Column(String(50), nullable=True, index=True)

    # 创建复合索引
    __table_args__ = (
        Index('idx_strategy_tradeid', 'strategy_name', 'tradeid'),
        Index('idx_strategy_symbol_direction', 'strategy_name', 'symbol', 'direction'),
        Index('idx_backtest_id', 'backtest_id'),
    )


def get_last_trade(strategy_name: str, symbol: str, direction: str):
    """
    获取指定策略、合约、方向的最新开仓交易
    
    Args:
        strategy_name: 策略名称
        symbol: 合约代码
        direction: 交易方向
        
    Returns:
        最新的开仓交易记录，如果没有则返回None
    """
    session = get_db_session()
    try:
        result = session.query(TradeData).filter(
            TradeData.strategy_name == strategy_name,
            TradeData.symbol == symbol,
            TradeData.direction == direction,
            TradeData.offset == Offset.OPEN.name
        ).order_by(TradeData.datetime.desc()).first()
        return result
    finally:
        close_db_session(session)


def get_unclosed_trades(strategy_name: str, symbol: str, direction: str):
    """
    获取所有未完全平仓的交易数据
    
    Args:
        strategy_name: 策略名称
        symbol: 合约代码
        direction: 交易方向
        
    Returns:
        未平仓交易记录列表
    """
    session = get_db_session()
    try:
        results = session.query(TradeData).filter(
            TradeData.strategy_name == strategy_name,
            TradeData.symbol == symbol,
            TradeData.direction == direction,
            TradeData.status == TradeStatus.UN_CLOSED.value,
            TradeData.offset == Offset.OPEN.name
        ).order_by(TradeData.datetime.asc()).all()
        return results
    finally:
        close_db_session(session)


def save_trade_data(strategy_name: str, capital: float, trade: VnpyTradeData, 
                   use_local_time=False, trade_type="REAL", backtest_id=None):
    """
    保存交易数据
    
    Args:
        strategy_name: 策略名称
        capital: 交易后资金量
        trade: vnpy的trade数据
        use_local_time: 是否使用本地时间，回测时建议使用数据虚拟时间
        trade_type: 交易类型，REAL(实盘)或BACKTEST(回测)
        backtest_id: 回测ID（如果是回测交易）
    """
    session = get_db_session()
    try:
        db_trade_data = TradeData(
            strategy_name=strategy_name,
            capital=capital,
            gateway_name=trade.gateway_name,
            symbol=f"{trade.symbol}.{trade.exchange.value}",
            exchange=trade.exchange.value,
            orderid=trade.orderid,
            tradeid=trade.tradeid,
            direction=trade.direction.name,
            offset=trade.offset.name,
            price=trade.price,
            volume=trade.volume,
            closed_volume=trade.closed_volume,
            status=TradeStatus.UN_CLOSED.value if trade.offset == Offset.OPEN else TradeStatus.CLOSED.value,
            datetime=datetime.now() if use_local_time else trade.datetime,
            trade_type=trade_type,
            backtest_id=backtest_id
        )
        session.add(db_trade_data)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        close_db_session(session)


def update_db_trade_data(trade_data: TradeData):
    """
    更新交易数据
    
    Args:
        trade_data: 要更新的交易数据对象
    """
    session = get_db_session()
    try:
        session.merge(trade_data)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        close_db_session(session)


def get_trades_by_backtest_id(backtest_id: str):
    """
    根据回测ID获取所有交易记录
    
    Args:
        backtest_id: 回测ID
        
    Returns:
        该回测的所有交易记录列表
    """
    session = get_db_session()
    try:
        results = session.query(TradeData).filter(
            TradeData.backtest_id == backtest_id
        ).order_by(TradeData.datetime.asc()).all()
        return results
    finally:
        close_db_session(session)


def get_trades_by_strategy_and_period(strategy_name: str, start_date: datetime, end_date: datetime):
    """
    根据策略名称和时间段获取交易记录
    
    Args:
        strategy_name: 策略名称
        start_date: 开始时间
        end_date: 结束时间
        
    Returns:
        指定时间段内的交易记录列表
    """
    session = get_db_session()
    try:
        results = session.query(TradeData).filter(
            TradeData.strategy_name == strategy_name,
            TradeData.datetime >= start_date,
            TradeData.datetime <= end_date
        ).order_by(TradeData.datetime.asc()).all()
        return results
    finally:
        close_db_session(session)


def create_tables():
    """创建交易数据表"""
    try:
        Base.metadata.create_all(engine)
        print("交易数据表创建成功！")
    except Exception as e:
        print(f"创建交易数据表失败: {e}")
        raise e


if __name__ == '__main__':
    # 初始化表结构
    create_tables()