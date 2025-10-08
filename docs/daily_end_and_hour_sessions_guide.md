# daily_end 和交易时段设计指南

## 1. daily_end 时间设置规范

### 1.1 核心原理

在vnpy框架中，`daily_end`用于判断日K线何时结束。vnpy使用**相等判断**来检测：

```python
# vnpy/trader/utility.py:460
if bar.datetime.time() == self.daily_end:
```

### 1.2 时间戳理解

1分钟K线的时间戳表示该分钟的**开始时间**：
- 时间戳 `14:59` 表示 `14:59:00 - 14:59:59` 这一分钟的数据
- 市场收盘时间 `15:00` 意味着最后一根1分钟K线的时间戳是 `14:59`

### 1.3 设置规则

**规则：daily_end 应设置为最后一根1分钟K线的时间戳，而非市场实际收盘时间**

示例：
```python
# ✅ 正确：中国期货市场15:00收盘
daily_end = time(14, 59)  # 最后一根K线时间戳

# ❌ 错误：这样会导致最后一分钟数据无法被包含在日K线中
daily_end = time(15, 0)
```

### 1.4 各市场设置

| 市场 | 实际收盘时间 | daily_end 设置 | 说明 |
|------|------------|---------------|------|
| 中国期货 | 15:00 | `time(14, 59)` | 最后一根K线14:59 |
| 中金所 | 15:00 | `time(14, 59)` | 同上 |
| A股 | 15:00 | `time(14, 59)` | 同上 |
| 科创板 | 15:30 | `time(15, 29)` | 盘后交易延长 |
| 港股 | 16:00 | `time(15, 59)` | 最后一根K线15:59 |
| 美股 | 16:00 | `time(15, 59)` | 美东时间 |
| 伦交所 | 16:30 | `time(16, 29)` | 英国时间 |
| 欧股 | 17:30 | `time(17, 29)` | 欧洲中部时间 |
| 东京 | 15:00 | `time(14, 59)` | 日本时间 |
| 新加坡 | 17:00 | `time(16, 59)` | 新加坡时间 |
| 加密货币 | 23:59 | `time(23, 59)` | 24小时交易 |

## 2. 交易时段（hour_sessions）设计

### 2.1 时段定义原则

交易时段用于**小时K线聚合**，定义格式为：
```python
hour_sessions = [
    (start_time, end_time),  # 闭区间 [start, end]
    ...
]
```

**重要：时段范围是闭区间，start和end都表示分钟级别的时间点**

### 2.2 时段划分逻辑

#### 中国期货市场示例
```python
hour_sessions = [
    (time(9, 0), time(9, 59)),      # 第1小时：09:00-09:59
    (time(10, 0), time(11, 14)),    # 第2小时：10:00-11:14 (跨过10:15-10:30休盘)
    (time(11, 15), time(14, 14)),   # 第3小时：11:15-14:14 (跨过11:30-13:30午休)
    (time(14, 15), time(14, 59)),   # 第4小时：14:15-14:59
]
```

**设计考虑：**
1. **交易时段不连续**：10:15-10:30、11:30-13:30 是休盘时间
2. **时段合并**：将休盘前后的交易时段合并为一个小时时段
3. **目标**：确保每个交易时段的实际交易时长接近1小时

### 2.3 夜盘时段处理

夜盘可能跨越午夜，需要特殊处理：

```python
night_sessions = [
    (time(21, 0), time(21, 59)),    # 21:00-21:59
    (time(22, 0), time(22, 59)),    # 22:00-22:59
    (time(23, 0), time(23, 59)),    # 23:00-23:59
    (time(0, 0), time(0, 59)),      # 00:00-00:59（次日）
    (time(1, 0), time(1, 59)),      # 01:00-01:59
    (time(2, 0), time(2, 30)),      # 02:00-02:30
]
```

**跨午夜判断逻辑**（enhanced_chart_widget.py）：
```python
if start <= end:
    # 不跨午夜的情况
    if start <= bar_time <= end:
        return session_index
else:
    # 跨午夜的情况（例如 23:00 > 02:30）
    if bar_time >= start or bar_time <= end:
        return session_index
```

## 3. 小时K线聚合算法

### 3.1 聚合流程

```
1. 遍历每根1分钟K线
2. 获取K线时间戳 bar_time
3. 调用 _get_hour_session_index(bar_time) 
4. 如果返回 session_index (非None):
   - 使用 (date, f"session_{session_index}") 作为聚合key
5. 如果返回 None:
   - 使用 (date, hour) 作为聚合key（自然小时）
6. 相同key的K线聚合为一根小时K线
```

### 3.2 聚合规则

