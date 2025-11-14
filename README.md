# ATMQuant - AI量化交易系统

基于vnpy 4.1框架的AI量化交易系统，专注于AI量化投资、指标信号可视化与策略研发。

## 项目特点

- 📊 **定制化图表**: 基于vnpy的专业量化图表系统
- 🏗️ **模块化架构**: 清晰的业务模块划分，易于扩展和维护
- 📈 **策略开发**: 丰富的交易策略，可定制化策略开发与参数优化
- 📚 **教学导向**: 完整的文档和示例，适合学习和教学
- 🎯 **实战导向**: 面向实盘交易的完整解决方案
- ⚙️ **配置管理**: 轻量级配置系统，支持环境隔离

## 快速开始

### 1. 环境准备

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置设置

```bash
# 复制配置文件
cp .env.example .env

# 编辑配置文件，填入你的CTP账户信息
vim .env

# 启动程序（自动加载配置）
python main.py
```

## 项目结构

```
atmquant/                          # 项目根目录
├── 📁 core/                        # 核心业务模块
│   ├── 📁 charts/                  # 图表相关(定制化图表)
│   ├── 📁 data/                    # 数据处理核心
│   ├── 📁 logging/                 # 日志和告警系统
│   │   ├── logger_manager.py      # 日志管理器
│   │   └── alert_manager.py       # 告警管理器
│   └── 📁 strategies/              # 策略相关
├── 📁 config/                      # 统一配置管理
│   ├── settings.py                 # 轻量级配置管理
│   └── alert_config.py             # 告警配置
├── 📁 scripts/                     # 运行脚本
├── 📁 backtests/                   # 回测相关
├── 📁 utils/                       # 工具模块
├── 📁 tests/                       # 测试文件
│   ├── unit/                       # 单元测试
│   ├── integration/                # 集成测试
│   └── backtest/                   # 回测测试
├── 📁 docs/                        # 文档目录
│   ├── README.md                   # 文档中心
│   ├── logging-system.md          # 日志系统文档
│   └── alert-bot-setup.md         # 告警机器人配置
├── 📁 examples/                    # 使用示例
├── 📁 articles/                    # 公众号文章
├── 📁 logs/                        # 日志文件
├── 📁 vnpy/                        # VeighNa框架
├── 📄 main.py                      # 主入口文件
├── 📄 requirements.txt             # 依赖包
└── 📄 README.md                    # 项目说明
```

## 📚 系列文章

### 以AI量化为生系列（交易系统开发）

从零开始搭建完整的量化交易系统，涵盖环境配置、数据管理、策略开发、回测优化、图表可视化等全流程。

