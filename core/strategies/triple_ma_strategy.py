#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三均线策略
支持多时间周期和动态止盈止损的经典移动平均策略
"""

from datetime import datetime
from vnpy_ctastrategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
)
from .base_strategy import BaseCtaStrategy


class TripleMaStrategy(BaseCtaStrategy):
    """三均线策略"""
    
    # 策略参数
    short_window = 5      # 短期均线周期
    mid_window = 20       # 中期均线周期  
    long_window = 60      # 长期均线周期
    ma_type = "SMA"       # 均线类型：SMA或EMA
    
    # 多时间周期参数
    signal_timeframe = 15  # 信号时间周期（分钟）
    trade_timeframe = 5    # 交易时间周期（分钟）
    
    # 止盈止损参数
    stop_loss_pct = 2.0   # 止损百分比
    take_profit_pct = 4.0 # 止盈百分比
    trailing_stop_pct = 1.0  # 跟踪止损百分比
    
    # 策略变量
    short_ma = 0.0
    mid_ma = 0.0
    long_ma = 0.0
    trend_direction = 0   # 趋势方向：1上升，-1下降，0震荡
    
    # 交易状态
    entry_price = 0.0
    highest_price = 0.0
    lowest_price = 0.0
    
    parameters = [
        "short_window", "mid_window", "long_window", "ma_type",
        "signal_timeframe", "trade_timeframe",
        "stop_loss_pct", "take_profit_pct", "trailing_stop_pct"
    ]
    
    variables = [
        "short_ma", "mid_ma", "long_ma", "trend_direction",
        "entry_price", "highest_price", "lowest_price"
    ]

    def on_init(self):
        """策略初始化"""
        super().on_init()
        
        # 创建多时间周期BarGenerator
        self.signal_bg = BarGenerator(
            self.on_bar, 
            self.signal_timeframe, 
            self.on_trend_bar
        )
        self.signal_am = ArrayManager()
        
        self.trade_bg = BarGenerator(
            self.on_bar, 
            self.trade_timeframe, 
            self.on_signal_bar
        )
        self.trade_am = ArrayManager()
        
        # 加载历史数据
        self.load_bar(100)
        
        self.logger.info(f"3MA策略初始化完成 - 信号周期:{self.signal_timeframe}分钟, 交易周期:{self.trade_timeframe}分钟")

    def on_start(self):
        """策略启动"""
        super().on_start()
        self.logger.success("3MA策略启动成功")

    def on_stop(self):
        """策略停止"""
        super().on_stop()
        self.logger.info("3MA策略已停止")

    def on_tick(self, tick: TickData):
        """Tick数据更新"""
        self.signal_bg.update_tick(tick)
        self.trade_bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """K线数据更新"""
        self.signal_bg.update_bar(bar)
        self.trade_bg.update_bar(bar)

    def on_trend_bar(self, bar: BarData):
        """趋势分析 - 15分钟K线更新，判断大趋势方向"""
        self.signal_am.update_bar(bar)
        if not self.signal_am.inited:
            return
        
        # 根据参数选择均线类型
        if self.ma_type == "SMA":
            short_ma_array = self.signal_am.sma(self.short_window, array=True)
            mid_ma_array = self.signal_am.sma(self.mid_window, array=True)
            long_ma_array = self.signal_am.sma(self.long_window, array=True)
        else:  # EMA
            short_ma_array = self.signal_am.ema(self.short_window, array=True)
            mid_ma_array = self.signal_am.ema(self.mid_window, array=True)
            long_ma_array = self.signal_am.ema(self.long_window, array=True)
        
        # 获取当前和前一根K线的均线值
        self.short_ma = short_ma_array[-1]
        mid_ma = mid_ma_array[-1]
        self.long_ma = long_ma_array[-1]
        
        prev_short_ma = short_ma_array[-2]
        prev_mid_ma = mid_ma_array[-2]
        
        # 判断趋势方向
        if self.short_ma > self.long_ma and mid_ma > self.long_ma:
            self.trend_direction = 1  # 上升趋势
        elif self.short_ma < self.long_ma and mid_ma < self.long_ma:
            self.trend_direction = -1  # 下降趋势
        else:
            self.trend_direction = 0  # 震荡趋势
        
        # 记录趋势
        self.logger.info(
            f"趋势分析 - 短期MA:{self.short_ma:.2f}, 中期MA:{mid_ma:.2f}, "
            f"长期MA:{self.long_ma:.2f}, 趋势:{self.trend_direction}"
        )

    def on_signal_bar(self, bar: BarData):
        """信号执行 - 5分钟K线更新，执行具体交易"""
        self.cancel_all()
        
        self.trade_am.update_bar(bar)
        if not self.trade_am.inited:
            return
        
        # 只有在信号时间周期趋势明确时才执行交易
        if self.trend_direction == 0:
            return
        
        # 计算交易信号
        signal = self.calculate_trade_signal(bar)
        
        # 执行交易
        self.execute_trade(bar, signal)

    def calculate_trade_signal(self, bar: BarData) -> int:
        """计算交易信号"""
        if self.trend_direction == 0:
            return 0
        
        # 获取交易时间周期的均线
        if self.ma_type == "SMA":
            short_ma_array = self.trade_am.sma(self.short_window, array=True)
            mid_ma_array = self.trade_am.sma(self.mid_window, array=True)
        else:
            short_ma_array = self.trade_am.ema(self.short_window, array=True)
            mid_ma_array = self.trade_am.ema(self.mid_window, array=True)
        
        if len(short_ma_array) < 2 or len(mid_ma_array) < 2:
            return 0
        
        current_short = short_ma_array[-1]
        current_mid = mid_ma_array[-1]
        prev_short = short_ma_array[-2]
        prev_mid = mid_ma_array[-2]
        
        # 判断交叉信号
        cross_up = current_short > current_mid and prev_short <= prev_mid
        cross_down = current_short < current_mid and prev_short >= prev_mid
        
        # 结合趋势方向判断信号
        if cross_up and self.trend_direction > 0:
            return 1  # 做多信号
        elif cross_down and self.trend_direction < 0:
            return -1  # 做空信号
        else:
            return 0  # 无信号

    def execute_trade(self, bar: BarData, signal: int):
        """执行交易"""
        if signal == 0:
            return
        
        # 获取当前仓位
        pos = self.pos
        
        if signal > 0:  # 做多信号
            if pos == 0:
                # 开多仓
                self.buy(bar.close_price, 1)
                self.entry_price = bar.close_price
                self.highest_price = bar.close_price
                self.lowest_price = bar.close_price
                
                self.logger.success(f"开多仓: {bar.close_price}")
                self.send_alert(f"开多仓信号触发，价格: {bar.close_price}")
                
            elif pos < 0:
                # 平空开多
                self.cover(bar.close_price, abs(pos))
                self.buy(bar.close_price, 1)
                self.entry_price = bar.close_price
                self.highest_price = bar.close_price
                self.lowest_price = bar.close_price
                
                self.logger.success(f"平空开多: {bar.close_price}")
                self.send_alert(f"平空开多信号触发，价格: {bar.close_price}")
        
        elif signal < 0:  # 做空信号
            if pos == 0:
                # 开空仓
                self.short(bar.close_price, 1)
                self.entry_price = bar.close_price
                self.highest_price = bar.close_price
                self.lowest_price = bar.close_price
                
                self.logger.success(f"开空仓: {bar.close_price}")
                self.send_alert(f"开空仓信号触发，价格: {bar.close_price}")
                
            elif pos > 0:
                # 平多开空
                self.sell(bar.close_price, pos)
                self.short(bar.close_price, 1)
                self.entry_price = bar.close_price
                self.highest_price = bar.close_price
                self.lowest_price = bar.close_price
                
                self.logger.success(f"平多开空: {bar.close_price}")
                self.send_alert(f"平多开空信号触发，价格: {bar.close_price}")
        
        # 更新止盈止损
        self.update_stop_loss_take_profit(bar)

    def update_stop_loss_take_profit(self, bar: BarData):
        """更新止盈止损"""
        if self.pos == 0:
            return
        
        # 更新最高价和最低价
        self.highest_price = max(self.highest_price, bar.high_price)
        self.lowest_price = min(self.lowest_price, bar.low_price)
        
        if self.pos > 0:  # 多头仓位
            # 计算止损价格
            stop_loss_price = self.entry_price * (1 - self.stop_loss_pct / 100)
            
            # 计算跟踪止损价格
            trailing_stop_price = self.highest_price * (1 - self.trailing_stop_pct / 100)
            
            # 取更优的止损价格
            final_stop_price = max(stop_loss_price, trailing_stop_price)
            
            # 计算止盈价格
            take_profit_price = self.entry_price * (1 + self.take_profit_pct / 100)
            
            # 设置止损单
            self.sell(final_stop_price, abs(self.pos), True)
            
            # 如果价格达到止盈条件，设置止盈单
            if bar.close_price >= take_profit_price:
                self.sell(take_profit_price, abs(self.pos), True)
                self.logger.success(f"触发止盈: {take_profit_price}")
                self.send_alert(f"多头止盈触发，价格: {take_profit_price}")
        
        elif self.pos < 0:  # 空头仓位
            # 计算止损价格
            stop_loss_price = self.entry_price * (1 + self.stop_loss_pct / 100)
            
            # 计算跟踪止损价格
            trailing_stop_price = self.lowest_price * (1 + self.trailing_stop_pct / 100)
            
            # 取更优的止损价格
            final_stop_price = min(stop_loss_price, trailing_stop_price)
            
            # 计算止盈价格
            take_profit_price = self.entry_price * (1 - self.take_profit_pct / 100)
            
            # 设置止损单
            self.cover(final_stop_price, abs(self.pos), True)
            
            # 如果价格达到止盈条件，设置止盈单
            if bar.close_price <= take_profit_price:
                self.cover(take_profit_price, abs(self.pos), True)
                self.logger.success(f"触发止盈: {take_profit_price}")
                self.send_alert(f"空头止盈触发，价格: {take_profit_price}")

    def on_trade(self, trade: TradeData):
        """成交回报"""
        super().on_trade(trade)
        
        # 更新入场价格
        if self.pos != 0 and self.entry_price == 0:
            self.entry_price = trade.price
            self.highest_price = trade.price
            self.lowest_price = trade.price
        elif self.pos == 0:
            # 平仓时重置状态
            self.entry_price = 0
            self.highest_price = 0
            self.lowest_price = 0
            
            self.logger.info("仓位已平，重置交易状态")
            self.send_alert(f"仓位已平，成交价格: {trade.price}")

    def on_order(self, order: OrderData):
        """委托回报"""
        super().on_order(order)

    def on_stop_order(self, stop_order: StopOrder):
        """停止单回报"""
        pass
