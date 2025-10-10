# 多周期买卖点连线功能使用指南

## 概述

CandleChartDialog现已支持多周期买卖点连线显示功能。无论在哪个时间周期下查看K线图，系统都能智能地将交易配对并正确显示买入点和卖出点的连线。

## 功能特性

### 1. 智能时间匹配

系统使用三层匹配策略来定位交易在K线图上的位置：

- **精确匹配**：交易时间刚好等于某根K线的时间
- **范围匹配**：交易时间落在某根K线的时间范围内（用于聚合周期）
- **最近匹配**：找时间差最小的K线（兜底策略）

### 2. 支持的时间周期

- **1分钟**：精确显示每笔交易
- **5分钟**：智能匹配到对应的5分钟K线
- **15分钟**：智能匹配到对应的15分钟K线
- **1小时**：智能匹配到对应的小时K线
- **日线**：智能匹配到对应的日K线

### 3. 自动重绘机制

当用户切换时间周期时，系统会：
1. 自动清除旧的交易连线和标记
2. 根据新周期的K线重新计算交易位置
3. 重新绘制所有买卖点连线

## 技术实现

### 核心方法

#### 1. `find_nearest_bar_index(trade_dt: datetime) -> int`

智能查找交易时间对应的K线索引。

**匹配策略**：
1. 优先精确匹配（交易时间 == K线时间）
2. 其次范围匹配（交易时间在K线时间范围内）
3. 最后最近匹配（找时间差最小的K线）

**示例**：
```python
# 1分钟周期：09:32的交易 -> 09:32的K线（精确匹配）
# 5分钟周期：09:32的交易 -> 09:30-09:34的K线（范围匹配）
# 15分钟周期：09:32的交易 -> 09:30-09:44的K线（范围匹配）
```

#### 2. `get_bar_time_range(bar: BarData) -> tuple`

计算K线的时间范围。

**返回**：`(start_time, end_time)` 元组

**示例**：
```python
# 1分钟K线 09:30 -> (09:30, 09:31)
# 5分钟K线 09:30 -> (09:30, 09:35)
# 1小时K线 09:00 -> (09:00, 10:00)
```

#### 3. `_calculate_bar_duration(interval: Interval) -> int`

计算K线周期对应的分钟数。

**支持的周期**：
- 1m → 1分钟
- 5m → 5分钟
- 15m → 15分钟
- 1h → 60分钟
- d → 1440分钟（24小时）

#### 4. `redraw_trades() -> None`

重绘交易连线（用于周期切换后）。

**流程**：
1. 清除现有的交易图形项
2. 使用保存的交易数据重新绘制
3. 自动调用`update_trades()`

## 使用示例

### 基本使用

```python
from vnpy_ctabacktester.ui.widget import CandleChartDialog

# 创建K线图表对话框
dialog = CandleChartDialog()

# 更新历史数据（1分钟K线）
dialog.update_history(minute_bars)

# 更新交易数据（自动保存并绘制）
dialog.update_trades(trades)

# 显示对话框
dialog.exec_()
```

### 周期切换

当用户通过EnhancedChartWidget的周期切换面板切换周期时：

```python
# EnhancedChartWidget会自动调用update_history
# 传入聚合后的K线数据

# update_history内部逻辑：
# 1. 更新K线映射表（dt_ix_map, ix_bar_map）
# 2. 检测到有交易数据（self.trade_data不为空）
# 3. 自动调用redraw_trades()重绘连线
```

**用户体验**：
- ✅ 无需手动操作
- ✅ 切换周期后交易连线自动更新
- ✅ 所有买卖点始终正确定位

### 手动重绘

如果需要手动重绘交易连线：

```python
# 清除当前连线
dialog.items.clear()

# 重新绘制
dialog.redraw_trades()
```

## 数据流程

```
回测完成
  ↓
获取交易数据 (trades)
  ↓
CandleChartDialog.update_trades(trades)
  ↓
保存到 self.trade_data
  ↓
配对交易 (generate_trade_pairs)
  ↓
智能匹配K线索引 (find_nearest_bar_index)
  ↓
绘制连线和标记
```

