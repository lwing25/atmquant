from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime, 
    Index, func, and_, desc, asc
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import BarData, TickData
from vnpy.trader.database import (
    BaseDatabase,
    BarOverview,
    TickOverview,
    DB_TZ,
    convert_tz
)
from vnpy.trader.setting import SETTINGS

# SQLAlchemy基础类
Base = declarative_base()

# 数据库连接配置
DATABASE_URL = f"mysql+pymysql://{SETTINGS['database.user']}:{SETTINGS['database.password']}@{SETTINGS['database.host']}:{SETTINGS['database.port']}/{SETTINGS['database.database']}?charset=utf8mb4"

# 创建数据库引擎，使用连接池
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,           # 连接池大小
    max_overflow=20,        # 最大溢出连接数
    pool_pre_ping=True,     # 连接前检查连接是否有效
    pool_recycle=3600,      # 连接回收时间（秒）
    echo=False              # 是否打印SQL语句
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 全局会话对象（保持向后兼容）
db_session = None

def get_db_session():
    """获取数据库会话"""
    global db_session
    if db_session is None:
        db_session = SessionLocal()
    return db_session

def close_db_session(session=None):
    """关闭数据库会话"""
    global db_session
    if session:
        session.close()
    elif db_session:
        db_session.close()
        db_session = None


class DbBarData(Base):
    """K线数据表映射对象"""
    __tablename__ = "dbbardata"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(50), nullable=False)
    exchange = Column(String(20), nullable=False)
    datetime = Column(DateTime, nullable=False)
    interval = Column(String(20), nullable=False)
    volume = Column(Float, nullable=False)
    turnover = Column(Float, nullable=False)
    open_interest = Column(Float, nullable=False)
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)

    __table_args__ = (
        Index('idx_symbol_exchange_interval_datetime', 'symbol', 'exchange', 'interval', 'datetime', unique=True),
    )


class DbTickData(Base):
    """TICK数据表映射对象"""
    __tablename__ = "dbtickdata"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(50), nullable=False)
    exchange = Column(String(20), nullable=False)
    datetime = Column(DateTime(3), nullable=False)  # 支持毫秒
    name = Column(String(100), nullable=False)
    volume = Column(Float, nullable=False)
    turnover = Column(Float, nullable=False)
    open_interest = Column(Float, nullable=False)
    last_price = Column(Float, nullable=False)
    last_volume = Column(Float, nullable=False)
    limit_up = Column(Float, nullable=False)
    limit_down = Column(Float, nullable=False)
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    pre_close = Column(Float, nullable=False)
    
    bid_price_1 = Column(Float, nullable=False)
    bid_price_2 = Column(Float, nullable=True)
    bid_price_3 = Column(Float, nullable=True)
    bid_price_4 = Column(Float, nullable=True)
    bid_price_5 = Column(Float, nullable=True)
    
    ask_price_1 = Column(Float, nullable=False)
    ask_price_2 = Column(Float, nullable=True)
    ask_price_3 = Column(Float, nullable=True)
    ask_price_4 = Column(Float, nullable=True)
    ask_price_5 = Column(Float, nullable=True)
    
    bid_volume_1 = Column(Float, nullable=False)
    bid_volume_2 = Column(Float, nullable=True)
    bid_volume_3 = Column(Float, nullable=True)
    bid_volume_4 = Column(Float, nullable=True)
    bid_volume_5 = Column(Float, nullable=True)
    
    ask_volume_1 = Column(Float, nullable=False)
    ask_volume_2 = Column(Float, nullable=True)
    ask_volume_3 = Column(Float, nullable=True)
    ask_volume_4 = Column(Float, nullable=True)
    ask_volume_5 = Column(Float, nullable=True)
    
    localtime = Column(DateTime(3), nullable=True)

    __table_args__ = (
        Index('idx_symbol_exchange_datetime', 'symbol', 'exchange', 'datetime', unique=True),
    )


class DbBarOverview(Base):
    """K线汇总数据表映射对象"""
    __tablename__ = "dbbaroverview"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(50), nullable=False)
    exchange = Column(String(20), nullable=False)
    interval = Column(String(20), nullable=False)
    count = Column(Integer, nullable=False)
    start = Column(DateTime, nullable=False)
    end = Column(DateTime, nullable=False)

    __table_args__ = (
        Index('idx_symbol_exchange_interval', 'symbol', 'exchange', 'interval', unique=True),
    )


