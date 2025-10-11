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
