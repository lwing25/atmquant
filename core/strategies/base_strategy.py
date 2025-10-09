#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ATMQuant基础策略类
基于vnpy CtaTemplate扩展，添加日志和告警功能
"""

from datetime import time
from typing import List, Tuple, Optional

from vnpy_ctastrategy import CtaTemplate
from vnpy.trader.utility import BarGenerator
from vnpy.trader.constant import Interval
from core.logging.logger_manager import get_logger
from core.logging.alert_manager import alert_manager
from config.trading_sessions_config import (
    get_trading_session_by_symbol,
    TradingSession,
    MarketType
)


class BaseCtaStrategy(CtaTemplate):
    """
    ATMQuant基础策略类
    
    特性：
    1. 自动识别品种的交易时段
    2. 支持日志和告警功能
    3. 小时K线按照实际交易时段合成（如果配置了trading_session）
    """
    
    # 交易时段定义（子类可以重写这些属性）
    # 如果不重写，将自动根据品种代码识别市场类型并使用对应的交易时段
    trading_session: Optional[TradingSession] = None
    
    # 每日收盘时间（用于日线聚合，如果未设置则使用trading_session中的值）
    daily_end: Optional[time] = None
    
    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """初始化策略"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        
        # 初始化日志系统
        self.logger = get_logger(symbol=self.vt_symbol.split('.')[0])
        
        # 策略状态
        self.strategy_status = "未启动"
        
        # 自动识别并设置交易时段
        if self.trading_session is None:
            # 解析品种代码和交易所
            symbol = self.vt_symbol.split('.')[0]
            exchange = self.vt_symbol.split('.')[1] if '.' in self.vt_symbol else ""
            
            # 自动获取交易时段
            self.trading_session = get_trading_session_by_symbol(symbol, exchange)
            self.logger.info(f"自动识别交易时段: {self.trading_session.name}")
        
        # 设置每日收盘时间
        if self.daily_end is None:
            self.daily_end = self.trading_session.daily_end
        
    def on_init(self):
        """策略初始化"""
        self.strategy_status = "初始化中"
        self.logger.info(f"策略 {self.strategy_name} 开始初始化")
        super().on_init()
        
    def on_start(self):
        """策略启动"""
        self.strategy_status = "运行中"
        self.logger.success(f"策略 {self.strategy_name} 启动成功")
        super().on_start()
        
    def on_stop(self):
        """策略停止"""
        self.strategy_status = "已停止"
        self.logger.info(f"策略 {self.strategy_name} 已停止")
        super().on_stop()
        
    def on_trade(self, trade):
        """成交回报"""
        self.logger.success(
            f"成交回报: {trade.direction} {trade.volume}@{trade.price} "
            f"成交金额: {trade.price * trade.volume}"
        )
        super().on_trade(trade)
        
    def on_order(self, order):
        """委托回报"""
        if order.status == "全部成交":
            self.logger.info(f"委托全部成交: {order.direction} {order.volume}@{order.price}")
        elif order.status == "部分成交":
            self.logger.info(f"委托部分成交: {order.direction} {order.volume}@{order.price}")
        elif order.status == "已撤销":
            self.logger.warning(f"委托已撤销: {order.direction} {order.volume}@{order.price}")
        super().on_order(order)
        
    def send_alert(self, message: str, level: str = "INFO"):
        """发送告警消息"""
        try:
            alert_manager.send_alert(
                content=f"📊 策略告警\n策略：{self.strategy_name}\n品种：{self.vt_symbol}\n消息：{message}",
                symbol=self.vt_symbol,
                alert_type="feishu"
            )
        except Exception as e:
            self.logger.error(f"发送告警失败: {e}")