| 字段 | 聚合方式 | 说明 |
|------|---------|------|
| open_price | 第一根K线的开盘价 | 时段开盘价 |
| high_price | 所有K线最高价的最大值 | 时段最高价 |
| low_price | 所有K线最低价的最小值 | 时段最低价 |
| close_price | 最后一根K线的收盘价 | 时段收盘价 |
| volume | 所有K线成交量之和 | 时段总成交量 |
| turnover | 所有K线成交额之和 | 时段总成交额 |
| open_interest | 最后一根K线的持仓量 | 时段末持仓量 |

### 3.3 时间戳设置

聚合后的小时K线时间戳设置为**该时段第一根1分钟K线的时间**：

```python
current_bar = BarData(
    datetime=bar.datetime,  # 使用第一根K线的时间
    ...
)
```

## 4. 不同市场的特殊考虑

### 4.1 中国期货市场
- **日盘**：09:00-10:15, 10:30-11:30, 13:30-15:00
- **夜盘**：21:00-次日02:30（部分品种到01:00或23:00）
- **特点**：有多次休盘，需要合并时段

### 4.2 中金所
- **交易时间**：09:30-11:30, 13:00-15:00
- **特点**：开盘时间与期货不同，无夜盘

### 4.3 美股/港股/欧股
- **特点**：连续交易，无中间休盘
- **时段**：按自然小时划分即可

### 4.4 24小时市场（加密货币）
- **设置**：`hour_sessions = None`
- **行为**：自动按自然小时聚合

## 5. 实现验证

### 5.1 测试要点

1. **日K线验证**：
   - 检查 `daily_end` 时间是否正确触发日K线结束
   - 确认最后一分钟数据被包含

2. **小时K线验证**：
   - 不同时段的K线是否正确分隔
   - 跨休盘时段是否正确合并
   - 夜盘跨午夜是否正确处理

3. **边界情况**：
   - 休盘时间的K线如何处理
   - 时段边界的K线归属

### 5.2 调试输出

建议在聚合时输出关键信息：
```python
print(f"Bar时间: {bar_time}, 时段索引: {session_index}, 聚合key: {bar_key}")
```

## 6. 常见问题

### Q1: 为什么 daily_end 要设为 14:59 而不是 15:00？

**A**: vnpy使用相等判断 `bar.datetime.time() == self.daily_end`，而1分钟K线的时间戳是该分钟的开始时间。15:00收盘意味着最后一根K线时间戳是14:59，所以必须设为14:59。

### Q2: hour_sessions 的时间范围是开区间还是闭区间？

**A**: **闭区间** `[start, end]`。例如 `(time(9, 0), time(9, 59))` 包含 09:00 到 09:59 的所有分钟。

### Q3: 如果某个时间不在任何 hour_sessions 中会怎样？

**A**: 返回 `None`，该K线将按**自然小时**聚合，即使用 `(date, hour)` 作为key。

### Q4: 夜盘跨午夜如何处理？

**A**: 代码会检测 `start > end` 的情况，使用 `bar_time >= start or bar_time <= end` 来判断是否属于该时段。

### Q5: 为什么中国期货的 hour_sessions 只有4个时段，实际交易时间更长？

**A**: 考虑到休盘时间，我们将多个交易片段合并为接近1小时的时段。例如：
- 时段2：10:00-11:14 包含 10:00-10:15（15分钟）+ 10:30-11:14（44分钟）= 59分钟
- 时段3：11:15-14:14 跨越午休，包含多个片段

## 7. 代码示例

### 7.1 设置交易时段

```python
from config.trading_sessions_config import TradingSession
from datetime import time

# 自定义市场交易时段
custom_session = TradingSession(
    name="自定义市场",
    hour_sessions=[
        (time(9, 0), time(11, 59)),
        (time(13, 0), time(15, 59))
    ],
    daily_end=time(15, 59),  # 最后一根K线时间戳
    timezone="Asia/Shanghai",
    has_night_session=False
)

# 在策略中使用
class MyStrategy(BaseCtaStrategy):
    trading_session = custom_session
```

### 7.2 在图表中使用

```python
from core.charts.enhanced_chart_widget import EnhancedChartWidget

# 创建图表
chart = EnhancedChartWidget()

# 设置交易时段（方式1：自动识别）
chart.set_trading_session_by_symbol("jm2601", "DCE")

# 设置交易时段（方式2：手动指定）
from config.trading_sessions_config import CN_FUTURES_SESSION
chart.set_trading_session(CN_FUTURES_SESSION)
```

## 8. 更新日志

### v1.0 (2025-10-06)
- 初始版本
- 修复 `daily_end` 设置错误（15:00 -> 14:59）
- 修复小时时段索引判断逻辑
- 添加夜盘跨午夜处理
- 更新所有市场的 `daily_end` 配置

---

**文档维护**: 当添加新市场或修改交易时段时，请及时更新本文档。

