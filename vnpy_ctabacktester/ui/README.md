# CTA回测UI模块说明

## 📁 文件结构与职责

### 核心文件

#### 1. `widget.py` ⭐ **主回测界面（推荐使用）**
- **职责**：CTA回测的主界面，已集成所有增强功能
- **包含组件**：
  - `OriginalBacktesterManager`：原始回测管理器
  - `BacktesterManager`：当前使用的回测管理器（指向RedesignedBacktesterManager）
  - `CandleChartDialog`：K线图表对话框（已集成`EnhancedChartWidget`）
  - `StatisticsMonitor`：基础统计监控器
  - 其他支持组件（优化设置、结果显示等）

- **增强功能**：
  - ✅ 使用 `EnhancedChartWidget` 显示K线图表
  - ✅ 集成 `EnhancedStatisticsMonitor`（增强版统计监控器）
  - ✅ 集成 `EnhancedOptimizationResultMonitor`（增强版优化结果显示）
  - ✅ 支持多周期切换
  - ✅ 自动回退机制（如果增强组件不可用）

- **修改建议**：
  - ✏️ 需要修改K线图表功能 → 修改 `core/charts/enhanced_chart_widget.py`
  - ✏️ 需要修改统计指标显示 → 修改 `enhanced_widget.py` 中的 `EnhancedStatisticsMonitor`
  - ✏️ 需要修改优化结果显示 → 修改 `enhanced_widget.py` 中的 `EnhancedOptimizationResultMonitor`

---

#### 2. `enhanced_widget.py` 🔧 **增强组件库**
- **职责**：提供增强版UI组件
- **包含组件**：
  - `EnhancedStatisticsMonitor`：增强版统计监控器（分组显示更多指标）
  - `EnhancedOptimizationResultMonitor`：增强版优化结果显示器（带筛选、导出功能）
  - `NumericTableWidgetItem`：支持数值排序的表格项

- **使用方式**：
  - 被 `widget.py` 动态导入使用
  - 独立维护，不依赖其他UI文件

---

#### 3. `redesigned_widget.py` 🎨 **现代化界面（可选）**
- **职责**：提供重新设计的两列布局回测界面
- **特点**：
  - 深色主题
  - 两列布局（1:3比例）
  - 核心指标概览
  - 集成图表显示

- **使用方式**：
  - 通过 `BacktesterManager = RedesignedBacktesterManager` 启用
  - 可以切换回原始界面（修改widget.py中的别名）

---

## 🔗 依赖关系

```
widget.py (主界面)
├── 导入 → core/charts/enhanced_chart_widget.py (增强图表)
├── 导入 → enhanced_widget.py (增强组件)
└── 导入 → redesigned_widget.py (现代化界面)

redesigned_widget.py (现代化界面)
├── 导入 → enhanced_widget.py (增强组件)
└── 导入 → widget.py (部分对话框)

enhanced_widget.py (增强组件)
└── 独立运行，无依赖其他UI文件
```

---

## 🎯 开发指南

### 场景1：修改K线图表功能
**位置**：`core/charts/enhanced_chart_widget.py`
```python
# 修改EnhancedChartWidget类
# widget.py会自动使用修改后的版本
```

### 场景2：添加新的统计指标
**位置**：`enhanced_widget.py` → `EnhancedStatisticsMonitor`
```python
# 在GROUPED_INDICATORS中添加新指标
GROUPED_INDICATORS = {
    "【你的新分组】": [
        ("new_metric", "新指标名称"),
    ],
}
```

### 场景3：修改优化结果筛选条件
**位置**：`enhanced_widget.py` → `EnhancedOptimizationResultMonitor`
```python
# 在filter_combo中添加新的筛选条件
self.filter_combo.addItems([
    "你的新筛选条件",
])
```

### 场景4：切换到原始界面
**位置**：`widget.py`
```python
# 修改最后一行的别名
BacktesterManager = OriginalBacktesterManager  # 使用原始界面
# 或
BacktesterManager = RedesignedBacktesterManager  # 使用现代化界面
```

---

## ⚠️ 注意事项

1. **不要修改错地方**：
   - ❌ 不要在 `widget.py` 中直接修改图表功能
   - ✅ 修改 `core/charts/enhanced_chart_widget.py`

2. **确保使用正确的类**：
   - ✅ 使用 `CandleChartDialog`（来自widget.py）
   - ❌ 不要使用 `EnhancedCandleChartDialog`（已删除）

3. **增强功能的启用**：
   - `EnhancedStatisticsMonitor` 和 `EnhancedOptimizationResultMonitor` 会自动启用
   - 如果导入失败，会自动回退到基础版本

4. **文件隔离原则**：
   - `core/charts/enhanced_chart_widget.py` 独立维护图表功能
   - `enhanced_widget.py` 独立维护增强组件
   - `widget.py` 作为主界面集成所有功能

---

## 🚀 快速参考

| 需求 | 修改文件 | 位置 |
|------|---------|------|
| 添加技术指标 | `core/charts/enhanced_chart_widget.py` | `EnhancedChartWidget` 类 |
| 修改统计指标 | `enhanced_widget.py` | `EnhancedStatisticsMonitor.GROUPED_INDICATORS` |
| 修改优化结果显示 | `enhanced_widget.py` | `EnhancedOptimizationResultMonitor` 类 |
| 修改界面布局 | `widget.py` 或 `redesigned_widget.py` | UI初始化方法 |
| 切换界面风格 | `widget.py` | 修改 `BacktesterManager` 别名 |

---

## 📝 更新日志

### 2025-01-06
- ✅ 在 `widget.py` 中集成 `EnhancedChartWidget`
- ✅ 统一使用 `CandleChartDialog` 作为K线图表对话框
- ✅ 添加清晰的文件头注释和说明文档
- ✅ 确保所有增强功能正确集成