**周期切换时**：

```
用户点击周期按钮
  ↓
EnhancedChartWidget聚合K线
  ↓
调用 update_history(aggregated_bars)
  ↓
更新映射表 (dt_ix_map, ix_bar_map)
  ↓
检测到 self.trade_data 不为空
  ↓
自动调用 redraw_trades()
  ↓
清除旧连线 → 重新匹配索引 → 重新绘制
```

## 配对逻辑

系统使用FIFO原则配对开平仓交易：

```python
# 多头交易与空头交易反向配对
# 例如：
# 1. 买入开仓 10手 (LONG)
# 2. 卖出平仓 6手  (SHORT) -> 配对前6手
# 3. 卖出平仓 4手  (SHORT) -> 配对剩余4手
```

**配对结果**：
- 开仓时间、价格
- 平仓时间、价格
- 方向（LONG/SHORT）
- 成交量

## 视觉效果

### 连线颜色

- **红色虚线**：盈利交易
  - 多头：平仓价 >= 开仓价
  - 空头：平仓价 <= 开仓价

- **绿色虚线**：亏损交易
  - 多头：平仓价 < 开仓价
  - 空头：平仓价 > 开仓价

### 标记样式

- **多头**：
  - 开仓：黄色下三角（t1）在K线底部
  - 平仓：黄色上三角（t）在K线顶部

- **空头**：
  - 开仓：品红色上三角（t）在K线顶部
  - 平仓：品红色下三角（t1）在K线底部

### 成交量显示

在每个开平仓点旁边显示成交量：`[10]`

## 常见问题

### Q: 为什么有些交易连线不显示？

A: 可能的原因：
1. 交易时间不在当前显示的K线范围内
2. K线数据量太少，无法匹配到对应的K线
3. 使用了`continue`跳过了索引为None的交易

**解决方案**：
- 确保K线数据覆盖所有交易时间
- 检查`find_nearest_bar_index`的返回值

### Q: 切换周期后连线位置不准确？

A: 这不太可能发生。智能匹配算法会：
1. 优先使用范围匹配（最准确）
2. 兜底使用最近匹配

如果确实不准确，请检查：
- `get_bar_time_range`计算是否正确
- `_calculate_bar_duration`是否支持当前周期

### Q: 如何优化大量交易的显示性能？

A: 建议：
1. 限制显示的交易数量
2. 只显示当前视图范围内的交易
3. 使用更大的时间周期（减少交易密度）

## 扩展开发

### 添加新的时间周期

修改`_calculate_bar_duration`方法：

```python
def _calculate_bar_duration(self, interval: Interval) -> int:
    # 添加新周期
    if isinstance(interval, str):
        if interval == "30m":
            return 30
        # ...其他周期
```

### 自定义匹配策略

修改`find_nearest_bar_index`方法：

```python
def find_nearest_bar_index(self, trade_dt: datetime) -> int:
    # 添加自定义策略
    # 策略4：按交易量权重匹配
    # ...
```

### 自定义视觉样式

修改`update_trades`方法中的颜色和标记：

```python
# 修改连线颜色
color = "blue"  # 自定义颜色

# 修改标记样式
scatter_color = "cyan"  # 自定义标记颜色
open_symbol = "o"  # 圆形标记
```

## 相关文档

- [多周期图表使用指南](multi_interval_chart_guide.md)
- [增强版K线图表使用指南](enhanced_chart_widget_guide.md)
- [CTA回测模块架构](../vnpy_ctabacktester/ui/ARCHITECTURE.md)

## 更新日志

### v1.0 (2025-10-09)
- ✅ 实现智能时间匹配功能
- ✅ 支持1m/5m/15m/1h/d多周期
- ✅ 自动重绘机制
- ✅ 保存交易数据用于周期切换
- ✅ 容错处理（找不到索引时跳过）

## 贡献者

- Claude Code Team
