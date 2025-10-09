#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的小时双均线策略
演示如何使用交易时段配置的BarGenerator
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import time
from vnpy.trader.constant import Interval
from vnpy.trader.object import BarData
from vnpy.trader.utility import BarGenerator, ArrayManager
from core.strategies.base_strategy import BaseCtaStrategy

class SimpleHourMAStrategy(BaseCtaStrategy):
    """
    简单的小时双均线策略
    
    使用交易时段配置的BarGenerator，小时K线按实际交易时段合成，不会跨越休市时间
    """
    
    # 策略参数
    fast_window = 10    # 快速均线周期
    slow_window = 20    # 慢速均线周期
    fixed_size = 1      # 固定下单数量
    
    # 策略变量
    fast_ma = 0.0
    slow_ma = 0.0
    
    # 参数列表（用于优化）
    parameters = ["fast_window", "slow_window", "fixed_size"]
    
    # 变量列表（用于保存）
    variables = ["fast_ma", "slow_ma"]
    
    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """初始化策略"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        
        # 创建BarGenerator - 关键：传入hour_sessions参数
        self.bg = BarGenerator(
            on_bar=self.on_bar,
            window=1,
            on_window_bar=self.on_hour_bar,
            interval=Interval.HOUR,
            hour_sessions=self.trading_session.hour_sessions  # 使用交易时段配置
        )
        
        # 创建ArrayManager
        self.am = ArrayManager()
        
        self.logger.info("策略初始化完成")
        self.logger.info(f"交易时段: {self.trading_session.name}")
        self.logger.info(f"时段配置: {len(self.trading_session.hour_sessions)}个时段")
    
    def on_init(self):
        """策略初始化回调"""
        super().on_init()
        self.logger.info("开始加载历史数据")
        self.load_bar(10)
    
    def on_start(self):
        """策略启动回调"""
        super().on_start()
        self.logger.success("策略启动成功，开始运行")
    
    def on_stop(self):
        """策略停止回调"""
        super().on_stop()
        self.logger.info("策略已停止")
    
    def on_bar(self, bar):
        """
        1分钟K线回调
        
        将1分钟K线送入BarGenerator，当到达时段结束时，会自动调用on_hour_bar
        """
        self.bg.update_bar(bar)
    
    def on_hour_bar(self, bar):
        """
        小时K线回调
        
        这里的小时K线是按照交易时段生成的，不会跨越休市时间
        例如中国期货：
        - 09:00-09:59: 第1根小时K线
        - 10:00-11:14: 第2根小时K线（跳过10:15-10:30休息）
        - 11:15-14:14: 第3根小时K线（跳过11:30-13:30午休）
        - 14:15-14:59: 第4根小时K线
        """
        self.logger.info(f"小时K线: {bar.datetime}, O:{bar.open_price}, C:{bar.close_price}, V:{bar.volume}")
        
        # 更新ArrayManager
        self.am.update_bar(bar)
        if not self.am.inited:
            return
        
        # 计算均线
        self.fast_ma = self.am.sma(self.fast_window)
        self.slow_ma = self.am.sma(self.slow_window)
        
        # 取消所有未成交委托
        self.cancel_all()
        
        # 生成交易信号
        if self.pos == 0:
            # 无仓位，判断开仓信号
            if self.fast_ma > self.slow_ma:
                self.logger.info(f"做多信号: fast_ma({self.fast_ma:.2f}) > slow_ma({self.slow_ma:.2f})")
                self.buy(bar.close_price + 5, self.fixed_size)
            elif self.fast_ma < self.slow_ma:
                self.logger.info(f"做空信号: fast_ma({self.fast_ma:.2f}) < slow_ma({self.slow_ma:.2f})")
                self.short(bar.close_price - 5, self.fixed_size)
        
        elif self.pos > 0:
            # 持有多仓，判断平仓信号
            if self.fast_ma < self.slow_ma:
                self.logger.info(f"平多信号: fast_ma({self.fast_ma:.2f}) < slow_ma({self.slow_ma:.2f})")
                self.sell(bar.close_price - 5, abs(self.pos))
        
        elif self.pos < 0:
            # 持有空仓，判断平仓信号
            if self.fast_ma > self.slow_ma:
                self.logger.info(f"平空信号: fast_ma({self.fast_ma:.2f}) > slow_ma({self.slow_ma:.2f})")
                self.cover(bar.close_price + 5, abs(self.pos))
        
        # 更新UI
        self.put_event()


# ==================== 回测示例 ====================

if __name__ == "__main__":
    """运行回测"""
    from datetime import datetime
    from vnpy_ctabacktester.engine import BacktestingEngine
    
    print("="*60)
    print("简单小时双均线策略回测")
    print("="*60)
    
    # 创建回测引擎
    engine = BacktestingEngine()
    
    # 设置回测参数
    engine.set_parameters(
        vt_symbol="jm2501.DCE",      # 品种代码
        interval=Interval.MINUTE,     # 使用1分钟数据
        start=datetime(2024, 1, 1),   # 回测开始时间
        end=datetime(2024, 6, 30),    # 回测结束时间
        rate=0.0003,                  # 手续费率
        slippage=2,                   # 滑点
        size=100,                     # 合约乘数
        pricetick=0.5,                # 最小价格变动
        capital=1000000,              # 初始资金
    )
    
    # 添加策略
    engine.add_strategy(SimpleHourMAStrategy, {
        "fast_window": 10,
        "slow_window": 20,
        "fixed_size": 1
    })
    
    # 运行回测
    print("\n加载数据...")
    engine.load_data()
    
    print("运行回测...")
    engine.run_backtesting()
    
    print("计算统计...")
    df = engine.calculate_result()
    stats = engine.calculate_statistics()
    
    print("\n回测统计:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # 显示图表
    engine.show_chart()

