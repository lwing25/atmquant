# 全球金融市场交易时段支持文档

## 概述

ATMQuant 支持全球主要金融市场的交易时段配置，能够根据不同市场的交易规则进行K线聚合。系统会自动识别品种所属市场，并应用对应的交易时段规则。

## 功能特性

### 支持的市场

#### 中国市场
1. **中国期货市场**（上期所、大商所、郑商所、上期能源）
2. **中金所**（股指期货、国债期货）
3. **A股市场**（沪深主板）
4. **科创板**（688开头）
5. **创业板**（300开头）

#### 国际市场
6. **港股市场**（香港交易所）
7. **美股市场**（纽交所、纳斯达克）
8. **英国市场**（伦敦交易所）
9. **欧洲市场**（法兰克福、巴黎等）
10. **日本市场**（东京交易所）
11. **新加坡市场**
12. **加密货币市场**（24小时交易）

### 设计思路

采用集中配置管理的方式：
- 所有市场的交易时段配置集中在 `config/trading_sessions_config.py`
- 自动识别品种所属市场
- 支持自定义扩展新市场
- 如果无法识别，则使用默认规则（自然小时）

## 使用方法

### 1. 自动识别（推荐）

系统会自动根据品种代码和交易所识别市场类型：

**在策略中**：
```python
from core.strategies.base_strategy import BaseCtaStrategy

class MyStrategy(BaseCtaStrategy):
    """自定义策略"""
    
    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        # trading_session 已自动设置
        # 无需手动配置
```

**在图表中**：
```python
from core.charts.enhanced_chart_widget import EnhancedChartWidget

# 创建图表
chart = EnhancedChartWidget()

# 自动识别并设置交易时段
chart.set_trading_session_by_symbol("jm2501", "DCE")

# 加载数据
chart.update_history(bars)
```

### 2. 手动指定市场类型

如果需要明确指定市场类型：

```python
from config.trading_sessions_config import MarketType

# 在图表中设置
chart.set_trading_session(MarketType.CN_FUTURES)  # 中国期货
chart.set_trading_session(MarketType.CN_CFFEX)    # 中金所
chart.set_trading_session(MarketType.CN_A_SHARE)  # A股
chart.set_trading_session(MarketType.HK_STOCK)    # 港股
chart.set_trading_session(MarketType.US_STOCK)    # 美股
```

### 3. 自定义交易时段

如果需要自定义交易时段：

```python
from config.trading_sessions_config import TradingSession
from datetime import time

# 创建自定义交易时段
custom_session = TradingSession(
    name="自定义市场",
    hour_sessions=[
        (time(9, 0), time(10, 59)),
        (time(11, 0), time(14, 59))
    ],
    daily_end=time(15, 0),
    timezone="Asia/Shanghai"
)

# 在策略中使用
class MyStrategy(BaseCtaStrategy):
    trading_session = custom_session

# 在图表中使用
chart.set_trading_session(custom_session)
```

## 时段划分规则

### 期货市场（trading_sessions）

**日盘时段**：
- **时段1**：09:00 - 09:59 (第一小时)
- **时段2**：10:00 - 11:14 (第二小时，包含10:15休息)
- **时段3**：11:15 - 14:14 (第三小时，跨越午休)
- **时段4**：14:15 - 14:59 (第四小时)

**夜盘时段**（按自然小时）：
- 21:00 - 21:59
- 22:00 - 22:59
- 23:00 - 23:59
- 00:00 - 00:59
- 01:00 - 01:59
- 02:00 - 02:30

### 中金所股指期货（cffex_trading_sessions）

**日盘时段**：
- **时段1**：09:30 - 10:29 (第一小时)
- **时段2**：10:30 - 11:29 (第二小时)
- **时段3**：13:00 - 13:59 (第三小时)
- **时段4**：14:00 - 14:59 (第四小时)

**无夜盘交易**

## K线聚合逻辑

### 1分钟 → 5分钟

按照自然时间段聚合，不受交易时段影响：
- 09:00-09:04 → 1根5分钟K线
- 09:05-09:09 → 1根5分钟K线
- ...

### 1分钟 → 15分钟

按照自然时间段聚合，不受交易时段影响：
- 09:00-09:14 → 1根15分钟K线
- 09:15-09:29 → 1根15分钟K线
- ...

### 1分钟 → 1小时

**如果定义了交易时段**：
- 按照交易时段划分
- 日盘：4根小时K线（对应4个时段）
- 夜盘：按自然小时划分

**如果未定义交易时段**：
- 按照自然小时划分
- 09:00-09:59 → 1根小时K线
- 10:00-10:59 → 1根小时K线
- ...

### 1分钟 → 日线

按照交易日聚合，不受交易时段影响：
- 一个交易日的所有1分钟K线 → 1根日K线

## 代码示例

