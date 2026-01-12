# 指标自动加载机制说明

## 概述

`EnhancedChartWidget` 现在支持自动检测并加载 `core/indicators/` 目录下的所有可用指标。这个机制对所有用户都友好：

- **基础版用户**：只加载基础指标，不会因为缺少扩展指标文件而报错
- **会员用户**：将扩展指标文件复制到 `core/indicators/` 后，图表会自动识别并加载

## 工作原理

### 1. 基础指标（必需）

这些指标是所有用户都有的，直接静态导入：

```python
# core/charts/enhanced_chart_widget.py (30-37行)
from core.indicators.boll_item import BollItem
from core.indicators.multi_sma_item import MultiSmaItem
from core.indicators.multi_ema_item import MultiEmaItem
from core.indicators.rsi_item import RsiItem
from core.indicators.macd_item import Macd3Item
from core.indicators.dmi_item import DmiItem
```

在 `__init__` 方法中配置：
- **主图指标**：BOLL、SMA、EMA
- **副图指标**：Volume、MACD、RSI、DMI

### 2. 扩展指标（可选）

扩展指标通过配置字典定义，然后动态加载：

```python
# core/charts/enhanced_chart_widget.py (52-105行)
EXTENDED_INDICATORS_CONFIG = {
    # 主图指标
    "fibonacci": {
        "module": "fibonacci_entry_bands_item",  # 文件名（不含.py）
        "class": "FibonacciEntryBandsItem",      # 类名
        "type": "main",                           # 主图指标
        "default_visible": False,                 # 默认不显示
        "configurable": True,                     # 支持参数配置
    },
    # 副图指标
    "adaptive_macd": {
        "module": "adaptive_macd_deluxe_item",
        "class": "AdaptiveMacdDeluxeItem",
        "type": "sub",                            # 副图指标
        "default_visible": False,
        "min_height": 120,                        # 最小高度
        "max_height": 180,                        # 最大高度
        "configurable": True,
    },
    # ... 其他扩展指标
}
```

### 3. 自动加载逻辑

在模块加载时（107-119行），自动尝试导入每个扩展指标：

```python
EXTENDED_INDICATORS_CLASSES = {}
for indicator_name, config in EXTENDED_INDICATORS_CONFIG.items():
    try:
        module = __import__(
            f"core.indicators.{config['module']}",
            fromlist=[config['class']]
        )
        indicator_class = getattr(module, config['class'])
        EXTENDED_INDICATORS_CLASSES[indicator_name] = indicator_class
    except (ImportError, AttributeError):
        # 文件不存在或类名不匹配，跳过（不报错）
        pass
```

### 4. 注册到图表

在 `EnhancedChartWidget.__init__` 方法中（354-375行），自动注册已加载的扩展指标：

```python
for indicator_name, indicator_class in EXTENDED_INDICATORS_CLASSES.items():
    config = EXTENDED_INDICATORS_CONFIG[indicator_name]

    if config["type"] == "main":
        # 注册到主图指标
        self.main_indicators[indicator_name] = [
            indicator_class, indicator_name,
            config["default_visible"], config["configurable"]
        ]
    elif config["type"] == "sub":
        # 注册到副图指标
        self.sub_indicators[indicator_name] = [
            indicator_class, indicator_name,
            config["default_visible"],
            config["min_height"], config["max_height"],
            config["configurable"]
        ]
```

## 已配置的扩展指标

### 主图指标（4个）

| 显示名称 | 模块文件 | 类名 | 默认显示 |
|---------|---------|------|---------|
| fibonacci | fibonacci_entry_bands_item.py | FibonacciEntryBandsItem | 否 |
| smart_money | smart_money_channels.py | SmartMoneyChannelsItem | 否 |
| zlema | zlema_item.py | ZlemaItem | 否 |
| supertrend | supertrend_item.py | SupertrendItem | 否 |

### 副图指标（4个）

| 显示名称 | 模块文件 | 类名 | 默认显示 | 高度 |
|---------|---------|------|---------|------|
| adaptive_macd | adaptive_macd_deluxe_item.py | AdaptiveMacdDeluxeItem | 否 | 120-180 |
| squeeze | squeeze_momentum_item.py | SqueezeMomentumItem | 否 | 100-150 |
| supertrended_rsi | supertrended_rsi_item.py | SupertrendedRsiItem | 否 | 100-150 |
| wavetrend | wavetrend_item.py | WaveTrendItem | 否 | 100-150 |

