# ATMQuant 策略开发指南

## 概述

本目录包含ATMQuant项目的自研量化策略。所有策略都基于vnpy框架开发，并集成了日志和告警系统。

## 目录结构

```
core/strategies/
├── __init__.py
├── base_strategy.py          # 基础策略类
├── triple_ma_strategy.py     # 三均线策略
└── README.md                 # 本文件
```

## 基础策略类

### BaseCtaStrategy

所有ATMQuant策略都继承自`BaseCtaStrategy`，它基于vnpy的`CtaTemplate`扩展，添加了以下功能：

- **日志系统集成**：自动记录策略运行日志
- **告警系统集成**：支持飞书、钉钉等告警通知
- **状态管理**：跟踪策略运行状态
- **错误处理**：统一的异常处理机制

### 使用方法

```python
from core.strategies.base_strategy import BaseCtaStrategy

class MyStrategy(BaseCtaStrategy):
    """我的策略"""
    
    def on_init(self):
        """策略初始化"""
        super().on_init()
        # 你的初始化代码
        
    def on_bar(self, bar):
        """K线数据更新"""
        # 你的策略逻辑
        pass
```

## 内置策略

### 三均线策略 (TripleMaStrategy)

一个经典的多时间周期移动平均策略，支持以下特性：

#### 核心参数

- `short_window`: 短期均线周期 (默认: 5)
- `mid_window`: 中期均线周期 (默认: 20)
- `long_window`: 长期均线周期 (默认: 60)
- `ma_type`: 均线类型，支持"SMA"和"EMA" (默认: "SMA")

#### 多时间周期

- `signal_timeframe`: 趋势分析时间周期，用于判断大趋势方向 (默认: 15分钟)
- `trade_timeframe`: 信号执行时间周期，用于执行具体交易 (默认: 5分钟)

#### 风险控制

- `stop_loss_pct`: 止损百分比 (默认: 2.0%)
- `take_profit_pct`: 止盈百分比 (默认: 4.0%)
- `trailing_stop_pct`: 跟踪止损百分比 (默认: 1.0%)

#### 交易信号

- **做多信号**: 短期MA向上穿过中期MA，且交叉点位于长期MA上方
- **做空信号**: 短期MA向下穿过中期MA，且交叉点位于长期MA下方

## 策略开发指南

### 1. 创建新策略

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
我的策略
"""

from .base_strategy import BaseCtaStrategyV6

class MyStrategy(BaseCtaStrategyV6):
    """我的策略"""
    
    # 策略参数
    param1 = 10
    param2 = 20
    
    # 策略变量
    var1 = 0
    var2 = 0
    
    parameters = ["param1", "param2"]
    variables = ["var1", "var2"]
    
    def on_init(self):
        """策略初始化"""
        super().on_init()
        # 初始化代码
        
    def on_bar(self, bar):
        """K线数据更新"""
        # 策略逻辑
        pass
```

### 2. 策略测试

使用提供的测试脚本验证策略：

```bash
# 测试策略加载
python scripts/test_3ma_strategy.py

# 演示策略功能
python scripts/demo_3ma_strategy.py
```

### 3. 策略回测

```bash
# 运行回测
python scripts/backtest_3ma_strategy.py

# 参数优化
python scripts/optimize_3ma_strategy.py
```

### 4. 实盘部署

在vnpy界面中：
1. 启动vnpy主程序
2. 进入CTA策略模块
3. 添加策略，选择"TripleMaStrategy"
4. 配置参数和交易品种
5. 初始化并启动策略

## 最佳实践

### 1. 代码规范

- 遵循PEP 8代码规范
- 使用类型注解
- 添加详细的中文注释
- 保持函数和类的单一职责

### 2. 参数设计

- 参数名应清晰表达其用途
- 提供合理的默认值
- 支持参数优化
- 避免参数过多导致过拟合

### 3. 风险控制

- 实现止损机制
- 控制仓位大小
- 避免过度交易
- 监控策略表现

### 4. 日志和监控

- 记录关键操作
- 监控策略状态
- 设置告警阈值
- 定期检查日志

## 故障排除

### 常见问题

1. **策略加载失败**
   - 检查策略文件语法
   - 确认继承关系正确
   - 查看错误日志

2. **参数设置错误**
   - 检查参数类型
   - 确认参数范围
   - 验证默认值

3. **交易信号异常**
   - 检查数据质量
   - 验证指标计算
   - 调试信号逻辑

4. **性能问题**
   - 优化计算逻辑
   - 减少不必要的计算
   - 使用缓存机制

### 调试技巧

1. **使用日志系统**
   ```python
   self.logger.info("调试信息")
   self.logger.error("错误信息")
   ```

2. **设置断点**
   ```python
   import pdb; pdb.set_trace()
   ```

3. **打印变量值**
   ```python
   print(f"变量值: {variable}")
   ```

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 编写策略代码
4. 添加测试用例
5. 提交Pull Request

## 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 联系方式

如有问题或建议，请通过以下方式联系：

- 项目Issues: [GitHub Issues](https://github.com/your-repo/issues)
- 邮箱: your-email@example.com
- 微信群: 扫码加入

---

*本文档会持续更新，请关注最新版本。*
