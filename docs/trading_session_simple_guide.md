# 交易时段K线合成 - 简化使用指南

## 问题

vnpy原生的`BarGenerator`按自然小时（每小时第59分钟）合成K线，对于有休市时间的品种（期货、股票），会导致K线跨越休市时间，技术指标计算错误。

**示例：**
```
原生BarGenerator:
10:00-10:59: 小时K线 ✗（包含10:15-10:30休息时间，数据不连续！）
```

## 解决方案

我们直接在vnpy的`BarGenerator`中添加了`hour_sessions`参数支持，使用非常简单！

## 使用方法

### 方式1：使用BaseCtaStrategy（自动配置，推荐）

```python
from vnpy.trader.utility import BarGenerator
from vnpy.trader.constant import Interval
from core.strategies.base_strategy import BaseCtaStrategy

class MyStrategy(BaseCtaStrategy):
    """
    继承BaseCtaStrategy会自动识别品种的交易时段
    只需在创建BarGenerator时传入hour_sessions即可
    """
    
    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        
        # 创建BarGenerator，传入trading_session的hour_sessions
        self.bg = BarGenerator(
            on_bar=self.on_bar,
            window=1,
            on_window_bar=self.on_hour_bar,
            interval=Interval.HOUR,
            hour_sessions=self.trading_session.hour_sessions  # 就这一行！
        )
    
    def on_bar(self, bar):
        """1分钟K线"""
        self.bg.update_bar(bar)
    
    def on_hour_bar(self, bar):
        """小时K线 - 按交易时段生成，不跨休市"""
        print(f"小时K线: {bar.datetime}")
        # 计算指标...
```

### 方式2：手动指定交易时段

```python
from vnpy_ctastrategy import CtaTemplate
from vnpy.trader.utility import BarGenerator
from vnpy.trader.constant import Interval
from config.trading_sessions_config import get_trading_session_by_symbol

class MyStrategy(CtaTemplate):
    """
    不继承BaseCtaStrategy也可以使用
    手动获取trading_session并传入BarGenerator
    """
    
    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        
        # 手动获取交易时段
        symbol = vt_symbol.split('.')[0]
        exchange = vt_symbol.split('.')[1]
        trading_session = get_trading_session_by_symbol(symbol, exchange)
        
        # 创建BarGenerator，传入hour_sessions
        self.bg = BarGenerator(
            on_bar=self.on_bar,
            window=1,
            on_window_bar=self.on_hour_bar,
            interval=Interval.HOUR,
            hour_sessions=trading_session.hour_sessions  # 传入交易时段
        )
    
    def on_bar(self, bar):
        self.bg.update_bar(bar)
    
    def on_hour_bar(self, bar):
        print(f"小时K线: {bar.datetime}")
```

### 方式3：不使用交易时段（原有行为）

```python
from vnpy.trader.utility import BarGenerator
from vnpy.trader.constant import Interval

# 不传hour_sessions参数，保持原有行为
self.bg = BarGenerator(
    on_bar=self.on_bar,
    window=1,
    on_window_bar=self.on_hour_bar,
    interval=Interval.HOUR
    # 不传hour_sessions，按自然小时合成（原有行为）
)
```

## 完整示例

```python
from vnpy.trader.utility import BarGenerator, ArrayManager
from vnpy.trader.constant import Interval
from core.strategies.base_strategy import BaseCtaStrategy

class DoubleMAStrategy(BaseCtaStrategy):
    """双均线策略 - 使用交易时段K线"""
    
    # 策略参数
    fast_window = 10
    slow_window = 20
    fixed_size = 1
    
    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """初始化"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        
        # 创建BarGenerator - 只需添加hour_sessions参数
        self.bg = BarGenerator(
            on_bar=self.on_bar,
            window=1,
            on_window_bar=self.on_hour_bar,
            interval=Interval.HOUR,
            hour_sessions=self.trading_session.hour_sessions  # 关键！
        )
        
        # 创建ArrayManager
        self.am = ArrayManager()
    
    def on_init(self):
        """策略初始化"""
        self.write_log("策略初始化")
        self.load_bar(10)
    
    def on_bar(self, bar):
        """1分钟K线"""
        self.bg.update_bar(bar)
    
    def on_hour_bar(self, bar):
        """小时K线 - 按交易时段生成"""
        # 更新ArrayManager
        self.am.update_bar(bar)
        if not self.am.inited:
            return
        
        # 计算均线
        fast_ma = self.am.sma(self.fast_window)
        slow_ma = self.am.sma(self.slow_window)
        
        # 生成信号
        if self.pos == 0:
            if fast_ma > slow_ma:
                self.buy(bar.close_price, self.fixed_size)
            elif fast_ma < slow_ma:
                self.short(bar.close_price, self.fixed_size)
        elif self.pos > 0:
            if fast_ma < slow_ma:
                self.sell(bar.close_price, abs(self.pos))
        elif self.pos < 0:
            if fast_ma > slow_ma:
                self.cover(bar.close_price, abs(self.pos))
        
        self.put_event()
```