**注意**：`enhanced_volume` 指标是单独处理的（39-46行），因为它要替换默认的 Volume 指标。

## 如何添加新的扩展指标

### 步骤1: 创建指标文件

在 `core/indicators/` 目录下创建新指标文件，例如 `new_indicator_item.py`：

```python
from vnpy.chart.item import ChartItem
from core.indicators.indicator_base import ConfigurableIndicator

class NewIndicatorItem(ChartItem, ConfigurableIndicator):
    def __init__(self, manager, **kwargs):
        super().__init__(manager)
        # ... 指标实现
```

### 步骤2: 添加到配置字典

在 `core/charts/enhanced_chart_widget.py` 的 `EXTENDED_INDICATORS_CONFIG` 字典中添加配置：

```python
EXTENDED_INDICATORS_CONFIG = {
    # ... 现有配置

    "new_indicator": {
        "module": "new_indicator_item",      # 文件名（不含.py）
        "class": "NewIndicatorItem",         # 类名
        "type": "sub",                       # "main" 或 "sub"
        "default_visible": False,            # 默认是否显示
        "min_height": 100,                   # 副图指标需要
        "max_height": 150,                   # 副图指标需要
        "configurable": True,                # 是否可配置参数
    },
}
```

### 步骤3: 无需其他操作

- ✓ 自动导入
- ✓ 自动注册到图表
- ✓ 自动出现在控制面板
- ✓ 自动支持显示/隐藏
- ✓ 自动支持参数配置（如果 `configurable=True`）

## 用户使用流程

### 免费用户

1. 下载开源代码
2. 运行 `python main.py`
3. 只看到基础指标（BOLL、SMA、EMA、MACD、RSI、DMI、Volume）
4. 不会有任何错误

### 会员用户

1. 从知识星球下载扩展指标文件（例如 `fibonacci_entry_bands_item.py`）
2. 将文件复制到 `core/indicators/` 目录
3. 运行 `python main.py`
4. 在图表控制面板中看到新增的扩展指标选项
5. 勾选复选框即可显示指标

## 优势

1. **零配置**：会员用户只需复制文件，无需修改任何代码
2. **向后兼容**：免费用户不受影响，不会报错
3. **统一管理**：所有指标配置集中在一个字典中
4. **易于扩展**：添加新指标只需修改配置字典
5. **类型安全**：配置信息明确，不会出现格式错误
6. **可维护性**：配置与实现分离，便于维护

## 注意事项

1. **命名规范**：
   - 配置字典的 key 应该简短且有意义
   - 模块名（文件名）使用 snake_case
   - 类名使用 PascalCase

2. **类型一致性**：
   - 主图指标配置：`[类, key, 默认可见, 可配置]`
   - 副图指标配置：`[类, key, 默认可见, 最小高度, 最大高度, 可配置]`

3. **默认可见性**：
   - 建议扩展指标默认设置为 `False`（不显示）
   - 用户手动勾选后才显示，避免界面过于拥挤

4. **高度设置**：
   - 副图指标需要设置 `min_height` 和 `max_height`
   - 通常范围：100-150（简单指标）或 120-180（复杂指标）

## 调试技巧

如果指标没有正常加载，检查以下几点：

1. **文件名是否正确**：
   ```python
   "module": "fibonacci_entry_bands_item"  # 对应文件 fibonacci_entry_bands_item.py
   ```

2. **类名是否匹配**：
   ```python
   "class": "FibonacciEntryBandsItem"  # 必须与文件中的类名完全一致
   ```

3. **查看加载结果**：
   ```python
   from core.charts.enhanced_chart_widget import EXTENDED_INDICATORS_CLASSES
   print(EXTENDED_INDICATORS_CLASSES)  # 查看哪些指标成功加载
   ```

4. **捕获导入错误**（仅用于调试）：
   修改动态导入部分，临时打印错误信息：
   ```python
   except (ImportError, AttributeError) as e:
       print(f"Failed to load {indicator_name}: {e}")
       pass
   ```