### 判断品种类型并设置时段

```python
def setup_chart_for_symbol(symbol: str, chart: EnhancedChartWidget):
    """根据品种设置图表交易时段"""
    
    # 定义交易时段
    futures_sessions = [
        (time(9, 0), time(9, 59)),
        (time(10, 0), time(11, 14)),
        (time(11, 15), time(14, 14)),
        (time(14, 15), time(14, 59))
    ]
    
    cffex_sessions = [
        (time(9, 30), time(10, 29)),
        (time(10, 30), time(11, 29)),
        (time(13, 0), time(13, 59)),
        (time(14, 0), time(14, 59))
    ]
    
    # 判断是否是中金所品种
    cffex_symbols = ["IF", "IC", "IH", "IM", "MO"]
    is_cffex = any(symbol.startswith(s) for s in cffex_symbols)
    
    # 设置交易时段
    chart.set_trading_sessions(
        trading_sessions=futures_sessions,
        cffex_trading_sessions=cffex_sessions,
        use_cffex=is_cffex
    )
    
    print(f"品种 {symbol} 使用 {'中金所' if is_cffex else '期货市场'} 交易时段")
```

### 策略中使用

```python
class MyStrategy(BaseCtaStrategy):
    """示例策略"""
    
    # 定义交易时段
    trading_sessions = [
        (time(9, 0), time(9, 59)),
        (time(10, 0), time(11, 14)),
        (time(11, 15), time(14, 14)),
        (time(14, 15), time(14, 59))
    ]
    
    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        
        # trading_sessions已经在基础类中初始化
        # 子类可以直接使用
        self.logger.info(f"策略使用 {len(self.trading_sessions)} 个交易时段")
```

## 默认行为

### 如果未设置交易时段

1. **基础策略类**：
   - 自动使用默认的期货市场交易时段
   - 自动使用默认的中金所交易时段

2. **图表组件**：
   - 如果调用了 `set_trading_sessions()`，使用设置的时段
   - 如果未调用，小时K线按自然小时聚合

### 后备方案

- 夜盘时间始终按自然小时聚合
- 如果K线时间不在任何定义的时段内，按自然小时处理
- 确保系统在任何情况下都能正常运行

## 技术实现

### 核心方法

**`_get_hour_session_index(bar_time)`**
```python
def _get_hour_session_index(self, bar_time: time) -> Optional[int]:
    """
    根据交易时段判断当前时间属于哪个小时时段
    
    Returns:
        时段索引 (0-3)，如果不在任何时段内则返回None
    """
    sessions = self.cffex_trading_sessions if self.use_cffex_sessions else self.trading_sessions
    
    if not sessions:
        return None  # 使用自然小时
    
    for idx, (start, end) in enumerate(sessions):
        if start <= bar_time <= end:
            return idx
    
    return None  # 夜盘或未定义时段
```

**`_aggregate_bars()` 中的小时聚合逻辑**
```python
elif interval_str == "1h":
    # 小时线：按照交易时段或自然小时聚合
    bar_time = bar.datetime.time()
    session_index = self._get_hour_session_index(bar_time)
    
    if session_index is not None:
        # 使用交易时段索引作为key
        bar_key = (bar.datetime.date(), f"session_{session_index}")
    else:
        # 使用自然小时作为key（夜盘或未定义交易时段时）
        bar_key = (bar.datetime.date(), bar.datetime.hour)
```

## 常见问题

### Q: 为什么夜盘还是按自然小时划分？

A: 因为夜盘交易时间相对规整（21:00-02:30），且不同品种夜盘时间可能不同，所以夜盘统一按自然小时处理，保持简单和一致性。

### Q: 可以自定义更多的交易时段吗？

A: 可以。您可以定义任意数量的交易时段，系统会按照定义的时段进行聚合。

### Q: 如果K线时间跨越了两个时段怎么办？

A: 系统会根据K线的时间判断它属于哪个时段。确保您的交易时段定义是合理的，没有重叠。

### Q: 是否支持其他市场（如A股）？

A: 是的。您可以为A股定义自己的交易时段：
```python
a_share_sessions = [
    (time(9, 30), time(10, 29)),
    (time(10, 30), time(11, 29)),
    (time(13, 0), time(13, 59)),
    (time(14, 0), time(14, 59))
]
```

## 最佳实践

1. **明确品种类型**：在使用前判断品种属于哪个市场
2. **统一时段定义**：在项目中统一管理交易时段定义
3. **测试验证**：切换到1小时周期验证时段划分是否正确
4. **文档记录**：记录各个品种使用的交易时段规则

## 相关文档

- [多周期图表使用指南](multi_interval_chart_guide.md)
- [增强版K线图表使用指南](enhanced_chart_widget_guide.md)
- [策略开发指南](../core/strategies/README.md)