class DbTickOverview(Base):
    """Tick汇总数据表映射对象"""
    __tablename__ = "dbtickoverflow"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(50), nullable=False)
    exchange = Column(String(20), nullable=False)
    count = Column(Integer, nullable=False)
    start = Column(DateTime, nullable=False)
    end = Column(DateTime, nullable=False)

    __table_args__ = (
        Index('idx_symbol_exchange', 'symbol', 'exchange', unique=True),
    )


class MysqlDatabase(BaseDatabase):
    """Mysql数据库接口"""

    def __init__(self) -> None:
        """初始化数据库连接"""
        self.engine = engine
        self.session = get_db_session()
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        print("✓ MySQL数据库连接成功，表结构已初始化")

    def save_bar_data(self, bars: List[BarData], stream: bool = False) -> bool:
        """保存K线数据"""
        if not bars:
            return False
            
        # 读取主键参数
        bar: BarData = bars[0]
        symbol: str = bar.symbol
        exchange: Exchange = bar.exchange
        interval: Interval = bar.interval

        try:
            # 批量插入或更新K线数据
            for bar in bars:
                bar.datetime = convert_tz(bar.datetime)
                
                # 检查是否已存在
                existing = self.session.query(DbBarData).filter(
                    and_(
                        DbBarData.symbol == symbol,
                        DbBarData.exchange == exchange.value,
                        DbBarData.interval == interval.value,
                        DbBarData.datetime == bar.datetime
                    )
                ).first()
                
                if existing:
                    # 更新现有记录
                    existing.volume = bar.volume
                    existing.turnover = bar.turnover
                    existing.open_interest = bar.open_interest
                    existing.open_price = bar.open_price
                    existing.high_price = bar.high_price
                    existing.low_price = bar.low_price
                    existing.close_price = bar.close_price
                else:
                    # 插入新记录
                    db_bar = DbBarData(
                        symbol=symbol,
                        exchange=exchange.value,
                        datetime=bar.datetime,
                        interval=interval.value,
                        volume=bar.volume,
                        turnover=bar.turnover,
                        open_interest=bar.open_interest,
                        open_price=bar.open_price,
                        high_price=bar.high_price,
                        low_price=bar.low_price,
                        close_price=bar.close_price
                    )
                    self.session.add(db_bar)

            # 更新K线汇总数据
            overview = self.session.query(DbBarOverview).filter(
                and_(
                    DbBarOverview.symbol == symbol,
                    DbBarOverview.exchange == exchange.value,
                    DbBarOverview.interval == interval.value
                )
            ).first()

            if not overview:
                overview = DbBarOverview(
                    symbol=symbol,
                    exchange=exchange.value,
                    interval=interval.value,
                    start=bars[0].datetime,
                    end=bars[-1].datetime,
                    count=len(bars)
                )
                self.session.add(overview)
            elif stream:
                overview.end = bars[-1].datetime
                overview.count += len(bars)
            else:
                overview.start = min(bars[0].datetime, overview.start)
                overview.end = max(bars[-1].datetime, overview.end)
                
                # 重新计算总数
                count = self.session.query(DbBarData).filter(
                    and_(
                        DbBarData.symbol == symbol,
                        DbBarData.exchange == exchange.value,
                        DbBarData.interval == interval.value
                    )
                ).count()
                overview.count = count

            self.session.commit()
            return True
            
        except Exception as e:
            self.session.rollback()
            print(f"保存K线数据失败: {e}")
            return False

    def save_tick_data(self, ticks: List[TickData], stream: bool = False) -> bool:
        """保存TICK数据"""
        if not ticks:
            return False
            
        # 读取主键参数
        tick: TickData = ticks[0]
        symbol: str = tick.symbol
        exchange: Exchange = tick.exchange

        try:
            # 批量插入或更新Tick数据
            for tick in ticks:
                tick.datetime = convert_tz(tick.datetime)
                
                # 检查是否已存在
                existing = self.session.query(DbTickData).filter(
                    and_(
                        DbTickData.symbol == symbol,
                        DbTickData.exchange == exchange.value,
                        DbTickData.datetime == tick.datetime
                    )
                ).first()
                
                if existing:
                    # 更新现有记录
                    self._update_tick_data(existing, tick)
                else:
                    # 插入新记录
                    db_tick = self._create_db_tick(tick)
                    self.session.add(db_tick)

            # 更新Tick汇总数据
            overview = self.session.query(DbTickOverview).filter(
                and_(
                    DbTickOverview.symbol == symbol,
                    DbTickOverview.exchange == exchange.value
                )
            ).first()

            if not overview:
                overview = DbTickOverview(
                    symbol=symbol,
                    exchange=exchange.value,
                    start=ticks[0].datetime,
                    end=ticks[-1].datetime,
                    count=len(ticks)
                )
                self.session.add(overview)
            elif stream:
                overview.end = ticks[-1].datetime
                overview.count += len(ticks)
            else:
                overview.start = min(ticks[0].datetime, overview.start)
                overview.end = max(ticks[-1].datetime, overview.end)
                
                # 重新计算总数
                count = self.session.query(DbTickData).filter(
                    and_(
                        DbTickData.symbol == symbol,
                        DbTickData.exchange == exchange.value
                    )
                ).count()
                overview.count = count

            self.session.commit()
            return True
            
        except Exception as e:
            self.session.rollback()
            print(f"保存Tick数据失败: {e}")
            return False
    
    def _create_db_tick(self, tick: TickData) -> DbTickData:
        """创建数据库Tick对象"""
        return DbTickData(
            symbol=tick.symbol,
            exchange=tick.exchange.value,
            datetime=tick.datetime,
            name=tick.name,
            volume=tick.volume,
            turnover=tick.turnover,
            open_interest=tick.open_interest,
            last_price=tick.last_price,
            last_volume=tick.last_volume,
            limit_up=tick.limit_up,
            limit_down=tick.limit_down,
            open_price=tick.open_price,
            high_price=tick.high_price,
            low_price=tick.low_price,
            pre_close=tick.pre_close,
            bid_price_1=tick.bid_price_1,
            bid_price_2=tick.bid_price_2,
            bid_price_3=tick.bid_price_3,
            bid_price_4=tick.bid_price_4,
            bid_price_5=tick.bid_price_5,
            ask_price_1=tick.ask_price_1,
            ask_price_2=tick.ask_price_2,
            ask_price_3=tick.ask_price_3,
            ask_price_4=tick.ask_price_4,
            ask_price_5=tick.ask_price_5,
            bid_volume_1=tick.bid_volume_1,
            bid_volume_2=tick.bid_volume_2,
            bid_volume_3=tick.bid_volume_3,
            bid_volume_4=tick.bid_volume_4,
            bid_volume_5=tick.bid_volume_5,
            ask_volume_1=tick.ask_volume_1,
            ask_volume_2=tick.ask_volume_2,
            ask_volume_3=tick.ask_volume_3,
            ask_volume_4=tick.ask_volume_4,
            ask_volume_5=tick.ask_volume_5,
            localtime=tick.localtime
        )
    
    def _update_tick_data(self, db_tick: DbTickData, tick: TickData):
        """更新数据库Tick对象"""
        db_tick.name = tick.name
        db_tick.volume = tick.volume
        db_tick.turnover = tick.turnover
        db_tick.open_interest = tick.open_interest
        db_tick.last_price = tick.last_price
        db_tick.last_volume = tick.last_volume
        db_tick.limit_up = tick.limit_up
        db_tick.limit_down = tick.limit_down
        db_tick.open_price = tick.open_price
        db_tick.high_price = tick.high_price
        db_tick.low_price = tick.low_price
        db_tick.pre_close = tick.pre_close
        db_tick.bid_price_1 = tick.bid_price_1
        db_tick.bid_price_2 = tick.bid_price_2
        db_tick.bid_price_3 = tick.bid_price_3
        db_tick.bid_price_4 = tick.bid_price_4
        db_tick.bid_price_5 = tick.bid_price_5
        db_tick.ask_price_1 = tick.ask_price_1
        db_tick.ask_price_2 = tick.ask_price_2
        db_tick.ask_price_3 = tick.ask_price_3
        db_tick.ask_price_4 = tick.ask_price_4
        db_tick.ask_price_5 = tick.ask_price_5
        db_tick.bid_volume_1 = tick.bid_volume_1
        db_tick.bid_volume_2 = tick.bid_volume_2
        db_tick.bid_volume_3 = tick.bid_volume_3
        db_tick.bid_volume_4 = tick.bid_volume_4
        db_tick.bid_volume_5 = tick.bid_volume_5
        db_tick.ask_volume_1 = tick.ask_volume_1
        db_tick.ask_volume_2 = tick.ask_volume_2
        db_tick.ask_volume_3 = tick.ask_volume_3
        db_tick.ask_volume_4 = tick.ask_volume_4
        db_tick.ask_volume_5 = tick.ask_volume_5
        db_tick.localtime = tick.localtime

    def load_bar_data(
        self,
        symbol: str,
        exchange: Exchange,
        interval: Interval,
        start: datetime,
        end: datetime
    ) -> List[BarData]:
        """加载K线数据"""
        try:
            db_bars = self.session.query(DbBarData).filter(
                and_(
                    DbBarData.symbol == symbol,
                    DbBarData.exchange == exchange.value,
                    DbBarData.interval == interval.value,
                    DbBarData.datetime >= start,
                    DbBarData.datetime <= end
                )
            ).order_by(DbBarData.datetime).all()

            bars: List[BarData] = []
            for db_bar in db_bars:
                bar = BarData(
                    symbol=db_bar.symbol,
                    exchange=Exchange(db_bar.exchange),
                    datetime=datetime.fromtimestamp(db_bar.datetime.timestamp(), DB_TZ),
                    interval=Interval(db_bar.interval),
                    volume=db_bar.volume,
                    turnover=db_bar.turnover,
                    open_interest=db_bar.open_interest,
                    open_price=db_bar.open_price,
                    high_price=db_bar.high_price,
                    low_price=db_bar.low_price,
                    close_price=db_bar.close_price,
                    gateway_name="DB"
                )
                bars.append(bar)

            return bars
            
        except Exception as e:
            print(f"加载K线数据失败: {e}")
            return []

    def load_tick_data(
        self,
        symbol: str,
        exchange: Exchange,
        start: datetime,
        end: datetime
    ) -> List[TickData]:
        """读取TICK数据"""
        try:
            db_ticks = self.session.query(DbTickData).filter(
                and_(
                    DbTickData.symbol == symbol,
                    DbTickData.exchange == exchange.value,
                    DbTickData.datetime >= start,
                    DbTickData.datetime <= end
                )
            ).order_by(DbTickData.datetime).all()

            ticks: List[TickData] = []
            for db_tick in db_ticks:
                tick = TickData(
                    symbol=db_tick.symbol,
                    exchange=Exchange(db_tick.exchange),
                    datetime=datetime.fromtimestamp(db_tick.datetime.timestamp(), DB_TZ),
                    name=db_tick.name,
                    volume=db_tick.volume,
                    turnover=db_tick.turnover,
                    open_interest=db_tick.open_interest,
                    last_price=db_tick.last_price,
                    last_volume=db_tick.last_volume,
                    limit_up=db_tick.limit_up,
                    limit_down=db_tick.limit_down,
                    open_price=db_tick.open_price,
                    high_price=db_tick.high_price,
                    low_price=db_tick.low_price,
                    pre_close=db_tick.pre_close,
                    bid_price_1=db_tick.bid_price_1,
                    bid_price_2=db_tick.bid_price_2,
                    bid_price_3=db_tick.bid_price_3,
                    bid_price_4=db_tick.bid_price_4,
                    bid_price_5=db_tick.bid_price_5,
                    ask_price_1=db_tick.ask_price_1,
                    ask_price_2=db_tick.ask_price_2,
                    ask_price_3=db_tick.ask_price_3,
                    ask_price_4=db_tick.ask_price_4,
                    ask_price_5=db_tick.ask_price_5,
                    bid_volume_1=db_tick.bid_volume_1,
                    bid_volume_2=db_tick.bid_volume_2,
                    bid_volume_3=db_tick.bid_volume_3,
                    bid_volume_4=db_tick.bid_volume_4,
                    bid_volume_5=db_tick.bid_volume_5,
                    ask_volume_1=db_tick.ask_volume_1,
                    ask_volume_2=db_tick.ask_volume_2,
                    ask_volume_3=db_tick.ask_volume_3,
                    ask_volume_4=db_tick.ask_volume_4,
                    ask_volume_5=db_tick.ask_volume_5,
                    localtime=db_tick.localtime,
                    gateway_name="DB"
                )
                ticks.append(tick)

            return ticks
            
        except Exception as e:
            print(f"加载Tick数据失败: {e}")
            return []

    def delete_bar_data(
        self,
        symbol: str,
        exchange: Exchange,
        interval: Interval
    ) -> int:
        """删除K线数据"""
        try:
            # 删除K线数据
            count = self.session.query(DbBarData).filter(
                and_(
                    DbBarData.symbol == symbol,
                    DbBarData.exchange == exchange.value,
                    DbBarData.interval == interval.value
                )
            ).delete()

            # 删除K线汇总数据
            self.session.query(DbBarOverview).filter(
                and_(
                    DbBarOverview.symbol == symbol,
                    DbBarOverview.exchange == exchange.value,
                    DbBarOverview.interval == interval.value
                )
            ).delete()
            
            self.session.commit()
            return count
            
        except Exception as e:
            self.session.rollback()
            print(f"删除K线数据失败: {e}")
            return 0

    def delete_tick_data(
        self,
        symbol: str,
        exchange: Exchange
    ) -> int:
        """删除TICK数据"""
        try:
            # 删除Tick数据
            count = self.session.query(DbTickData).filter(
                and_(
                    DbTickData.symbol == symbol,
                    DbTickData.exchange == exchange.value
                )
            ).delete()

            # 删除Tick汇总数据
            self.session.query(DbTickOverview).filter(
                and_(
                    DbTickOverview.symbol == symbol,
                    DbTickOverview.exchange == exchange.value
                )
            ).delete()
            
            self.session.commit()
            return count
            
        except Exception as e:
            self.session.rollback()
            print(f"删除Tick数据失败: {e}")
            return 0

    def get_bar_overview(self) -> List[BarOverview]:
        """查询数据库中的K线汇总信息"""
        try:
            # 如果已有K线，但缺失汇总信息，则执行初始化
            data_count = self.session.query(DbBarData).count()
            overview_count = self.session.query(DbBarOverview).count()
            if data_count and not overview_count:
                self.init_bar_overview()

            db_overviews = self.session.query(DbBarOverview).all()
            overviews: List[BarOverview] = []
            for db_overview in db_overviews:
                overview = BarOverview(
                    symbol=db_overview.symbol,
                    exchange=Exchange(db_overview.exchange),
                    interval=Interval(db_overview.interval),
                    count=db_overview.count,
                    start=db_overview.start,
                    end=db_overview.end
                )
                overviews.append(overview)
            return overviews
            
        except Exception as e:
            print(f"获取K线汇总信息失败: {e}")
            return []

    def get_tick_overview(self) -> List[TickOverview]:
        """查询数据库中的Tick汇总信息"""
        try:
            db_overviews = self.session.query(DbTickOverview).all()
            overviews: List[TickOverview] = []
            for db_overview in db_overviews:
                overview = TickOverview(
                    symbol=db_overview.symbol,
                    exchange=Exchange(db_overview.exchange),
                    count=db_overview.count,
                    start=db_overview.start,
                    end=db_overview.end
                )
                overviews.append(overview)
            return overviews
            
        except Exception as e:
            print(f"获取Tick汇总信息失败: {e}")
            return []

    def init_bar_overview(self) -> None:
        """初始化数据库中的K线汇总信息"""
        try:
            # 获取所有不同的symbol, exchange, interval组合
            groups = self.session.query(
                DbBarData.symbol,
                DbBarData.exchange,
                DbBarData.interval,
                func.count(DbBarData.id).label("count")
            ).group_by(
                DbBarData.symbol,
                DbBarData.exchange,
                DbBarData.interval
            ).all()

            for group in groups:
                symbol, exchange, interval, count = group
                
                # 获取开始时间
                start_bar = self.session.query(DbBarData).filter(
                    and_(
                        DbBarData.symbol == symbol,
                        DbBarData.exchange == exchange,
                        DbBarData.interval == interval
                    )
                ).order_by(asc(DbBarData.datetime)).first()

                # 获取结束时间
                end_bar = self.session.query(DbBarData).filter(
                    and_(
                        DbBarData.symbol == symbol,
                        DbBarData.exchange == exchange,
                        DbBarData.interval == interval
                    )
                ).order_by(desc(DbBarData.datetime)).first()

                if start_bar and end_bar:
                    overview = DbBarOverview(
                        symbol=symbol,
                        exchange=exchange,
                        interval=interval,
                        count=count,
                        start=start_bar.datetime,
                        end=end_bar.datetime
                    )
                    self.session.add(overview)

            self.session.commit()
            
        except Exception as e:
            self.session.rollback()
            print(f"初始化K线汇总信息失败: {e}")
