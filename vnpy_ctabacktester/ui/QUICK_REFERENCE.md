# 🚀 CTA回测UI快速参考

## 一分钟了解文件结构

```
vnpy_ctabacktester/ui/
├── widget.py ⭐              # 主界面（这里修改最多）
├── enhanced_widget.py 🔧     # 增强组件（统计和优化结果）
├── redesigned_widget.py 🎨  # 现代化界面（可选）
└── README.md 📖             # 完整文档

core/charts/
└── enhanced_chart_widget.py 📊  # 图表组件（独立维护）
```

## ⚡ 常见修改场景

### 场景1：我想添加一个新的技术指标
**文件**：`core/charts/enhanced_chart_widget.py`
```python
# 找到指标注册部分，添加你的指标
```

### 场景2：我想在统计面板显示新的指标
**文件**：`enhanced_widget.py`
```python
# 在 EnhancedStatisticsMonitor.GROUPED_INDICATORS 中添加
GROUPED_INDICATORS = {
    "【你的分组】": [
        ("metric_key", "显示名称"),
    ],
}
```

### 场景3：K线图显示有问题
**检查顺序**：
1. 查看 `core/charts/enhanced_chart_widget.py`（图表逻辑）
2. 查看 `widget.py` 中的 `CandleChartDialog`（集成逻辑）
3. ❌ 不要去找 `enhanced_candle_dialog.py`（已删除）

### 场景4：优化结果需要新的筛选条件
**文件**：`enhanced_widget.py`
```python
# 在 EnhancedOptimizationResultMonitor.init_ui() 中添加
self.filter_combo.addItems([
    "你的筛选条件",
])
```

### 场景5：我想切换回原始界面
**文件**：`widget.py`（最后一行）
```python
# 修改别名
BacktesterManager = OriginalBacktesterManager  # 原始界面
# 或
BacktesterManager = RedesignedBacktesterManager  # 现代化界面
```

## 🎯 记住这3条规则

1. **图表功能** → 修改 `core/charts/enhanced_chart_widget.py`
2. **统计和优化** → 修改 `enhanced_widget.py`
3. **界面布局** → 修改 `widget.py` 或 `redesigned_widget.py`

## ❌ 常见错误

| 错误做法 | 正确做法 |
|---------|---------|
| 在 widget.py 中直接修改图表代码 | 修改 enhanced_chart_widget.py |
| 使用 EnhancedCandleChartDialog | 使用 CandleChartDialog（widget.py） |
| 复制代码到多个文件 | 在正确的文件中修改一次 |

## 📞 需要更多帮助？

- 📖 详细文档：`README.md`
- 🏗️ 架构图：`ARCHITECTURE.md`
- 💬 不确定改哪里？查看文件头部的注释

---

**最后更新**：2025-01-06
**版本**：v1.0

