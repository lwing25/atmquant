#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
3MA策略参数优化
"""

import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from vnpy_ctabacktester import BacktestingEngine
from core.strategies.triple_ma_strategy import TripleMaStrategy


def run_optimization():
    """运行参数优化"""
    # 创建回测引擎
    engine = BacktestingEngine()
    
    # 设置回测参数
    engine.set_parameters(
        vt_symbol="rb2501.SHFE",
        interval="1m",
        start=datetime(2024, 1, 1),
        end=datetime(2024, 12, 31),
        rate=0.0003,
        slippage=0.2,
        size=10,
        pricetick=1,
        capital=1_000_000,
    )
    
    # 添加策略
    engine.add_strategy(TripleMaStrategy, {})
    
    # 设置优化参数
    params = {
        "short_window": range(3, 11, 2),      # 3, 5, 7, 9
        "mid_window": range(15, 31, 5),       # 15, 20, 25, 30
        "long_window": range(50, 101, 10),    # 50, 60, 70, 80, 90, 100
        "stop_loss_pct": [1.5, 2.0, 2.5, 3.0],
        "take_profit_pct": [3.0, 4.0, 5.0, 6.0],
    }
    
    # 运行优化
    engine.run_optimization(params, target_name="sharpe_ratio")
    
    # 显示优化结果
    engine.show_chart()


if __name__ == "__main__":
    print("🔧 开始3MA策略参数优化...")
    run_optimization()
    print("✅ 优化完成！")