## K线合成对比

**中国期货日盘（以jm2501为例）：**

配置的交易时段：
```python
hour_sessions=[
    (time(9, 0), time(9, 59)),      # 时段1
    (time(10, 0), time(11, 14)),    # 时段2（包含10:15休息）
    (time(11, 15), time(14, 14)),   # 时段3（跨午休）
    (time(14, 15), time(14, 59))    # 时段4
]
```

**原生BarGenerator（错误）：**
```
09:00-09:59: 小时K线1 ✓
10:00-10:59: 小时K线2 ✗（包含10:15-10:30休息，数据不连续）
11:00-11:59: 小时K线3 ✗（包含11:30-11:59午休）
13:00-13:59: 小时K线4 ✗（包含13:00-13:30午休）
14:00-14:59: 小时K线5 ✓
```

**新BarGenerator（正确）：**
```
09:00-09:59: 小时K线1 ✓（时段1）
10:00-11:14: 小时K线2 ✓（时段2，跳过10:15-10:30休息）
11:15-14:14: 小时K线3 ✓（时段3，跳过11:30-13:30午休）
14:15-14:59: 小时K线4 ✓（时段4）
```

## 自动识别的市场

`BaseCtaStrategy`会自动识别以下品种的交易时段：

- **中国期货**（DCE, SHFE, CZCE, INE, GFEX）→ 4个日盘时段
- **中金所**（CFFEX）→ 4个日盘时段
- **A股**（SSE, SZSE）→ 4个交易时段
- **港股**（SEHK）→ 6个交易时段
- **美股**（NYSE, NASDAQ）→ 7个交易时段

## 常见问题

### Q: 现有策略需要改吗？

**A:** 很简单！只需在创建`BarGenerator`时添加`hour_sessions`参数：

```python
# 旧代码
self.bg = BarGenerator(on_bar=self.on_bar, ...)

# 新代码（添加一个参数）
self.bg = BarGenerator(
    on_bar=self.on_bar, 
    ...,
    hour_sessions=self.trading_session.hour_sessions  # 加这一行
)
```

### Q: 不想使用交易时段怎么办？

**A:** 不传`hour_sessions`参数即可，保持原有行为。

### Q: 如何验证K线是否正确？

**A:** 查看小时K线的时间戳，应该是时段开始时间（如09:00, 10:00, 11:15, 14:15），而不是自然小时。

### Q: 支持自定义交易时段吗？

**A:** 支持！手动创建`TradingSession`并传入即可：

```python
from datetime import time
from config.trading_sessions_config import TradingSession

custom_session = TradingSession(
    name="自定义",
    hour_sessions=[
        (time(9, 30), time(10, 29)),
        (time(10, 30), time(11, 29)),
    ],
    daily_end=time(15, 0),
    timezone="Asia/Shanghai"
)

# 在策略中使用
self.bg = BarGenerator(
    ...,
    hour_sessions=custom_session.hour_sessions
)
```

## 总结

**核心改进：**
- ✅ 直接修改vnpy的`BarGenerator`，无需额外的类
- ✅ 使用简单，只需添加一个`hour_sessions`参数
- ✅ 向后兼容，不传参数保持原有行为
- ✅ K线按实际交易时段合成，不跨休市

**使用步骤：**
1. 继承`BaseCtaStrategy`（自动识别交易时段）
2. 创建`BarGenerator`时传入`hour_sessions`
3. 完成！

就是这么简单！🎉

