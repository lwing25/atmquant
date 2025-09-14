# 以AI量化为生：7.编写自己的第一个量化策略

> 本文是《以AI量化为生》系列的第七篇，我们将从零开始学习vnpy策略开发，修改策略加载机制，分析经典策略，并最终实现一个支持多时间周期的3MA策略。

## 前言

在前面的文章中，我们已经搭建了完整的数据下载系统和日志告警机制。现在系统可以稳定地获取数据并监控运行状态，是时候开始编写我们的第一个量化策略了！

刚开始做量化的时候，我经常遇到这样的困惑：
- vnpy的策略模板怎么用？
- 如何设计交易信号？
- 怎么处理多时间周期？
- 如何实现动态止盈止损？

今天我们要解决的问题：
- **策略模板使用**：掌握vnpy策略开发的基本框架
- **策略加载机制**：修改vnpy使其能加载我们自研的策略
- **经典策略分析**：学习vnpy自带策略的设计思路
- **3MA策略实现**：编写支持多时间周期的移动平均策略

## 一、vnpy策略开发基础

### 1.1 策略模板结构分析

vnpy的策略开发基于`CtaTemplate`基类，让我们先看看它的基本结构：

```python
from vnpy_ctastrategy import (
    CtaTemplate,        # 策略基类
    StopOrder,          # 停止单
    TickData,           # Tick数据
    BarData,            # K线数据
    TradeData,          # 成交数据
    OrderData,          # 委托数据
    BarGenerator,       # K线合成器
    ArrayManager,       # 数组管理器
)

class MyStrategy(CtaTemplate):
    """我的策略"""
    
    # 策略参数
    param1 = 10
    param2 = 20
    
    # 策略变量
    var1 = 0
    var2 = 0
    
    # 参数列表（用于回测优化）
    parameters = ["param1", "param2"]
    
    # 变量列表（用于监控显示）
    variables = ["var1", "var2"]
    
    def on_init(self):
        """策略初始化"""
        pass
        
    def on_start(self):
        """策略启动"""
        pass
        
    def on_stop(self):
        """策略停止"""
        pass
        
    def on_tick(self, tick: TickData):
        """Tick数据更新"""
        pass
        
    def on_bar(self, bar: BarData):
        """K线数据更新"""
        pass
        
    def on_trade(self, trade: TradeData):
        """成交回报"""
        pass
        
    def on_order(self, order: OrderData):
        """委托回报"""
        pass
```

### 1.2 核心组件详解

**BarGenerator（K线合成器）**：
- 将Tick数据合成为K线数据
- 支持多时间周期合成
- 自动处理数据缺失

**ArrayManager（数组管理器）**：
- 提供技术指标计算功能
- 支持SMA、EMA、RSI、ATR等指标
- 自动维护数据数组

**交易函数**：
- `buy(price, volume)`：买入
- `sell(price, volume)`：卖出
- `short(price, volume)`：做空
- `cover(price, volume)`：平空
- `cancel_all()`：撤销所有委托

## 二、修改策略加载机制

### 2.1 问题分析

vnpy默认只加载`vnpy_ctastrategy/strategies`目录下的策略，但我们的自研策略放在`core/strategies`目录。我们需要修改加载机制。

### 2.2 修改策略引擎

我们需要修改vnpy的策略引擎，让它能够加载我们自定义目录下的策略。实际上只需要修改`load_strategy_class`函数：

```python
# vnpy_ctastrategy/engine.py 修改部分
def load_strategy_class(self) -> None:
    """
    Load strategy class from source code.
    """
    # 加载vnpy自带策略
    path1: Path = Path(__file__).parent.joinpath("strategies")
    self.load_strategy_class_from_folder(path1, "vnpy_ctastrategy.strategies")

    # 加载当前目录下的策略
    path2: Path = Path.cwd().joinpath("strategies")
    self.load_strategy_class_from_folder(path2, "strategies")
    
    # 加载ATMQuant自定义策略
    path3: Path = Path(__file__).parent.parent.joinpath("core", "strategies")
    self.load_strategy_class_from_folder(path3, "core.strategies")
```

同样需要修改回测引擎：

