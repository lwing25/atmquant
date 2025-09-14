#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
3MA策略演示脚本
展示策略的基本使用方法
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from core.strategies.triple_ma_strategy import TripleMaStrategy

def demo_strategy_creation():
    """演示策略创建"""
    print("🎯 3MA策略演示")
    print("=" * 50)
    
    # 创建策略实例
    class MockEngine:
        def write_log(self, msg, strategy=None):
            print(f"📝 日志: {msg}")
    
    strategy = TripleMaStrategy(
        cta_engine=MockEngine(),
        strategy_name="3MA_Demo",
        vt_symbol="rb2501.SHFE",
        setting={
            "short_window": 5,
            "mid_window": 20,
            "long_window": 60,
            "ma_type": "SMA",
            "signal_timeframe": 15,
            "trade_timeframe": 5,
            "stop_loss_pct": 2.0,
            "take_profit_pct": 4.0,
            "trailing_stop_pct": 1.0,
        }
    )
    
    print(f"📊 策略名称: {strategy.strategy_name}")
    print(f"📊 交易品种: {strategy.vt_symbol}")
    print(f"📊 策略状态: {strategy.strategy_status}")
    
    print("\n⚙️ 策略参数:")
    for param in strategy.parameters:
        value = getattr(strategy, param)
        print(f"  {param}: {value}")
    
    print("\n📈 策略变量:")
    for var in strategy.variables:
        value = getattr(strategy, var)
        print(f"  {var}: {value}")
    
    return strategy

def demo_strategy_usage():
    """演示策略使用方法"""
    print("\n🔧 策略使用方法演示")
    print("=" * 50)
    
    print("1. 策略初始化:")
    print("   strategy.on_init()")
    
    print("\n2. 策略启动:")
    print("   strategy.on_start()")
    
    print("\n3. 数据更新:")
    print("   strategy.on_tick(tick_data)  # Tick数据")
    print("   strategy.on_bar(bar_data)    # K线数据")
    
    print("\n4. 交易执行:")
    print("   strategy.buy(price, volume)      # 买入")
    print("   strategy.sell(price, volume)     # 卖出")
    print("   strategy.short(price, volume)    # 做空")
    print("   strategy.cover(price, volume)    # 平空")
    
    print("\n5. 风险控制:")
    print("   strategy.cancel_all()            # 撤销所有委托")
    print("   strategy.update_stop_loss_take_profit(bar)  # 更新止盈止损")
    
    print("\n6. 策略停止:")
    print("   strategy.on_stop()")

def demo_strategy_features():
    """演示策略特性"""
    print("\n✨ 策略特性演示")
    print("=" * 50)
    
    print("🎯 核心特性:")
    print("  • 多时间周期分析（信号周期 + 交易周期）")
    print("  • 支持SMA和EMA两种均线类型")
    print("  • 三均线趋势判断（短期、中期、长期）")
    print("  • 动态止盈止损机制")
    print("  • 跟踪止损功能")
    print("  • 集成日志和告警系统")
    
    print("\n📊 交易信号:")
    print("  • 做多: 短期MA上穿中期MA + 趋势向上")
    print("  • 做空: 短期MA下穿中期MA + 趋势向下")
    print("  • 趋势判断: 基于长期MA位置")
    
    print("\n🛡️ 风险控制:")
    print("  • 固定止损: 基于入场价格的百分比")
    print("  • 跟踪止损: 基于最高/最低价的百分比")
    print("  • 止盈机制: 基于入场价格的百分比")
    print("  • 仓位管理: 支持多空转换")

def main():
    """主演示函数"""
    try:
        # 创建策略实例
        strategy = demo_strategy_creation()
        
        # 演示使用方法
        demo_strategy_usage()
        
        # 演示策略特性
        demo_strategy_features()
        
        print("\n🎉 演示完成！")
        print("\n💡 下一步:")
        print("  1. 运行回测: python scripts/backtest_3ma_strategy.py")
        print("  2. 参数优化: python scripts/optimize_3ma_strategy.py")
        print("  3. 实盘部署: 在vnpy界面中添加策略")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
