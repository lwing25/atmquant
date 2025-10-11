# 四图视图功能说明

## 功能概述

四图视图（Quad Chart）是ATMQuant量化交易系统的高级图表功能，在双图视图的基础上扩展而来。它可以同时显示四个不同周期的图表，以2x2网格布局排列，帮助交易者全面把握市场在不同时间尺度上的节奏。

## 核心特性

### 1. 2x2网格布局
- **左上图表**：默认5分钟周期
- **右上图表**：默认15分钟周期
- **左下图表**：默认1小时周期
- **右下图表**：默认日线周期

### 2. 时间轴同步
- 四个图表的时间轴自动同步
- 拖动或缩放任一图表，其他三个图表自动跟随
- 智能时间映射算法，确保不同周期间的精确对齐

### 3. 自适应布局
- 支持拖拽调整各图表的比例
- 垂直和水平分割器可独立调整
- 灵活适应不同屏幕尺寸

### 4. 完整功能支持
- 周期按钮自动激活
- 交易信号连线显示
- K线、成交量、技术指标完整显示
- 所有EnhancedChartWidget的功能都可用

## 使用方法

### 基本使用

1. **打开回测图表**
   ```python
   # 运行回测后，点击"图表"按钮
   ```

2. **切换到四图模式**
   - 点击顶部工具栏的"四图"按钮
   - 系统自动切换到2x2布局
   - 四个周期的图表同时显示

3. **调整图表比例**
   - 拖动水平分割线调整上下比例
   - 拖动垂直分割线调整左右比例
   - 可以让重要周期占据更大空间

### 高级功能

#### 1. 周期切换
每个图表都有独立的周期切换面板（左侧垂直按钮组）：
- 1分钟（1m）
- 5分钟（5m）
- 15分钟（15m）
- 1小时（1h）
- 日线（d）

切换周期时，该图表会重新聚合数据，其他图表保持不变。

#### 2. 时间轴同步
- **自动同步**：拖动任一图表，其他图表自动跟随
- **智能匹配**：不同周期间使用二分查找最近K线
- **防止循环**：内置循环检测机制

#### 3. 交易信号显示
- 买入信号：绿色三角形（向上）
- 卖出信号：红色三角形（向下）
- 平仓连线：连接开平仓位置
- 所有四个图表同步显示

## 技术架构

### 核心组件

#### 1. QuadChartWidget
主要的四图容器组件，负责：
- 创建和管理四个EnhancedChartWidget实例
- 布局管理（2x2网格）
- 数据分发和聚合
- 周期切换回调

#### 2. QuadChartTimeAxisSync
时间轴同步管理器，负责：
- 监听四个图表的X轴范围变化
- 智能时间映射和索引转换
- 同步其他图表到变化源
- 防止循环同步

### 数据流程

```
1分钟K线数据 (base_minute_bars)
    ↓
聚合为不同周期
    ↓
┌─────────┬─────────┐
│  5分钟  │ 15分钟  │
├─────────┼─────────┤
│  1小时  │  日线   │
└─────────┴─────────┘
    ↓
时间轴同步
    ↓
交易信号显示
```

## 代码示例

### 创建四图组件

```python
from core.charts import QuadChartWidget

# 创建四图组件（使用默认周期）
quad_chart = QuadChartWidget()

# 或自定义周期
quad_chart = QuadChartWidget(
    top_left_period="1m",
    top_right_period="5m",
    bottom_left_period="15m",
    bottom_right_period="1h"
)
```

### 更新数据

```python
# 更新历史数据（1分钟K线）
quad_chart.update_history(minute_bars)

# 设置交易时段
quad_chart.set_trading_session_by_symbol("rb2505", "SHFE")
```

### 切换周期

```python
# 切换左上图表为15分钟
quad_chart.set_period("top_left", "15m")

# 切换右下图表为周线
quad_chart.set_period("bottom_right", "w")
```

## 性能优化

### 内存管理
- 基础1分钟数据只存储一份
- 各周期数据按需聚合
- 使用延迟更新避免频繁重绘

### 渲染优化
- 只渲染可见区域的数据
- 使用pyqtgraph的高性能绘图
- 智能缓存减少重复计算