```python
# vnpy_ctabacktester/engine.py 修改部分
def load_strategy_class(self) -> None:
    """
    Load strategy class from source code.
    """
    # 加载vnpy自带策略
    app_path: Path = Path(vnpy_ctastrategy.__file__).parent
    path1: Path = app_path.joinpath("strategies")
    self.load_strategy_class_from_folder(path1, "vnpy_ctastrategy.strategies")

    # 加载当前目录下的策略
    path2: Path = Path.cwd().joinpath("strategies")
    self.load_strategy_class_from_folder(path2, "strategies")
    
    # 加载ATMQuant自定义策略
    path3: Path = Path(__file__).parent.parent.joinpath("core", "strategies")
    self.load_strategy_class_from_folder(path3, "core.strategies")
```

### 2.3 创建策略基类

为了保持代码风格的一致性，我们在`core/strategies`目录下创建一个基础策略类：

```python
# core/strategies/base_strategy.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ATMQuant基础策略类
基于vnpy CtaTemplate扩展，添加日志和告警功能
"""

from vnpy_ctastrategy import CtaTemplate
from core.logging.logger_manager import get_logger
from core.logging.alert_manager import alert_manager


class BaseCtaStrategy(CtaTemplate):
    """ATMQuant基础策略类"""
    
    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """初始化策略"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        
        # 初始化日志系统
        self.logger = get_logger(symbol=self.vt_symbol.split('.')[0])
        
        # 策略状态
        self.strategy_status = "未启动"
        
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
```

## 三、经典策略分析

让我们分析几个vnpy自带的经典策略，学习它们的设计思路。

### 3.1 双均线策略（DoubleMaStrategy）

这是最经典的策略之一，让我们看看它的核心逻辑：

```python
def on_bar(self, bar: BarData) -> None:
    """K线数据更新"""
    self.cancel_all()  # 撤销所有委托
    
    am = self.am
    am.update_bar(bar)
    if not am.inited:
        return
    
    # 计算移动平均线
    fast_ma = am.sma(self.fast_window, array=True)
    slow_ma = am.sma(self.slow_window, array=True)
    
    # 获取当前和前一根K线的均线值
    self.fast_ma0 = fast_ma[-1]
    self.fast_ma1 = fast_ma[-2]
    self.slow_ma0 = slow_ma[-1]
    self.slow_ma1 = slow_ma[-2]
    
    # 判断金叉死叉
    cross_over = self.fast_ma0 > self.slow_ma0 and self.fast_ma1 < self.slow_ma1
    cross_below = self.fast_ma0 < self.slow_ma0 and self.fast_ma1 > self.slow_ma1
    
    # 执行交易逻辑
    if cross_over:
        if self.pos == 0:
            self.buy(bar.close_price, 1)
        elif self.pos < 0:
            self.cover(bar.close_price, 1)
            self.buy(bar.close_price, 1)
    elif cross_below:
        if self.pos == 0:
            self.short(bar.close_price, 1)
        elif self.pos > 0:
            self.sell(bar.close_price, 1)
            self.short(bar.close_price, 1)
```

**关键学习点**：
- 使用`array=True`获取历史数据数组
- 通过比较当前和前一根K线的值判断交叉
- 考虑仓位状态进行交易决策

### 3.2 布林带策略（BollChannelStrategy）

这个策略展示了如何使用技术指标和止损：

```python
def on_15min_bar(self, bar: BarData) -> None:
    """15分钟K线更新"""
    self.cancel_all()
    
    am = self.am
    am.update_bar(bar)
    if not am.inited:
        return
    
    # 计算技术指标
    self.boll_up, self.boll_down = am.boll(self.boll_window, self.boll_dev)
    self.cci_value = am.cci(self.cci_window)
    self.atr_value = am.atr(self.atr_window)
    
    if self.pos == 0:
        # 无仓位时的入场逻辑
        if self.cci_value > 0:
            self.buy(self.boll_up, self.fixed_size, True)
        elif self.cci_value < 0:
            self.short(self.boll_down, self.fixed_size, True)
    elif self.pos > 0:
        # 多头仓位的止损逻辑
        self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
        self.long_stop = self.intra_trade_high - self.atr_value * self.sl_multiplier
        self.sell(self.long_stop, abs(self.pos), True)
    elif self.pos < 0:
        # 空头仓位的止损逻辑
        self.intra_trade_low = min(self.intra_trade_low, bar.low_price)
        self.short_stop = self.intra_trade_low + self.atr_value * self.sl_multiplier
        self.cover(self.short_stop, abs(self.pos), True)
```

**关键学习点**：
- 多时间周期处理（1分钟合成15分钟）
- 技术指标组合使用（布林带+CCI）
- 动态止损机制（基于ATR）

### 3.3 多时间周期策略（MultiTimeframeStrategy）

