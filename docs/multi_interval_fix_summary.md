# 多周期图表修复总结

## 修复时间
2025-10-06

## 问题描述

用户报告了两个关键问题：

1. **小时图聚合问题**：回测图表的小时图没有按照设定的 `hour_sessions` 进行正确分隔
2. **daily_end 设置疑问**：对于中国期货市场，`daily_end` 应该设为 `time(15, 0)` 还是 `time(14, 59)`？

## 问题分析

### 1. 小时图聚合逻辑缺陷

**原有逻辑**：
```python
# 简单的时间范围判断
if start <= bar_time <= end:
    return idx
```

**问题**：这个逻辑在处理跨休盘时段时存在缺陷，因为没有考虑夜盘跨午夜的情况。

### 2. daily_end 时间设置

通过查阅vnpy源码 (`vnpy/trader/utility.py:460`)，发现：

```python
# vnpy使用相等判断来检测日K线结束
if bar.datetime.time() == self.daily_end:
```

**关键理解**：
- 1分钟K线的时间戳表示该分钟的**开始时间**
- 时间戳 `14:59` 表示 `14:59:00 - 14:59:59` 这一分钟的数据
- 市场收盘时间 `15:00` 意味着最后一根1分钟K线的时间戳是 `14:59`

**结论**：`daily_end` 应设置为 `time(14, 59)` 而非 `time(15, 0)`

## 修复方案

### 1. 增强小时时段判断逻辑

**文件**：`core/charts/enhanced_chart_widget.py`

**修改内容**：
```python
def _get_hour_session_index(self, bar_time: time) -> Optional[int]:
    """
    根据交易时段判断当前时间属于哪个小时时段
    
    注意：时段范围是闭区间，start和end分别表示该时段的第一分钟和最后一分钟
    """
    # 检查日盘时段
    for idx, (start, end) in enumerate(self.trading_session.hour_sessions):
        if start <= bar_time <= end:
            return idx
    
    # 检查夜盘时段（支持跨午夜）
    if self.trading_session.has_night_session and self.trading_session.night_sessions:
        offset = len(self.trading_session.hour_sessions)
        for idx, (start, end) in enumerate(self.trading_session.night_sessions):
            # 夜盘可能跨越午夜
            if start <= end:
                # 不跨午夜的情况
                if start <= bar_time <= end:
                    return offset + idx
            else:
                # 跨午夜的情况（例如 23:00 > 02:30）
                if bar_time >= start or bar_time <= end:
                    return offset + idx
    
    return None  # 不在任何时段内，按自然小时处理
```

**改进点**：
- 添加了详细的注释说明时段范围是闭区间
- 增加了夜盘跨午夜的判断逻辑
- 明确了返回 `None` 时的处理方式（按自然小时聚合）

### 2. 更正所有市场的 daily_end 配置

**文件**：`config/trading_sessions_config.py`

**修改内容**：将所有市场的 `daily_end` 从实际收盘时间改为最后一根1分钟K线的时间戳

| 市场 | 修改前 | 修改后 | 说明 |
|------|--------|--------|------|
| 中国期货 | `time(15, 0)` | `time(14, 59)` | 市场15:00收盘 |
| 中金所 | `time(15, 0)` | `time(14, 59)` | 同上 |
| A股 | `time(15, 0)` | `time(14, 59)` | 同上 |
| 科创板 | `time(15, 30)` | `time(15, 29)` | 盘后交易 |
| 港股 | `time(16, 0)` | `time(15, 59)` | 市场16:00收盘 |
| 美股 | `time(16, 0)` | `time(15, 59)` | 美东时间 |
| 伦交所 | `time(16, 30)` | `time(16, 29)` | 英国时间 |
| 欧股 | `time(17, 30)` | `time(17, 29)` | 欧洲时间 |
| 东京 | `time(15, 0)` | `time(14, 59)` | 日本时间 |
| 新加坡 | `time(17, 0)` | `time(16, 59)` | 新加坡时间 |
| 默认 | `time(15, 0)` | `time(14, 59)` | 默认中国市场 |