### 同步优化
- 二分查找快速定位最近K线
- 循环检测避免无限递归
- 批量更新减少信号触发

## 应用场景

### 1. 多周期趋势分析
同时观察短、中、长期趋势：
- 短期（5分钟）：把握入场时机
- 中期（15分钟、1小时）：确认趋势方向
- 长期（日线）：判断大趋势

### 2. 关键位置确认
在不同周期确认支撑阻力位：
- 日线级别的关键位置
- 小时级别的震荡区间
- 分钟级别的精确入场点

### 3. 信号过滤
多周期信号共振：
- 日线趋势向上
- 1小时回调结束
- 15分钟突破信号
- 5分钟精确入场

### 4. 风险管理
不同周期设置止损：
- 日线级别：大止损
- 1小时级别：中止损
- 15分钟级别：小止损
- 根据持仓周期选择

## 与双图对比

| 特性 | 双图 | 四图 |
|------|------|------|
| 图表数量 | 2个 | 4个 |
| 布局方式 | 左右分栏 | 2x2网格 |
| 默认周期 | 15m, 1h | 5m, 15m, 1h, d |
| 适用场景 | 快速对比 | 全面分析 |
| 性能消耗 | 较低 | 适中 |

## 最佳实践

### 1. 周期选择建议
- **日内交易**：1m、5m、15m、1h
- **波段交易**：5m、15m、1h、d
- **趋势交易**：15m、1h、4h、d

### 2. 布局调整建议
- 主要关注周期占据更大空间
- 次要周期缩小但保持可见
- 根据交易风格调整

### 3. 性能优化建议
- 数据量大时适当限制历史长度
- 不需要时切换回单图或双图
- 定期清理不用的数据

## 技术细节

### 时间同步算法

```python
def _sync_all_charts(self, source_chart: str, source_range: Tuple[float, float]):
    """同步所有图表到源图表的时间范围"""
    # 1. 获取源图表的时间范围
    source_start_time = source_bars[source_min_idx].datetime
    source_end_time = source_bars[source_max_idx].datetime

    # 2. 对其他图表使用二分查找
    for chart_name, chart in self.charts.items():
        if chart_name == source_chart:
            continue

        start_idx = self._find_nearest_index(bars, source_start_time)
        end_idx = self._find_nearest_index(bars, source_end_time)

        # 3. 更新X轴范围
        viewbox.setXRange(start_idx, end_idx, padding=0)
```

### K线聚合逻辑

```python
def _aggregate_bars(self, minute_bars: List[BarData], target_period: str) -> List[BarData]:
    """聚合K线数据"""
    # 使用EnhancedChartWidget的聚合方法
    # 支持的周期：1m, 5m, 15m, 1h, 4h, d, w
    return self.top_left_chart._aggregate_bars(minute_bars, target_period)
```

## 故障排除

### 问题1：图表不同步
**原因**：数据时间戳不一致
**解决**：确保所有数据使用相同的时间戳格式

### 问题2：性能卡顿
**原因**：数据量过大
**解决**：限制历史数据长度或使用更大周期

### 问题3：交易连线不显示
**原因**：时间匹配失败
**解决**：检查交易时间是否在K线范围内

## 未来计划

- [ ] 支持自定义布局（1x4、4x1等）
- [ ] 支持更多周期（周线、月线）
- [ ] 添加图表链接开关
- [ ] 支持独立缩放模式
- [ ] 添加图表预设模板

## 参考文档

- [双图视图开发文档](./DUAL_CHART_DEVELOPMENT.md)
- [EnhancedChartWidget使用指南](./enhanced_chart_guide.md)
- [图表组件架构说明](./chart_architecture.md)

## 更新日志

### v1.0.0 (2025-01-XX)
- ✅ 实现2x2四图布局
- ✅ 实现时间轴同步
- ✅ 实现周期按钮激活
- ✅ 实现交易连线显示
- ✅ 集成到CandleChartDialog
- ✅ 添加分段控制器风格按钮组

---

**开发完成时间**: 2025-01-10
**开发者**: Claude (ATMQuant团队)
**版本**: 1.0.0
