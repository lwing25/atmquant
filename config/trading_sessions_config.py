#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全球金融市场交易时段配置
集中管理不同市场的交易时段定义
"""

from datetime import time
from typing import List, Tuple, Optional, Dict
from enum import Enum


class MarketType(Enum):
    """市场类型枚举"""
    # 中国市场
    CN_FUTURES = "cn_futures"           # 中国期货市场（三大商品交易所）
    CN_CFFEX = "cn_cffex"               # 中金所（股指期货、国债期货）
    CN_A_SHARE = "cn_a_share"           # A股市场
    CN_STAR_MARKET = "cn_star_market"   # 科创板
    CN_GEM = "cn_gem"                   # 创业板
    
    # 香港市场
    HK_STOCK = "hk_stock"               # 港股主板
    HK_FUTURES = "hk_futures"           # 港股期货
    
    # 美国市场
    US_STOCK = "us_stock"               # 美股（NYSE, NASDAQ）
    US_FUTURES = "us_futures"           # 美国期货
    
    # 欧洲市场
    UK_STOCK = "uk_stock"               # 英国股票（伦敦交易所）
    EU_STOCK = "eu_stock"               # 欧洲股票
    
    # 其他亚洲市场
    JP_STOCK = "jp_stock"               # 日本股票
    SG_STOCK = "sg_stock"               # 新加坡股票
    
    # 加密货币
    CRYPTO = "crypto"                   # 加密货币（24小时）
    
    # 默认
    DEFAULT = "default"                 # 默认（按自然小时）


class TradingSession:
    """交易时段定义"""

    def __init__(
        self,
        name: str,
        hour_sessions: Optional[List[Tuple[time, time]]] = None,
        half_hour_sessions: Optional[List[Tuple[time, time]]] = None,
        daily_end: time = time(15, 0),
        timezone: str = "Asia/Shanghai",
        has_night_session: bool = False,
        night_sessions: Optional[List[Tuple[time, time]]] = None,
        night_half_hour_sessions: Optional[List[Tuple[time, time]]] = None
    ):
        """
        初始化交易时段

        Args:
            name: 市场名称
            hour_sessions: 日盘小时时段列表（用于小时K线聚合）
            half_hour_sessions: 日盘半小时时段列表（用于半小时K线聚合）
            daily_end: 每日收盘时间
            timezone: 时区
            has_night_session: 是否有夜盘
            night_sessions: 夜盘时段列表
            night_half_hour_sessions: 夜盘半小时时段列表
        """
        self.name = name
        self.hour_sessions = hour_sessions or []
        self.half_hour_sessions = half_hour_sessions or []
        self.daily_end = daily_end
        self.timezone = timezone
        self.has_night_session = has_night_session
        self.night_sessions = night_sessions or []
        self.night_half_hour_sessions = night_half_hour_sessions or []

    def __repr__(self):
        return f"TradingSession(name='{self.name}', sessions={len(self.hour_sessions)})"


# ==================== 中国市场 ====================

# 中国期货市场（上期所、大商所、郑商所、上期能源）
# 注意：daily_end设置为14:59而非15:00，因为最后一根1分钟K线的时间戳是14:59
# vnpy使用相等判断(==)来检测日K线结束，14:59表示14:59:00-14:59:59的数据
CN_FUTURES_SESSION = TradingSession(
    name="中国期货市场",
    hour_sessions=[
        (time(9, 0), time(9, 59)),      # 第一小时
        (time(10, 0), time(11, 14)),     # 第二小时（含10:15休息）
        (time(11, 15), time(14, 14)),    # 第三小时（跨午休）
        (time(14, 15), time(14, 59))     # 第四小时
    ],
    half_hour_sessions=[
        # 日盘半小时时段（考虑10:15-10:30休市和11:30-13:00午休）
        (time(9, 0), time(9, 29)),       # 第1根：09:00-09:29（30分钟）
        (time(9, 30), time(9, 59)),      # 第2根：09:30-09:59（30分钟）
        (time(10, 0), time(10, 44)),     # 第3根：10:00-10:44（45分钟，跨越10:15-10:30休市）
        (time(10, 45), time(11, 14)),    # 第4根：10:45-11:14（30分钟）
        (time(11, 15), time(13, 44)),    # 第5根：11:15-13:44（150分钟，跨越11:30-13:00午休，实际交易45分钟）
        (time(13, 45), time(14, 14)),    # 第6根：13:45-14:14（30分钟）
        (time(14, 15), time(14, 44)),    # 第7根：14:15-14:44（30分钟）
        (time(14, 45), time(14, 59))     # 第8根：14:45-14:59（15分钟）
    ],
    daily_end=time(14, 59),  # 最后一根1分钟K线的时间戳（市场实际收盘时间是15:00）
    timezone="Asia/Shanghai",
    has_night_session=True,
    night_sessions=[
        (time(21, 0), time(21, 59)),     # 夜盘第1小时
        (time(22, 0), time(22, 59)),     # 夜盘第2小时
        (time(23, 0), time(23, 59)),     # 夜盘第3小时
        (time(0, 0), time(0, 59)),       # 夜盘第4小时（次日）
        (time(1, 0), time(1, 59)),       # 夜盘第5小时
        (time(2, 0), time(2, 29))        # 夜盘第6小时（最后一根K线时间戳是02:29）
    ],
    night_half_hour_sessions=[
        # 夜盘半小时时段（按自然半小时划分）
        (time(21, 0), time(21, 29)),     # 夜盘第1根
        (time(21, 30), time(21, 59)),    # 夜盘第2根
        (time(22, 0), time(22, 29)),     # 夜盘第3根
        (time(22, 30), time(22, 59)),    # 夜盘第4根
        (time(23, 0), time(23, 29)),     # 夜盘第5根
        (time(23, 30), time(23, 59)),    # 夜盘第6根
        (time(0, 0), time(0, 29)),       # 夜盘第7根（次日）
        (time(0, 30), time(0, 59)),      # 夜盘第8根
        (time(1, 0), time(1, 29)),       # 夜盘第9根
        (time(1, 30), time(1, 59)),      # 夜盘第10根
        (time(2, 0), time(2, 29))        # 夜盘第11根（最后一根）
    ]
)

# 中金所（股指期货、国债期货）
CN_CFFEX_SESSION = TradingSession(
    name="中金所",
    hour_sessions=[
        (time(9, 30), time(10, 29)),     # 第一小时
        (time(10, 30), time(11, 29)),    # 第二小时
        (time(13, 0), time(13, 59)),     # 第三小时
        (time(14, 0), time(14, 59))      # 第四小时
    ],
    daily_end=time(14, 59),  # 最后一根1分钟K线的时间戳
    timezone="Asia/Shanghai",
    has_night_session=False
)

# A股市场（沪深主板）
CN_A_SHARE_SESSION = TradingSession(
    name="A股市场",
    hour_sessions=[
        (time(9, 30), time(10, 29)),     # 第一小时
        (time(10, 30), time(11, 29)),    # 第二小时
        (time(13, 0), time(13, 59)),     # 第三小时
        (time(14, 0), time(14, 59))      # 第四小时
    ],
    daily_end=time(14, 59),  # 最后一根1分钟K线的时间戳
    timezone="Asia/Shanghai",
    has_night_session=False
)

# 科创板（盘后固定价格交易延长至15:30）
CN_STAR_MARKET_SESSION = TradingSession(
    name="科创板",
    hour_sessions=[
        (time(9, 30), time(10, 29)),
        (time(10, 30), time(11, 29)),
        (time(13, 0), time(13, 59)),
        (time(14, 0), time(14, 59))
    ],
    daily_end=time(15, 29),  # 盘后交易延长（最后一根1分钟K线的时间戳）
    timezone="Asia/Shanghai",
    has_night_session=False
)

# ==================== 香港市场 ====================

# 港股主板（交易时间：09:30-12:00, 13:00-16:00）
HK_STOCK_SESSION = TradingSession(
    name="港股主板",
    hour_sessions=[
        (time(9, 30), time(10, 29)),     # 第1小时：09:30-10:29（60分钟）
        (time(10, 30), time(11, 29)),    # 第2小时：10:30-11:29（60分钟）
        (time(11, 30), time(13, 29)),    # 第3小时：11:30-13:29（跨午休，实际交易60分钟：11:30-11:59上午盘30分钟+13:00-13:29下午盘30分钟）
        (time(13, 30), time(14, 29)),    # 第4小时：13:30-14:29（60分钟）
        (time(14, 30), time(15, 29)),    # 第5小时：14:30-15:29（60分钟）
        (time(15, 30), time(15, 59))     # 第6时段：15:30-15:59（30分钟）
    ],
    daily_end=time(15, 59),  # 最后一根1分钟K线的时间戳（市场实际收盘时间是16:00）
    timezone="Asia/Hong_Kong",
    has_night_session=False
)

# ==================== 美国市场 ====================

# 美股市场（纽交所、纳斯达克）
US_STOCK_SESSION = TradingSession(
    name="美股市场",
    hour_sessions=[
        (time(9, 30), time(10, 29)),     # 第一小时（美东时间）
        (time(10, 30), time(11, 29)),    # 第二小时
        (time(11, 30), time(12, 29)),    # 第三小时
        (time(12, 30), time(13, 29)),    # 第四小时
        (time(13, 30), time(14, 29)),    # 第五小时
        (time(14, 30), time(15, 29)),    # 第六小时
        (time(15, 30), time(15, 59))     # 最后半小时
    ],
    daily_end=time(15, 59),  # 最后一根1分钟K线的时间戳（市场实际收盘时间是16:00）
    timezone="America/New_York",
    has_night_session=False
)

# ==================== 欧洲市场 ====================

# 英国股票（伦敦交易所）
UK_STOCK_SESSION = TradingSession(
    name="伦敦交易所",
    hour_sessions=[
        (time(8, 0), time(8, 59)),       # 第一小时（英国时间）
        (time(9, 0), time(9, 59)),       # 第二小时
        (time(10, 0), time(10, 59)),     # 第三小时
        (time(11, 0), time(11, 59)),     # 第四小时
        (time(12, 0), time(12, 59)),     # 第五小时
        (time(13, 0), time(13, 59)),     # 第六小时
        (time(14, 0), time(14, 59)),     # 第七小时
        (time(15, 0), time(15, 59)),     # 第八小时
        (time(16, 0), time(16, 29))      # 最后半小时
    ],
    daily_end=time(16, 29),  # 最后一根1分钟K线的时间戳（市场实际收盘时间是16:30）
    timezone="Europe/London",
    has_night_session=False
)

# 欧洲股票（法兰克福、巴黎等）
EU_STOCK_SESSION = TradingSession(
    name="欧洲股票",
    hour_sessions=[
        (time(9, 0), time(9, 59)),       # 第一小时（欧洲中部时间）
        (time(10, 0), time(10, 59)),
        (time(11, 0), time(11, 59)),
        (time(12, 0), time(12, 59)),
        (time(13, 0), time(13, 59)),
        (time(14, 0), time(14, 59)),
        (time(15, 0), time(15, 59)),
        (time(16, 0), time(16, 59)),
        (time(17, 0), time(17, 29))
    ],
    daily_end=time(17, 29),  # 最后一根1分钟K线的时间戳（市场实际收盘时间是17:30）
    timezone="Europe/Paris",
    has_night_session=False
)

# ==================== 亚洲其他市场 ====================

# 日本股票（东京交易所，交易时间：09:00-11:30, 12:30-15:00）
JP_STOCK_SESSION = TradingSession(
    name="东京交易所",
    hour_sessions=[
        (time(9, 0), time(9, 59)),       # 第1小时：09:00-09:59（60分钟）
        (time(10, 0), time(10, 59)),     # 第2小时：10:00-10:59（60分钟）
        (time(11, 0), time(12, 59)),     # 第3小时：11:00-12:59（跨午休，实际交易60分钟：11:00-11:29上午盘30分钟+12:30-12:59下午盘30分钟）
        (time(13, 0), time(13, 59)),     # 第4小时：13:00-13:59（60分钟）
        (time(14, 0), time(14, 59))      # 第5小时：14:00-14:59（60分钟）
    ],
    daily_end=time(14, 59),  # 最后一根1分钟K线的时间戳（市场实际收盘时间是15:00）
    timezone="Asia/Tokyo",
    has_night_session=False
)

# 新加坡股票（交易时间：09:00-12:00, 13:00-17:00）
SG_STOCK_SESSION = TradingSession(
    name="新加坡交易所",
    hour_sessions=[
        (time(9, 0), time(9, 59)),       # 第1小时：09:00-09:59
        (time(10, 0), time(10, 59)),     # 第2小时：10:00-10:59
        (time(11, 0), time(11, 59)),     # 第3小时：11:00-11:59
        (time(13, 0), time(13, 59)),     # 第4小时：13:00-13:59
        (time(14, 0), time(14, 59)),     # 第5小时：14:00-14:59
        (time(15, 0), time(15, 59)),     # 第6小时：15:00-15:59
        (time(16, 0), time(16, 59))      # 第7小时：16:00-16:59
    ],
    daily_end=time(16, 59),  # 最后一根1分钟K线的时间戳（市场实际收盘时间是17:00）
    timezone="Asia/Singapore",
    has_night_session=False
)

# ==================== 加密货币 ====================

# 加密货币（24小时交易，按自然小时）
CRYPTO_SESSION = TradingSession(
    name="加密货币市场",
    hour_sessions=None,  # 24小时，不使用特定时段
    daily_end=time(23, 59),
    timezone="UTC",
    has_night_session=False
)

# ==================== 默认设置 ====================

# 默认时段（按自然小时）
DEFAULT_SESSION = TradingSession(
    name="默认时段",
    hour_sessions=None,  # 不定义，按自然小时处理
    daily_end=time(14, 59),  # 默认使用中国市场的收盘时间
    timezone="Asia/Shanghai",
    has_night_session=False
)


# ==================== 市场配置字典 ====================

TRADING_SESSIONS: Dict[MarketType, TradingSession] = {
    # 中国市场
    MarketType.CN_FUTURES: CN_FUTURES_SESSION,
    MarketType.CN_CFFEX: CN_CFFEX_SESSION,
    MarketType.CN_A_SHARE: CN_A_SHARE_SESSION,
    MarketType.CN_STAR_MARKET: CN_STAR_MARKET_SESSION,
    MarketType.CN_GEM: CN_A_SHARE_SESSION,  # 创业板与主板相同
    
    # 香港市场
    MarketType.HK_STOCK: HK_STOCK_SESSION,
    
    # 美国市场
    MarketType.US_STOCK: US_STOCK_SESSION,
    
    # 欧洲市场
    MarketType.UK_STOCK: UK_STOCK_SESSION,
    MarketType.EU_STOCK: EU_STOCK_SESSION,
    
    # 亚洲其他市场
    MarketType.JP_STOCK: JP_STOCK_SESSION,
    MarketType.SG_STOCK: SG_STOCK_SESSION,
    
    # 加密货币
    MarketType.CRYPTO: CRYPTO_SESSION,
    
    # 默认
    MarketType.DEFAULT: DEFAULT_SESSION,
}


# ==================== 品种到市场类型的映射 ====================

def get_market_type_by_symbol(symbol: str, exchange: str = "") -> MarketType:
    """
    根据品种代码和交易所判断市场类型
    
    Args:
        symbol: 品种代码
        exchange: 交易所代码
    
    Returns:
        市场类型
    """
    symbol_upper = symbol.upper()
    exchange_upper = exchange.upper()
    
    # 中金所品种（股指期货、国债期货）
    cffex_symbols = ["IF", "IC", "IH", "IM", "MO", "T", "TF", "TS"]
    if any(symbol_upper.startswith(s) for s in cffex_symbols) or exchange_upper == "CFFEX":
        return MarketType.CN_CFFEX
    
    # 中国期货市场
    cn_futures_exchanges = ["SHFE", "DCE", "CZCE", "INE", "GFEX"]
    if exchange_upper in cn_futures_exchanges:
        return MarketType.CN_FUTURES
    
    # A股市场
    cn_stock_exchanges = ["SSE", "SZSE"]
    if exchange_upper in cn_stock_exchanges:
        # 科创板（688开头）
        if symbol_upper.startswith("688"):
            return MarketType.CN_STAR_MARKET
        # 创业板（300开头）
        elif symbol_upper.startswith("300"):
            return MarketType.CN_GEM
        # 主板
        else:
            return MarketType.CN_A_SHARE
    
    # 港股
    if exchange_upper in ["SEHK", "HKEX"]:
        return MarketType.HK_STOCK
    
    # 美股
    if exchange_upper in ["NYSE", "NASDAQ", "AMEX"]:
        return MarketType.US_STOCK
    
    # 英国
    if exchange_upper in ["LSE", "LONDON"]:
        return MarketType.UK_STOCK
    
    # 日本
    if exchange_upper in ["TSE", "TOKYO"]:
        return MarketType.JP_STOCK
    
    # 新加坡
    if exchange_upper in ["SGX", "SINGAPORE"]:
        return MarketType.SG_STOCK
    
    # 加密货币
    crypto_exchanges = ["BINANCE", "COINBASE", "HUOBI", "OKEX"]
    if exchange_upper in crypto_exchanges:
        return MarketType.CRYPTO
    
    # 默认
    return MarketType.DEFAULT


def get_trading_session(market_type: MarketType) -> TradingSession:
    """
    获取指定市场的交易时段
    
    Args:
        market_type: 市场类型
    
    Returns:
        交易时段对象
    """
    return TRADING_SESSIONS.get(market_type, DEFAULT_SESSION)


def get_trading_session_by_symbol(symbol: str, exchange: str = "") -> TradingSession:
    """
    根据品种代码获取交易时段
    
    Args:
        symbol: 品种代码
        exchange: 交易所代码
    
    Returns:
        交易时段对象
    """
    market_type = get_market_type_by_symbol(symbol, exchange)
    return get_trading_session(market_type)


# ==================== 便捷函数 ====================

def list_all_markets() -> Dict[str, str]:
    """列出所有支持的市场"""
    return {
        market_type.value: session.name
        for market_type, session in TRADING_SESSIONS.items()
    }


def print_market_sessions(market_type: MarketType):
    """打印市场交易时段信息"""
    session = get_trading_session(market_type)
    print(f"\n{session.name} 交易时段:")
    print(f"  时区: {session.timezone}")
    print(f"  收盘时间: {session.daily_end.strftime('%H:%M')}")
    
    if session.hour_sessions:
        print(f"  日盘时段 ({len(session.hour_sessions)}个):")
        for i, (start, end) in enumerate(session.hour_sessions, 1):
            print(f"    时段{i}: {start.strftime('%H:%M')} - {end.strftime('%H:%M')}")
    else:
        print("  日盘时段: 按自然小时划分")
    
    if session.has_night_session and session.night_sessions:
        print(f"  夜盘时段 ({len(session.night_sessions)}个):")
        for i, (start, end) in enumerate(session.night_sessions, 1):
            print(f"    时段{i}: {start.strftime('%H:%M')} - {end.strftime('%H:%M')}")


if __name__ == "__main__":
    """测试和演示"""
    print("=" * 60)
    print("全球金融市场交易时段配置")
    print("=" * 60)
    
    # 列出所有市场
    print("\n支持的市场:")
    for market_code, market_name in list_all_markets().items():
        print(f"  - {market_code}: {market_name}")
    
    # 测试品种识别
    print("\n\n品种识别测试:")
    test_cases = [
        ("jm2501", "DCE"),
        ("IF2312", "CFFEX"),
        ("600000", "SSE"),
        ("688001", "SSE"),
        ("00700", "SEHK"),
        ("AAPL", "NASDAQ"),
    ]
    
    for symbol, exchange in test_cases:
        market_type = get_market_type_by_symbol(symbol, exchange)
        session = get_trading_session(market_type)
        print(f"  {symbol}.{exchange} → {session.name}")
    
    # 打印几个主要市场的详细信息
    print("\n\n主要市场交易时段详情:")
    for market_type in [
        MarketType.CN_FUTURES,
        MarketType.CN_CFFEX,
        MarketType.CN_A_SHARE,
        MarketType.HK_STOCK,
        MarketType.US_STOCK
    ]:
        print_market_sessions(market_type)

