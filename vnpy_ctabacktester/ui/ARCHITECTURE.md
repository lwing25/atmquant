# CTA回测UI模块架构图

## 🏗️ 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     CTA回测系统UI层                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐    │
│  │           widget.py (主界面 - 推荐使用)                 │    │
│  │  ┌──────────────────────────────────────────────┐      │    │
│  │  │    OriginalBacktesterManager                │      │    │
│  │  │    (原始回测界面)                            │      │    │
│  │  └──────────────────────────────────────────────┘      │    │
│  │                                                         │    │
│  │  ┌──────────────────────────────────────────────┐      │    │
│  │  │    CandleChartDialog ⭐                      │      │    │
│  │  │    (K线图表对话框)                           │      │    │
│  │  │    ├─ 使用 EnhancedChartWidget               │      │    │
│  │  │    ├─ 支持多周期切换                         │      │    │
│  │  │    └─ 自动回退机制                           │      │    │
│  │  └──────────────────────────────────────────────┘      │    │
│  │                                                         │    │
│  │  ┌──────────────────────────────────────────────┐      │    │
│  │  │    BacktesterManager                        │      │    │
│  │  │    (当前使用的管理器)                        │      │    │
│  │  │    └─ 指向 → RedesignedBacktesterManager     │      │    │
│  │  └──────────────────────────────────────────────┘      │    │
│  └────────────────────────────────────────────────────────┘    │
│                        ↓ 导入                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │           enhanced_widget.py (增强组件库)               │    │
│  │  ┌──────────────────────────────────────────────┐      │    │
│  │  │    EnhancedStatisticsMonitor                │      │    │
│  │  │    (增强版统计监控器)                        │      │    │
│  │  │    └─ 分组显示更多指标                       │      │    │
│  │  └──────────────────────────────────────────────┘      │    │
│  │  ┌──────────────────────────────────────────────┐      │    │
│  │  │    EnhancedOptimizationResultMonitor        │      │    │
│  │  │    (增强版优化结果显示)                      │      │    │
│  │  │    ├─ 高级筛选功能                           │      │    │
│  │  │    ├─ 导出CSV和详细报告                      │      │    │
│  │  │    └─ 支持排序                               │      │    │
│  │  └──────────────────────────────────────────────┘      │    │
│  └────────────────────────────────────────────────────────┘    │
│                        ↓ 导入                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │        redesigned_widget.py (现代化界面 - 可选)         │    │
│  │  ┌──────────────────────────────────────────────┐      │    │
│  │  │    RedesignedBacktesterManager              │      │    │
│  │  │    (两列布局界面)                            │      │    │
│  │  │    ├─ 深色主题                               │      │    │
│  │  │    ├─ 核心指标概览                           │      │    │
│  │  │    ├─ 集成图表显示                           │      │    │
│  │  │    └─ 使用增强组件                           │      │    │
│  │  └──────────────────────────────────────────────┘      │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                            ↓ 使用
┌─────────────────────────────────────────────────────────────────┐
│                  core/charts/enhanced_chart_widget.py            │
│  ┌────────────────────────────────────────────────────────┐    │
│  │    EnhancedChartWidget                                 │    │
│  │    (增强版图表组件 - 独立维护)                         │    │
│  │    ├─ 多种技术指标 (MA, BOLL, RSI, MACD等)             │    │
│  │    ├─ 多周期切换                                       │    │
│  │    ├─ 交易时段管理                                     │    │
│  │    └─ 独立指标渲染                                     │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## 🔄 数据流向

```
用户操作
   │
   ├─ 开始回测 → BacktesterManager.start_backtesting()
   │                │
   │                ├─ 调用回测引擎
   │                └─ 更新统计监控器 (EnhancedStatisticsMonitor)
   │
   ├─ 查看K线图 → CandleChartDialog.show()
   │                │
   │                ├─ 创建 EnhancedChartWidget
   │                ├─ 加载历史数据
   │                ├─ 设置交易时段
   │                └─ 绘制交易信号
   │
   └─ 参数优化 → BacktesterManager.start_optimization()
                    │
                    ├─ 调用优化引擎
                    └─ 显示结果 (EnhancedOptimizationResultMonitor)
```