1. **[以AI量化为生：普通人如何从无到有稳步构建交易系统](https://mp.weixin.qq.com/s/vHL2ZNoqe65dGn9qEQzLgQ)**
   - 量化交易入门指南
   - 系统架构设计思路
   - 学习路径规划

2. **[以AI量化为生：2.手把手搭建专业量化开发环境](https://mp.weixin.qq.com/s/AFFntmIN6rAFmlk03aIzoA)**
   - Python环境配置
   - vnpy框架安装
   - 开发工具设置

3. **[以AI量化为生：3.vnpy插件安装与配置指南](https://mp.weixin.qq.com/s/0LQ0CLgvKuTMccVPP99WfQ)**
   - vnpy插件生态介绍
   - 核心插件安装配置
   - 常见问题解决

4. **[以AI量化为生：4.vnpy配置管理与系统集成](https://mp.weixin.qq.com/s/XjDe1nD1tDXyJwQweeGCSA)**
   - 轻量级配置管理方案
   - 数据库配置
   - 数据源接入
   - 邮件通知设置

5. **[以AI量化为生：5.期货数据定时下载与合约管理](https://mp.weixin.qq.com/s/r6ravF0YqtbvLcnXToX1Ug)**
   - 期货合约类型详解
   - 智能合约管理系统
   - 定时数据下载实现
   - 数据质量监控

6. **[以AI量化为生：6.日志系统与告警机制设计](https://mp.weixin.qq.com/s/90iZrNuY6qSZ5ZIP4q0nyQ)**
   - 基于loguru的高性能异步日志系统
   - 飞书、钉钉告警机器人配置

7. **[以AI量化为生：7.编写自己的第一个量化策略](https://mp.weixin.qq.com/s/lhTv5r7W5pM5O3osZq0vGA)**
   - vnpy策略开发基础教学
   - 经典策略分析与学习
   - 3MA多时间周期策略实现
   - 动态止盈止损机制设计

8. **[以AI量化为生：8.回测框架优化与重要指标增强](https://mp.weixin.qq.com/s/8Lin92Dm_yG1ZtAHfCb3uA)**
   - vnpy回测框架深度解析
   - 增强型回测指标实现
   - 交易对分析与统计算法
   - 智能评级系统设计

9. **[以AI量化为生：9.回测框架再优化与参数导出功能实现](https://mp.weixin.qq.com/s/iMEmoRekqAf-I3MS9mr0dQ)**
   - 参数回测结果导出功能
   - 滚动夏普比率图表实现

10. **[以AI量化为生：10.回测界面大改版与用户体验全面提升](https://mp.weixin.qq.com/s/9EbD1Qh-ux1mU1gYOt2vOA)**
    - 界面布局重新设计
    - 核心指标卡片式展示
    - 完整指标分组与图表集成
    - 成交记录、委托记录、每日盈亏等优化展示

11. **[以AI量化为生：11.增强版K线图表系统开发实战](https://mp.weixin.qq.com/s/dC1jXfPDsDXumvyOSQQcOw)**
    - 增强版K线图表系统架构设计
    - 主图技术指标实现（布林带、SMA、EMA）
    - 附图技术指标实现（MACD、RSI、DMI、成交量）
    - 交互控制功能（复选框控制、参数配置、拖拽扩展）
    - 与回测系统无缝集成

12. **[以AI量化为生：12.多周期图表开发实战](https://mp.weixin.qq.com/s/FQ85NgQC0h3KLLK3qD00Ew)**
    - 多时间框架分析需求分析
    - 周期切换面板设计与实现
    - K线数据聚合算法开发
    - 技术指标自动更新机制

13. **[以AI量化为生：13.交易时段小时K线合成实战](https://mp.weixin.qq.com/s/3UvbbWDhvZJactgAPtqH7w)**
    - 交易时段K线合成问题分析
    - 小时K线按实际交易时段合成
    - BarGenerator核心修改实现
    - 全球12个金融市场配置

14. **[以AI量化为生：14.多周期交易买卖点连线智能匹配实战](https://mp.weixin.qq.com/s/B35sV1A8klZ3UIO_E9VtYg)**
    - 多周期自适应显示与回调机制
    - 智能时间匹配（三层级匹配策略）

15. **[以AI量化为生：15.双图与四图视图开发实战](https://mp.weixin.qq.com/s/KXNfCfWwu6RExcHzQZHw_w)**
    - 双图并排对比分析（15分钟 vs 1小时）
    - 四图2x2网格全景视图（5分钟、15分钟、1小时、日线）
    - 多图表时间轴智能同步
    - 分段控制器风格视图切换

---

### 量化指标解码系列（技术指标研究）

《量化指标解码》是《以AI量化为生》的姊妹篇，专注于技术指标的深度研究与智能化改造。从经典指标到前沿指标，从原理剖析到实战应用，打造最全面、最前沿的量化指标库。

1. **[量化指标解码01：让指标开口说话！K线图表给技术指标装上AI大脑](https://mp.weixin.qq.com/s/nvF7VT25RXgHzSnVRfBEcQ)**
   - 智能解读的四层架构设计（基础信息、市场状态、信号识别、操作指导）
   - RSI指标智能解读完整实现
   - 区间分析、动量变化、关键位突破、钝化检测、背离信号
   - 为后续指标深度解码奠定基础

2. **[量化指标解码02：RSI深度解码 - 从超买超卖到背离钝化的全面分析](https://mp.weixin.qq.com/s/n1i676s4ZSvJCDdLX7C2sQ)**
   - RSI的计算原理和公式详解
   - 代码实现：TA-Lib计算与ATMQuant集成
   - 经典用法：超买超卖、背离（顶背离/底背离）、钝化
   - 三个实战策略：超买超卖策略、RSI+均线组合、背离策略

3. **[量化指标解码03：布林带的开口收口策略与市场波动性分析](https://mp.weixin.qq.com/s/VGOcKwW4FRSHf3gYMa7fFw)**
   - 布林带的原理：从标准差到波动率通道
   - 经典形态：收口(Squeeze)、开口(Expansion)、上下轨突破、中轨突破
   - 智能解读：价格位置、宽度变化、宽度比率、突破分析
   - 三个实战策略：均值回归策略(震荡市)、趋势突破策略(趋势市)、自适应策略(全市场)

4. **[量化指标解码04：MACD深度解码 - 零轴、背离与多周期共振策略](https://mp.weixin.qq.com/s/kzw_VUbjVWwj3RRxS1NeBQ)**
   - MACD的原理：从EMA到趋势动能
   - 经典用法：金叉死叉、零轴突破、MACD柱变化、DIFF与DEA距离
   - 高级用法：MACD背离（顶背离/底背离）、多周期共振
   - 智能解读：零轴位置、金叉死叉、MACD柱、背离检测

5. **[量化指标解码05：DMI深度解码 - 趋势强度判断的终极武器](https://mp.weixin.qq.com/s/placeholder-dmi)**
   - DMI的原理：从方向到强度
   - PDI和MDI：方向判断（对比、交叉、绝对位置）
   - ADX：趋势强度的核心（阈值判断、变化趋势、ADX与ADXR对比、拐点）
   - 经典组合：多头组合、空头组合、震荡组合

6. **[量化指标解码06：均线｜最简单的指标，最赚钱的策略](https://mp.weixin.qq.com/s/LoiclOU3V_JDTR55WzKYFQ)**
   - SMA与EMA的本质区别（稳定vs敏感）
   - SMA实战：支撑阻力、排列、散度、黄金/死亡交叉
   - EMA实战：动态支撑阻力、早期交叉信号、收敛预警、趋势强度
   - 多均线系统：三均线系统、葛兰碧法则、均线粘合与突破

7. **[量化指标解码07：会看成交量，你就成功了一半](https://mp.weixin.qq.com/s/ALjmwXM0CIu7qgTjX2XDgQ)**
   - 成交量尖峰识别：识别2倍以上异常放量
   - 买卖量智能分解：基于收盘价位置估算买卖力量
   - 量价关系分析：放量上涨、缩量上涨、放量下跌、缩量下跌
   - 增强版成交量指标（付费会员专享）

8. **[量化指标解码08：SuperTrend超级趋势指标深度解码](https://mp.weixin.qq.com/s/FslARKEL2OwVX2blCvtdnA)**
   - SuperTrend指标原理与计算方法
   - 趋势识别与信号生成机制
   - 参数优化与实战应用
   - 与其他指标的组合策略

---

## 开发规范

### 代码风格
- 使用Python 3.10+
- 遵循PEP 8代码规范
- 使用类型注解
- 添加详细的中文注释

### 提交规范
- feat: 新功能
- fix: 修复bug
- docs: 文档更新
- style: 代码格式调整
- refactor: 代码重构
- test: 测试相关
- chore: 构建过程或辅助工具的变动

## 许可证

MIT License

## 联系方式

- 公众号：堂主的ATMQuant
- GitHub：https://github.com/seasonstar/atmquant
