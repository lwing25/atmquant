# 独立技术指标使用指南

## 概述

本指南介绍ATMQuant项目中新增的独立技术指标模块。每个指标都被重构为独立的文件，支持参数配置，代码风格参考了提供的参考代码，具有更好的可维护性和扩展性。

## 技术指标列表

### 1. 布林带 (BOLL)
- **文件**: `core/charts/boll_item.py`
- **类名**: `BollItem`
- **参数**:
  - `boll_window`: 计算周期 (默认20)
  - `std_dev`: 标准差倍数 (默认2.0)
- **特点**: 支持填充区域，上下轨虚线显示

### 2. 多重简单移动平均线 (Multi SMA)
- **文件**: `core/charts/multi_sma_item.py`
- **类名**: `MultiSmaItem`
- **参数**:
  - `periods`: 周期列表 (默认[5, 10, 20, 60])
- **特点**: 支持多条不同周期的SMA，不同颜色区分

### 3. 多重指数移动平均线 (Multi EMA)
- **文件**: `core/charts/multi_ema_item.py`
- **类名**: `MultiEmaItem`
- **参数**:
  - `periods`: 周期列表 (默认[12, 26, 50])
- **特点**: 支持多条不同周期的EMA，响应更敏感

### 4. RSI相对强弱指标
- **文件**: `core/charts/rsi_item.py`
- **类名**: `RsiItem`
- **参数**:
  - `rsi_window`: RSI周期 (默认14)
  - `rsi_long_threshold`: 超买阈值 (默认70)
  - `rsi_short_threshold`: 超卖阈值 (默认30)
- **特点**: 支持超买超卖区域颜色区分，背离线显示

### 5. MACD指标
- **文件**: `core/charts/macd_item.py`
- **类名**: `Macd3Item`
- **参数**:
  - `short_window`: 快速周期 (默认12)
  - `long_window`: 慢速周期 (默认26)
  - `M`: 信号周期 (默认9)
  - `scale_factor`: 放大因子 (默认100.0)
- **特点**: 现代化配色，支持小数值放大，背离线显示

### 6. DMI方向性运动指标
- **文件**: `core/charts/dmi_item.py`
- **类名**: `DmiItem`
- **参数**:
  - `N`: PDI/MDI周期 (默认14)
  - `M`: ADX/ADXR周期 (默认7)
- **特点**: 四线显示，多空力量对比

## 基础组件

### 动态数组管理器 (DynaArrayManager)
- **文件**: `core/charts/dyna_array_manager.py`
- **类名**: `DynaArrayManager`
- **功能**: 扩展vnpy的ArrayManager，支持临时K线更新
- **方法**:
  - `dmi()`: 计算DMI指标
  - `macd3()`: 计算三线MACD
  - `xma()`: 计算可变周期移动平均

### 配置接口 (ConfigurableIndicator)
- **文件**: `core/charts/indicator_base.py`
- **类名**: `ConfigurableIndicator`
- **功能**: 提供统一的指标配置接口
- **方法**:
  - `get_config_dialog()`: 获取配置对话框
  - `apply_config()`: 应用配置
  - `get_current_config()`: 获取当前配置

## 使用示例

### 基本使用

```python
from vnpy.chart.manager import BarManager
from core.charts import BollItem, MultiSmaItem, RsiItem

# 创建BarManager并加载数据
manager = BarManager()
manager.update_history(bars)  # bars是BarData列表

# 创建布林带指标
boll = BollItem(manager, boll_window=20, std_dev=2.0)

# 创建多重SMA指标
sma = MultiSmaItem(manager, periods=[5, 10, 20, 60])

# 创建RSI指标
rsi = RsiItem(manager, rsi_window=14)
```

### 配置指标参数

```python
# 获取配置对话框
dialog = boll.get_config_dialog(parent_widget)
dialog.exec_()

# 直接应用配置
config = {
    'boll_window': 25,
    'std_dev': 2.5
}
boll.apply_config(config)

# 获取当前配置
current_config = boll.get_current_config()
print(current_config)
```