## 📊 类关系图

```
widget.py:
├── OriginalBacktesterManager
│   ├── has-a: StatisticsMonitor / EnhancedStatisticsMonitor
│   ├── has-a: CandleChartDialog
│   ├── has-a: BacktestingResultDialog (多个)
│   └── uses: EnhancedOptimizationResultMonitor
│
├── CandleChartDialog ⭐
│   ├── has-a: EnhancedChartWidget (优先)
│   ├── fallback: ChartWidget (标准)
│   └── uses: generate_trade_pairs()
│
├── BacktesterManager (别名)
│   └── points-to: RedesignedBacktesterManager
│
└── 其他支持类:
    ├── StatisticsMonitor
    ├── BacktestingSettingEditor
    ├── OptimizationSettingEditor
    ├── OptimizationResultMonitor
    └── BacktestingResultDialog

enhanced_widget.py:
├── EnhancedStatisticsMonitor
│   └── extends: QtWidgets.QTableWidget
│
├── EnhancedOptimizationResultMonitor
│   └── extends: QtWidgets.QDialog
│
└── NumericTableWidgetItem
    └── extends: QtWidgets.QTableWidgetItem

redesigned_widget.py:
├── RedesignedBacktesterManager
│   ├── uses: EnhancedStatisticsMonitor
│   ├── uses: EnhancedOptimizationResultMonitor
│   └── has-a: CoreMetricsWidget, MetricsGridWidget, ChartWidget
│
├── CoreMetricsWidget
│   └── extends: QtWidgets.QWidget
│
├── MetricsGridWidget
│   └── extends: QtWidgets.QWidget
│
└── ChartWidget
    └── extends: QtWidgets.QWidget
```

## 🎯 模块职责划分

### 1️⃣ UI层（vnpy_ctabacktester/ui/）
- **widget.py**：主界面集成
- **enhanced_widget.py**：增强UI组件
- **redesigned_widget.py**：现代化界面

### 2️⃣ 图表层（core/charts/）
- **enhanced_chart_widget.py**：图表功能实现

### 3️⃣ 引擎层（vnpy_ctabacktester/engine.py）
- 回测引擎
- 优化引擎
- 数据管理

## 🔧 修改指南快速索引

| 修改内容 | 文件位置 | 影响范围 |
|---------|---------|---------|
| K线图表外观 | `core/charts/enhanced_chart_widget.py` | CandleChartDialog |
| 添加技术指标 | `core/charts/enhanced_chart_widget.py` | CandleChartDialog |
| 统计指标分组 | `enhanced_widget.py` → GROUPED_INDICATORS | EnhancedStatisticsMonitor |
| 优化结果筛选 | `enhanced_widget.py` → filter_combo | EnhancedOptimizationResultMonitor |
| 界面布局 | `widget.py` 或 `redesigned_widget.py` | 整体UI |
| 切换界面风格 | `widget.py` → BacktesterManager别名 | 启动时的界面 |

## ⚠️ 重要提醒

1. **图表功能修改**
   - ✅ 修改 `core/charts/enhanced_chart_widget.py`
   - ❌ 不要修改 `widget.py` 中的 `CandleChartDialog`

2. **避免文件混淆**
   - ✅ 使用 `CandleChartDialog`（widget.py）
   - ❌ 已删除 `EnhancedCandleChartDialog`（enhanced_candle_dialog.py）

3. **增强功能可选性**
   - 所有增强功能都有回退机制
   - 如果导入失败，自动使用基础版本

4. **文件隔离原则**
   - 图表功能：`core/charts/enhanced_chart_widget.py`
   - UI组件：`enhanced_widget.py`
   - 主界面：`widget.py` 或 `redesigned_widget.py`

## 📝 版本历史

### v1.0 (2025-01-06) - 架构重组
- 删除重复文件 `enhanced_candle_dialog.py`
- 统一使用 `widget.py` 中的 `CandleChartDialog`
- 明确文件职责和依赖关系
- 添加完整的文档说明