这个策略展示了如何同时使用多个时间周期：

```python
def on_init(self) -> None:
    """策略初始化"""
    # 创建不同时间周期的BarGenerator
    self.bg5 = BarGenerator(self.on_bar, 5, self.on_5min_bar)
    self.am5 = ArrayManager()
    
    self.bg15 = BarGenerator(self.on_bar, 15, self.on_15min_bar)
    self.am15 = ArrayManager()

def on_5min_bar(self, bar: BarData) -> None:
    """5分钟K线更新 - 执行交易"""
    # 只有在15分钟趋势明确时才执行交易
    if not self.ma_trend:
        return
    
    # 5分钟RSI信号
    self.rsi_value = self.am5.rsi(self.rsi_window)
    
    if self.pos == 0:
        if self.ma_trend > 0 and self.rsi_value >= self.rsi_long:
            self.buy(bar.close_price + 5, self.fixed_size)
        elif self.ma_trend < 0 and self.rsi_value <= self.rsi_short:
            self.short(bar.close_price - 5, self.fixed_size)

def on_15min_bar(self, bar: BarData) -> None:
    """15分钟K线更新 - 判断趋势"""
    self.am15.update_bar(bar)
    if not self.am15.inited:
        return
    
    # 15分钟均线判断趋势
    self.fast_ma = self.am15.sma(self.fast_window)
    self.slow_ma = self.am15.sma(self.slow_window)
    
    if self.fast_ma > self.slow_ma:
        self.ma_trend = 1  # 上升趋势
    else:
        self.ma_trend = -1  # 下降趋势
```

**关键学习点**：
- 不同时间周期承担不同职责
- 大周期判断趋势，小周期执行交易
- 通过变量在不同时间周期间传递信息

## 四、3MA策略设计与实现

基于前面的学习，现在我们来设计一个经典的3MA策略。

### 4.1 策略需求分析

**交易信号**：
- 做多：短期MA向上穿过中期MA，且交叉点位于长期MA上方
- 做空：短期MA向下穿过中期MA，且交叉点位于长期MA下方

**技术要求**：
- 支持SMA和EMA两种移动平均线类型
- 支持多时间周期（趋势分析15分钟 + 信号执行5分钟）
- 百分比动态止盈止损机制
- 集成日志和告警系统

### 4.2 策略参数设计

```python
class TripleMaStrategy(BaseCtaStrategy):
    """三均线策略"""
    
    # 策略参数
    short_window = 5      # 短期均线周期
    mid_window = 20       # 中期均线周期  
    long_window = 60      # 长期均线周期
    ma_type = "SMA"       # 均线类型：SMA或EMA
    
    # 多时间周期参数
    signal_timeframe = 15  # 趋势分析时间周期（分钟）
    trade_timeframe = 5    # 信号执行时间周期（分钟）
    
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
```

### 4.3 策略核心实现

```python
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
    
    self.logger.info(f"3MA策略初始化完成 - 趋势分析周期:{self.signal_timeframe}分钟, 信号执行周期:{self.trade_timeframe}分钟")

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
    
    # 只有在趋势分析明确时才执行交易
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
```

## 五、策略回测与优化

### 5.1 使用vnpy回测模块进行回测

vnpy提供了图形化的回测界面，让我们通过界面操作来完成策略回测，这样更直观易懂。

#### 步骤1：启动vnpy主程序

首先启动vnpy主程序：

```bash
cd /Users/mac/code/atmquant
source vnpy_env/bin/activate
python main.py
```

#### 步骤2：进入回测模块

在vnpy主界面中，点击"CTA回测"模块，进入回测界面。