### 数据更新

```python
# 更新历史数据
boll.update_history(new_bars)

# 更新单个K线
boll.update_bar(new_bar)

# 清除所有数据
boll.clear_all()
```

### 获取指标信息

```python
# 获取指定位置的信息文本
info_text = boll.get_info_text(50)  # 第50根K线的信息

# 获取Y轴范围
min_y, max_y = boll.get_y_range(0, 100)  # 前100根K线的Y轴范围

# 获取边界矩形
rect = boll.boundingRect()
```

## 颜色方案

### 布林带 (BOLL)
- **上轨**: 亮蓝色虚线 (0, 191, 255)
- **下轨**: 亮绿色虚线 (50, 205, 50)
- **填充**: 淡蓝色半透明 (100, 149, 237, 35)

### 多重移动平均线
- **SMA**: 红、绿、蓝、黄依次循环
- **EMA**: 橙、绿黄、蓝、玫红依次循环

### RSI
- **正常区域**: 黄色线 (255, 255, 0)
- **超买区域**: 红色粗线 (255, 50, 50)
- **超卖区域**: 绿色粗线 (50, 255, 50)
- **参考线**: 白色半透明虚线

### MACD
- **DIFF线**: 现代蓝色 (64, 158, 255)
- **DEA线**: 现代橙色 (255, 152, 0)
- **多头柱**: 红色半透明 (239, 68, 68, 180)
- **空头柱**: 绿色半透明 (34, 197, 94, 180)

### DMI
- **PDI**: 白色线 (255, 255, 255)
- **MDI**: 黄色线 (255, 255, 0)
- **ADX**: 紫色线 (255, 0, 255)
- **ADXR**: 绿色线 (0, 255, 0)

## 测试

运行独立指标测试：

```bash
cd /Users/mac/code/atmquant
source vnpy_env/bin/activate
python scripts/test_independent_indicators.py
```

测试包含：
- 指标创建和配置
- 数据计算和绘制
- 信息文本和Y轴范围
- DynaArrayManager功能

## 集成到图表

这些独立指标可以轻松集成到现有的图表系统中：

```python
from core.charts import EnhancedChartWidget

# 如果EnhancedChartWidget可用
try:
    chart = EnhancedChartWidget()
    # 使用增强图表
except ImportError:
    # 或者直接使用独立指标
    from vnpy.chart.widget import ChartWidget
    from core.charts import BollItem
    
    chart = ChartWidget()
    boll = BollItem(chart._manager)
```

## 注意事项

1. **数据要求**: 每个指标都有最小数据量要求，通常为周期参数的2-3倍
2. **性能优化**: 指标使用缓存机制，避免重复计算
3. **配置持久化**: 配置更改会立即生效并触发重绘
4. **兼容性**: 所有指标继承自vnpy的ChartItem，保持API兼容性
5. **错误处理**: 计算错误时返回NaN值，不会中断绘制

## 扩展开发

要创建新的技术指标：

1. 继承`ChartItem`和`ConfigurableIndicator`
2. 实现必要的抽象方法
3. 添加配置相关方法
4. 编写测试用例
5. 更新`__init__.py`导出新指标

示例框架：

```python
class MyIndicatorItem(ChartItem, ConfigurableIndicator):
    def __init__(self, manager: BarManager, **kwargs):
        super().__init__(manager)
        # 初始化参数
    
    def _draw_bar_picture(self, ix: int, bar: BarData) -> QtGui.QPicture:
        # 绘制逻辑
        pass
    
    def get_y_range(self, min_ix=None, max_ix=None):
        # Y轴范围
        pass
    
    def get_info_text(self, ix: int) -> str:
        # 信息文本
        pass
    
    # 配置方法
    def get_config_dialog(self, parent):
        pass
    
    def apply_config(self, config):
        pass
```

这样的设计确保了代码的一致性、可维护性和扩展性。