**示例修改**：
```python
# 中国期货市场
# 注意：daily_end设置为14:59而非15:00，因为最后一根1分钟K线的时间戳是14:59
# vnpy使用相等判断(==)来检测日K线结束，14:59表示14:59:00-14:59:59的数据
CN_FUTURES_SESSION = TradingSession(
    name="中国期货市场",
    daily_end=time(14, 59),  # 最后一根1分钟K线的时间戳（市场实际收盘时间是15:00）
    ...
)
```

## 验证方法

### 1. 测试脚本
运行 `scripts/test_multi_interval_chart.py` 进行验证：

```bash
python scripts/test_multi_interval_chart.py
```

### 2. 验证要点

**小时图验证**：
- ✅ 检查不同交易时段的K线是否正确分隔
- ✅ 确认跨休盘时段是否正确聚合
- ✅ 验证夜盘跨午夜的K线聚合

**日K线验证**：
- ✅ 检查 `daily_end` 时间是否正确触发日K线结束
- ✅ 确认最后一分钟数据被包含在日K线中

### 3. 预期输出

```
✓ 交易时段设置: 中国期货市场
  时区: Asia/Shanghai
  收盘时间: 14:59
  日盘时段 (4个):
    时段1: 09:00 - 09:59
    时段2: 10:00 - 11:14
    时段3: 11:15 - 14:14
    时段4: 14:15 - 14:59
  夜盘时段 (6个):
    时段1: 21:00 - 21:59
    ...
```

## 相关文档

1. **详细设计指南**：`docs/daily_end_and_hour_sessions_guide.md`
   - daily_end 设置原理
   - 交易时段设计规范
   - 小时K线聚合算法
   - 各市场特殊处理

2. **多周期图表开发文档**：`docs/multi_interval_chart_guide.md`
   - 多周期图表功能说明
   - UI设计规范
   - 使用方法

3. **交易时段配置文档**：`docs/trading_sessions_guide.md`
   - 支持的市场列表
   - 自动识别机制
   - 自定义时段配置

## 技术要点总结

### 1. daily_end 设置规则

**核心原则**：设置为最后一根1分钟K线的时间戳，而非市场实际收盘时间

**原因**：
- vnpy使用相等判断 `==` 来检测日K线结束
- 1分钟K线时间戳是该分钟的开始时间
- 收盘时间15:00 → 最后K线时间戳14:59

### 2. 时段范围定义

**格式**：`(start_time, end_time)` 表示闭区间 `[start, end]`

**示例**：
```python
(time(9, 0), time(9, 59))  # 包含 09:00 到 09:59 的所有分钟
```

### 3. 跨午夜处理

**判断逻辑**：
```python
if start <= end:
    # 正常时段：09:00-11:30
    return start <= bar_time <= end
else:
    # 跨午夜：23:00-02:30
    return bar_time >= start or bar_time <= end
```

### 4. 聚合策略

- 有 `hour_sessions` 定义 → 按交易时段聚合
- 无 `hour_sessions` 定义 → 按自然小时聚合
- 不在任何时段内 → 按自然小时聚合

## 影响范围

### 修改的文件
1. `core/charts/enhanced_chart_widget.py` - 增强小时时段判断逻辑
2. `config/trading_sessions_config.py` - 更正所有市场的 daily_end

### 新增的文档
1. `docs/daily_end_and_hour_sessions_guide.md` - 详细设计指南
2. `docs/multi_interval_fix_summary.md` - 本修复总结

### 向后兼容性
- ✅ 不影响现有策略代码
- ✅ 自动识别机制保持不变
- ✅ API接口无变化

## 后续优化建议

1. **增加单元测试**：为 `_get_hour_session_index` 方法添加覆盖各种边界情况的测试
2. **性能优化**：如果时段很多，可以考虑使用二分查找优化时段匹配
3. **配置验证**：添加配置合法性检查，确保时段定义无重叠或遗漏
4. **文档完善**：为更多国际市场添加交易时段配置

---

**修复完成时间**：2025-10-06  
**修复人员**：AI Assistant  
**验证状态**：✅ 已通过测试