![vnpy主界面](https://files.mdnice.com/user/125063/vnpy-main-interface.png)

#### 步骤3：配置回测参数

在回测界面中配置以下参数：

**基本设置**：
- **策略类**：选择"TripleMaStrategy"
- **本地代码**：rb2501.SHFE（螺纹钢主力合约）
- **K线周期**：1分钟
- **开始日期**：2024-01-01
- **结束日期**：2024-12-31

**交易设置**：
- **手续费率**：0.0003
- **滑点**：0.2
- **合约乘数**：10
- **最小价格变动**：1
- **初始资金**：1000000

**策略参数**：
- **短期均线周期**：5
- **中期均线周期**：20
- **长期均线周期**：60
- **均线类型**：SMA
- **趋势分析周期**：15
- **信号执行周期**：5
- **止损百分比**：2.0
- **止盈百分比**：4.0
- **跟踪止损百分比**：1.0

![回测参数配置](https://files.mdnice.com/user/125063/backtest-parameters.png)

#### 步骤4：运行回测

点击"开始回测"按钮，等待回测完成。

![回测运行中](https://files.mdnice.com/user/125063/backtest-running.png)

#### 步骤5：查看回测结果

回测完成后，可以查看以下结果：

**统计指标**：
- 总收益率
- 年化收益率
- 最大回撤
- 夏普比率
- 胜率
- 盈亏比

**图表分析**：
- 权益曲线
- 回撤曲线
- 每日盈亏
- 持仓分析

![回测结果](https://files.mdnice.com/user/125063/backtest-results.png)

### 5.2 参数优化

#### 第一次优化：均线周期参数

首先优化均线周期参数，这是策略的核心参数。

**优化参数设置**：
- **短期均线周期**：3, 5, 7, 9
- **中期均线周期**：15, 20, 25, 30
- **长期均线周期**：50, 60, 70, 80, 90, 100
- **优化目标**：夏普比率

![均线参数优化](https://files.mdnice.com/user/125063/ma-optimization.png)

**优化结果分析**：
根据优化结果，选择夏普比率最高的参数组合。通常会发现：
- 短期均线：5-7周期表现较好
- 中期均线：20-25周期较为稳定
- 长期均线：60-80周期效果最佳

#### 第二次优化：跟踪止损参数

在确定最佳均线参数后，进一步优化跟踪止损参数。

**优化参数设置**：
- **跟踪止损百分比**：0.5, 1.0, 1.5, 2.0, 2.5, 3.0
- **优化目标**：最大回撤

![跟踪止损优化](https://files.mdnice.com/user/125063/trailing-stop-optimization.png)

**优化结果分析**：
跟踪止损参数的选择需要在风险控制和收益之间找到平衡：
- 过小的跟踪止损：容易被震出，错失趋势
- 过大的跟踪止损：风险控制效果不佳
- 建议选择：1.0-2.0%之间

#### 优化结果应用

将优化得到的最佳参数应用到策略中：

```python
# 优化后的策略参数
{
    "short_window": 5,        # 优化结果
    "mid_window": 20,         # 优化结果  
    "long_window": 60,        # 优化结果
    "trailing_stop_pct": 1.5, # 优化结果
    # 其他参数保持默认值
}
```

### 5.3 回测结果分析

通过回测，我们可以得到以下关键信息：

**策略表现**：
- 年化收益率：15-25%
- 最大回撤：5-10%
- 夏普比率：1.2-1.8
- 胜率：45-55%

**风险特征**：
- 在趋势明显的市场中表现较好
- 在震荡市中可能产生较多假信号
- 需要结合市场环境调整参数

**改进方向**：
- 可以添加市场状态判断
- 考虑加入成交量指标
- 优化止盈止损机制

## 六、下一步计划

在下一篇文章中，我们将进一步完善回测框架的功能：

### 6.1 回测指标增强

**更多实用指标**：
- **风险调整收益指标**：信息比率、卡尔玛比率、索提诺比率
- **交易分析指标**：平均持仓时间、交易频率、滑点分析
- **市场适应性指标**：不同市场环境下的表现分析
- **资金管理指标**：资金利用率、最大连续亏损、恢复因子

**指标可视化**：
- 交互式图表展示
- 多维度指标对比
- 历史表现趋势分析

### 6.2 参数优化功能优化

**优化界面改进**：
- 更直观的参数设置界面
- 实时优化进度显示
- 多目标优化支持

**结果展示优化**：
- 优化结果表格化显示
- 参数敏感性分析图表
- 最优参数组合推荐

**结果导出功能**：
- 优化结果Excel导出
- 参数组合CSV下载
- 回测报告PDF生成

### 6.3 策略开发工具

**策略模板库**：
- 更多经典策略模板
- 策略组合示例
- 最佳实践案例

**调试工具**：
- 策略运行状态监控
- 信号生成过程可视化
- 性能瓶颈分析

通过本篇文章的学习，你已经掌握了：
- vnpy策略开发的基本框架
- 多时间周期策略的设计思路
- 动态止盈止损的实现方法
- 策略回测和优化的完整流程

现在你可以开始编写自己的策略了！记住，策略开发是一个迭代的过程，需要不断地测试、优化和完善。

---

*本文内容仅供学习交流，不构成任何投资建议。交易有风险，投资需谨慎。*
> 本文是《以AI量化为生》系列的第七篇，我们将从零开始学习vnpy策略开发，修改策略加载机制，分析经典策略，并最终实现一个支持多时间周期的3MA策略。

## 前言


![焦煤在3MA策略下的最优回测效果](https://files.mdnice.com/user/125063/5f2fe845-a9c2-4853-82d3-3789947ca9e8.png)

在前面的文章中，我们已经搭建了完整的数据下载系统和日志告警机制。现在系统可以稳定地获取数据并监控运行状态，是时候开始编写我们的第一个量化策略了！

刚开始做量化的时候，我经常遇到这样的困惑：
- vnpy的策略模板怎么用？
- 如何设计交易信号？
- 怎么处理多时间周期？
- 如何实现动态止盈止损？

今天我们要解决的问题：
- **策略模板使用**：掌握vnpy策略开发的基本框架
- **策略加载机制**：修改vnpy使其能加载我们自研的策略
- **经典策略分析**：学习vnpy自带策略的设计思路
- **3MA策略实现**：编写支持多时间周期的移动平均策略

## 一、vnpy策略开发基础

### 1.1 策略模板结构分析

vnpy的策略开发基于`CtaTemplate`基类，让我们先看看它的基本结构：

```python
from vnpy_ctastrategy import (
    CtaTemplate,        # 策略基类
    StopOrder,          # 停止单
    TickData,           # Tick数据
    BarData,            # K线数据
    TradeData,          # 成交数据
    OrderData,          # 委托数据
    BarGenerator,       # K线合成器
    ArrayManager,       # 数组管理器
)

class MyStrategy(CtaTemplate):
    """我的策略"""
    
    # 策略参数
    param1 = 10
    param2 = 20
    
    # 策略变量
    var1 = 0
    var2 = 0
    
    # 参数列表（用于回测优化）
    parameters = ["param1", "param2"]
    
    # 变量列表（用于监控显示）
    variables = ["var1", "var2"]
    
    def on_init(self):
        """策略初始化"""
        pass
        
    def on_start(self):
        """策略启动"""
        pass
        
    def on_stop(self):
        """策略停止"""
        pass
        
    def on_tick(self, tick: TickData):
        """Tick数据更新"""
        pass
        
    def on_bar(self, bar: BarData):
        """K线数据更新"""
        pass
        
    def on_trade(self, trade: TradeData):
        """成交回报"""
        pass
        
    def on_order(self, order: OrderData):
        """委托回报"""
        pass
```

### 1.2 核心组件详解

**BarGenerator（K线合成器）**：
- 将Tick数据合成为K线数据
- 支持多时间周期合成
- 自动处理数据缺失

**ArrayManager（数组管理器）**：
- 提供技术指标计算功能
- 支持SMA、EMA、RSI、ATR等指标
- 自动维护数据数组

**交易函数**：
- `buy(price, volume)`：买入
- `sell(price, volume)`：卖出
- `short(price, volume)`：做空
- `cover(price, volume)`：平空
- `cancel_all()`：撤销所有委托

## 二、修改策略加载机制

### 2.1 问题分析

vnpy默认只加载`vnpy_ctastrategy/strategies`目录下的策略，但我们的自研策略放在`core/strategies`目录。我们需要修改加载机制。

### 2.2 修改策略引擎

我们需要修改vnpy的策略引擎，让它能够加载我们自定义目录下的策略。实际上只需要修改`load_strategy_class`函数：

```python
# vnpy_ctastrategy/engine.py 修改部分
def load_strategy_class(self) -> None:
    """
    Load strategy class from source code.
    """
    # 加载vnpy自带策略
    path1: Path = Path(__file__).parent.joinpath("strategies")
    self.load_strategy_class_from_folder(path1, "vnpy_ctastrategy.strategies")

    # 加载当前目录下的策略
    path2: Path = Path.cwd().joinpath("strategies")
    self.load_strategy_class_from_folder(path2, "strategies")
    
    # 加载ATMQuant自定义策略
    path3: Path = Path(__file__).parent.parent.joinpath("core", "strategies")
    self.load_strategy_class_from_folder(path3, "core.strategies")
```

同样需要修改回测引擎：

```python
# vnpy_ctabacktester/engine.py 修改部分
def load_strategy_class(self) -> None:
    """
    Load strategy class from source code.
    """
    # 加载vnpy自带策略
    app_path: Path = Path(vnpy_ctastrategy.__file__).parent
    path1: Path = app_path.joinpath("strategies")
    self.load_strategy_class_from_folder(path1, "vnpy_ctastrategy.strategies")

    # 加载当前目录下的策略
    path2: Path = Path.cwd().joinpath("strategies")
    self.load_strategy_class_from_folder(path2, "strategies")
    
    # 加载ATMQuant自定义策略
    path3: Path = Path(__file__).parent.parent.joinpath("core", "strategies")
    self.load_strategy_class_from_folder(path3, "core.strategies")
```

### 2.3 创建策略基类

为了保持代码风格的一致性，我们在`core/strategies`目录下创建一个基础策略类：

```python
# core/strategies/base_strategy.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ATMQuant基础策略类
基于vnpy CtaTemplate扩展，添加日志和告警功能
"""

from vnpy_ctastrategy import CtaTemplate
from core.logging.logger_manager import get_logger
from core.logging.alert_manager import alert_manager


class BaseCtaStrategy(CtaTemplate):
    """ATMQuant基础策略类"""
    
    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """初始化策略"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        
        # 初始化日志系统
        self.logger = get_logger(symbol=self.vt_symbol.split('.')[0])
        
        # 策略状态
        self.strategy_status = "未启动"
        
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
```

## 三、经典策略分析

让我们分析几个vnpy自带的经典策略，学习它们的设计思路。

### 3.1 双均线策略（DoubleMaStrategy）

这是最经典的策略之一，让我们看看它的核心逻辑：

```python
def on_bar(self, bar: BarData) -> None:
    """K线数据更新"""
    self.cancel_all()  # 撤销所有委托
    
    am = self.am
    am.update_bar(bar)
    if not am.inited:
        return
    
    # 计算移动平均线
    fast_ma = am.sma(self.fast_window, array=True)
    slow_ma = am.sma(self.slow_window, array=True)
    
    # 获取当前和前一根K线的均线值
    self.fast_ma0 = fast_ma[-1]
    self.fast_ma1 = fast_ma[-2]
    self.slow_ma0 = slow_ma[-1]
    self.slow_ma1 = slow_ma[-2]
    
    # 判断金叉死叉
    cross_over = self.fast_ma0 > self.slow_ma0 and self.fast_ma1 < self.slow_ma1
    cross_below = self.fast_ma0 < self.slow_ma0 and self.fast_ma1 > self.slow_ma1
    
    # 执行交易逻辑
    if cross_over:
        if self.pos == 0:
            self.buy(bar.close_price, 1)
        elif self.pos < 0:
            self.cover(bar.close_price, 1)
            self.buy(bar.close_price, 1)
    elif cross_below:
        if self.pos == 0:
            self.short(bar.close_price, 1)
        elif self.pos > 0:
            self.sell(bar.close_price, 1)
            self.short(bar.close_price, 1)
```

**关键学习点**：
- 使用`array=True`获取历史数据数组
- 通过比较当前和前一根K线的值判断交叉
- 考虑仓位状态进行交易决策

### 3.2 布林带策略（BollChannelStrategy）

这个策略展示了如何使用技术指标和止损：

```python
def on_15min_bar(self, bar: BarData) -> None:
    """15分钟K线更新"""
    self.cancel_all()
    
    am = self.am
    am.update_bar(bar)
    if not am.inited:
        return
    
    # 计算技术指标
    self.boll_up, self.boll_down = am.boll(self.boll_window, self.boll_dev)
    self.cci_value = am.cci(self.cci_window)
    self.atr_value = am.atr(self.atr_window)
    
    if self.pos == 0:
        # 无仓位时的入场逻辑
        if self.cci_value > 0:
            self.buy(self.boll_up, self.fixed_size, True)
        elif self.cci_value < 0:
            self.short(self.boll_down, self.fixed_size, True)
    elif self.pos > 0:
        # 多头仓位的止损逻辑
        self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
        self.long_stop = self.intra_trade_high - self.atr_value * self.sl_multiplier
        self.sell(self.long_stop, abs(self.pos), True)
    elif self.pos < 0:
        # 空头仓位的止损逻辑
        self.intra_trade_low = min(self.intra_trade_low, bar.low_price)
        self.short_stop = self.intra_trade_low + self.atr_value * self.sl_multiplier
        self.cover(self.short_stop, abs(self.pos), True)
```

**关键学习点**：
- 多时间周期处理（1分钟合成15分钟）
- 技术指标组合使用（布林带+CCI）
- 动态止损机制（基于ATR）

### 3.3 多时间周期策略（MultiTimeframeStrategy）

这个策略展示了如何同时使用多个时间周期：

```python
def on_init(self) -> None:
    """策略初始化"""
    # 创建不同时间周期的BarGenerator
    self.bg5 = BarGenerator(self.on_bar, 5, self.on_5min_bar)
    self.am5 = ArrayManager()
    
    self.bg15 = BarGenerator(self.on_bar, 15, self.on_15min_bar)
    self.am15 = ArrayManager()

def on_5min_bar(self, bar: BarData) -> None:
    """5分钟K线更新 - 执行交易"""
    # 只有在15分钟趋势明确时才执行交易
    if not self.ma_trend:
        return
    
    # 5分钟RSI信号
    self.rsi_value = self.am5.rsi(self.rsi_window)
    
    if self.pos == 0:
        if self.ma_trend > 0 and self.rsi_value >= self.rsi_long:
            self.buy(bar.close_price + 5, self.fixed_size)
        elif self.ma_trend < 0 and self.rsi_value <= self.rsi_short:
            self.short(bar.close_price - 5, self.fixed_size)

def on_15min_bar(self, bar: BarData) -> None:
    """15分钟K线更新 - 判断趋势"""
    self.am15.update_bar(bar)
    if not self.am15.inited:
        return
    
    # 15分钟均线判断趋势
    self.fast_ma = self.am15.sma(self.fast_window)
    self.slow_ma = self.am15.sma(self.slow_window)
    
    if self.fast_ma > self.slow_ma:
        self.ma_trend = 1  # 上升趋势
    else:
        self.ma_trend = -1  # 下降趋势
```

**关键学习点**：
- 不同时间周期承担不同职责
- 大周期判断趋势，小周期执行交易
- 通过变量在不同时间周期间传递信息

## 四、3MA策略设计与实现

基于前面的学习，现在我们来设计一个经典的3MA策略。

### 4.1 策略需求分析

**交易信号**：
- 做多：短期MA向上穿过中期MA，且交叉点位于长期MA上方
- 做空：短期MA向下穿过中期MA，且交叉点位于长期MA下方

**技术要求**：
- 支持SMA和EMA两种移动平均线类型
- 支持多时间周期（趋势分析15分钟 + 信号执行5分钟）
- 百分比动态止盈止损机制
- 集成日志和告警系统

### 4.2 策略参数设计

```python
class TripleMaStrategy(BaseCtaStrategy):
    """三均线策略"""
    
    # 策略参数
    short_window = 5      # 短期均线周期
    mid_window = 20       # 中期均线周期  
    long_window = 60      # 长期均线周期
    ma_type = "SMA"       # 均线类型：SMA或EMA
    
    # 多时间周期参数
    signal_timeframe = 15  # 趋势分析时间周期（分钟）
    trade_timeframe = 5    # 信号执行时间周期（分钟）
    
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
```

### 4.3 策略核心实现

```python
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
    
    self.logger.info(f"3MA策略初始化完成 - 趋势分析周期:{self.signal_timeframe}分钟, 信号执行周期:{self.trade_timeframe}分钟")

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
    
    # 只有在趋势分析明确时才执行交易
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
```

## 五、策略回测与优化

### 5.1 使用vnpy回测模块进行回测

我们写完了策略代码，终于来到了效果验证阶段。vnpy提供了图形化的回测界面，让我们通过界面操作来完成策略回测，这样更直观易懂。

#### 步骤1：启动vnpy主程序

首先启动vnpy主程序：

```bash
cd /Users/mac/code/atmquant
source vnpy_env/bin/activate
python main.py
```

#### 步骤2：进入回测模块

在vnpy主界面中，点击"CTA回测"模块，进入回测界面。

![回测界面](https://files.mdnice.com/user/125063/823016d9-17d4-4c2d-903f-87d7f274c091.png)

#### 步骤3：配置回测参数

在回测界面中配置以下参数：

**基本设置**：
- **策略类**：选择"TripleMaStrategy"
- **本地代码**：jm2601.SHFE（焦煤主力合约）
- **K线周期**：1分钟
- **开始日期**：2025-05-01
- **结束日期**：2025-9-13

**交易设置**：
- **手续费率**：0.0001
- **滑点**：0
- **合约乘数**：60
- **最小价格变动**：0.5
- **初始资金**：100000

**策略参数**：
- **短期均线周期**：20
- **中期均线周期**：60
- **长期均线周期**：100
- **均线类型**：SMA   
- **趋势分析周期**：5
- **信号执行周期**：5
- **止损百分比**：2.0
- **止盈百分比**：4.0
- **跟踪止损百分比**：1.0
- **固定手数**：1

![回测参数配置](https://files.mdnice.com/user/125063/5d9ee8ba-01a6-41ea-89c8-59df22213fd1.jpg)

#### 步骤4：运行回测，查看回测结果

点击"开始回测"按钮，等待回测完成。
回测完成后，可以查看以下结果：

![回测结果](https://files.mdnice.com/user/125063/7e1fe7da-98f6-4540-94e8-db67ed0b2e57.png)

**统计指标**：(固定1手)
- 总收益率：39.26%
- 年化收益率：102.41%
- 最大回撤：-3,987.20
- 百分比最大回撤：-2.17%
- 总盈亏：81,874.04
- 夏普比率：4.98

效果还不错，我们接下来进行参数优化，找到效果更优解。

### 5.2 参数优化

#### 第一次优化：均线周期参数

首先优化均线周期参数，这是策略的核心参数。

![均线参数优化](https://files.mdnice.com/user/125063/49b125d0-7628-418a-9f26-7a2e44ba7262.jpg)

**优化参数设置**：
- **短均线周期**：开始：5, 结束：21，步长：2
- **中均线周期**：开始：40, 结束：60，步长：5
- **长均线周期**：开始：80, 结束：120，步长：10
- **优化目标**：夏普比率

**优化结果分析**：

![参数优化结果](https://files.mdnice.com/user/125063/e5710b1e-25e2-46ff-bdc1-4651763a1359.jpg)

根据优化结果，选择夏普比率最高的参数组合。通常会发现：
- 短期均线：7-9周期表现较好
- 中期均线：55-60周期较为稳定
- 长期均线：100周期效果最佳


#### 第二次优化：跟踪止损参数

在确定最佳均线参数后，进一步优化跟踪止损参数。

![跟踪止损优化](https://files.mdnice.com/user/125063/bcf930d5-1777-4e1e-9fb4-6db3e0f0fcca.jpg)

**优化参数设置**：
- **跟踪止损百分比**：开始：0.1，结束：3.0，步长：0.1
- **优化目标**：最大回撤

![跟踪止损参数优化结果](https://files.mdnice.com/user/125063/6115255b-40d3-42d1-b048-23b44f8f9c06.jpg)

**优化结果分析**：
跟踪止损参数的选择需要在风险控制和收益之间找到平衡：
- 过小的跟踪止损：容易被震出，错失趋势
- 过大的跟踪止损：风险控制不佳，收益骤减12%
- 建议选择：0.5-0.8%之间

#### 优化结果应用

将优化得到的最佳参数应用到策略中：

```python
# 优化后的策略参数
{
    "short_window": 7,        # 优化结果
    "mid_window": 55,         # 优化结果  
    "long_window": 100,        # 优化结果
    "trailing_stop_pct": 0.5, # 优化结果
    # 其他参数保持默认值
}
```

### 5.3 回测结果分析

![最佳参数应用回测效果](https://files.mdnice.com/user/125063/49d56d74-9b20-4267-a4b4-524888e0b384.png)

通过回测，我们可以得到以下关键信息：

**策略表现**：
- 总收益率：59.45%
- 年化收益率：155.08%
- 最大回撤：-3,960.00
- 百分比最大回撤：-2.50%
- 总盈亏：59,445.81
- 夏普比率：5.07

**改进方向**：
- 可以添加市场状态判断，避免在震荡市中交易
- 考虑加入成交量指标，量价结合分析，避免假信号
- 优化止盈止损机制，留住更多利润

## 六、下一步计划

在下一篇文章中，我们将进一步完善回测框架的功能：

**增加回测指标**：
- 风险调整收益指标：卡尔玛比率、索提诺比率
- 交易分析指标：平均持仓时间、胜率、盈亏比
- 资金管理指标：最大连续盈利、最大连续亏损等

**参数优化结果界面改进**：
- 增加多参数综合评分
- 多指标参数结果展示
- 保存功能优化

通过本篇文章的学习，你已经掌握了：
- vnpy策略开发的基本框架
- 多时间周期策略的设计思路
- 动态止盈止损的实现方法
- 策略回测和优化的完整流程

学习完这个3MA策略后，如果你有更多优化想法，可以继续自行改进。记住，策略开发是一个迭代的过程，需要不断地测试、优化和完善。

---

*本文内容仅供学习交流，不构成任何投资建议。交易有风险，投资需谨慎。*
