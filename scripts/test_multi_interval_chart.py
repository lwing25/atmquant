#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试多周期图表功能
"""

import sys
from datetime import datetime, timedelta, time
from pathlib import Path
import random

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from vnpy.trader.ui import QtWidgets, QtCore, create_qapp
from vnpy.trader.database import get_database
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import BarData

from core.charts.enhanced_chart_widget import EnhancedChartWidget


def generate_sample_bars(start_time: datetime, count: int = 1000) -> list:
    """
    生成模拟的1分钟K线数据用于测试
    
    Args:
        start_time: 起始时间
        count: 生成的K线数量
    
    Returns:
        K线数据列表
    """
    bars = []
    current_time = start_time
    base_price = 2000.0
    
    for i in range(count):
        # 跳过非交易时间（简单处理）
        if current_time.hour < 9 or current_time.hour >= 15:
            if current_time.hour >= 21 or current_time.hour < 2:
                pass  # 夜盘时间
            else:
                current_time += timedelta(minutes=1)
                continue
        
        # 生成随机价格波动
        change = random.uniform(-5, 5)
        open_price = base_price + random.uniform(-2, 2)
        close_price = open_price + change
        high_price = max(open_price, close_price) + random.uniform(0, 3)
        low_price = min(open_price, close_price) - random.uniform(0, 3)
        
        bar = BarData(
            symbol="TEST",
            exchange=Exchange.DCE,
            datetime=current_time,
            interval=Interval.MINUTE,
            open_price=open_price,
            high_price=high_price,
            low_price=low_price,
            close_price=close_price,
            volume=random.randint(100, 1000),
            turnover=random.uniform(100000, 1000000),
            open_interest=random.randint(10000, 50000),
            gateway_name="TEST"
        )
        
        bars.append(bar)
        base_price = close_price
        current_time += timedelta(minutes=1)
    
    return bars


def test_multi_interval_with_sample_data():
    """使用模拟数据测试多周期图表功能"""
    # 创建应用
    qapp = create_qapp()
    
    # 创建图表窗口
    chart = EnhancedChartWidget()
    chart.resize(1400, 800)
    chart.show()
    
    # 生成模拟数据
    print("正在生成模拟数据...")
    start_time = datetime.now() - timedelta(days=5)
    bars = generate_sample_bars(start_time, count=2000)
    
    print(f"生成了 {len(bars)} 条1分钟K线数据")
    print(f"第一条: {bars[0].datetime}")
    print(f"最后一条: {bars[-1].datetime}")
    
    # 更新图表数据
    chart.update_history(bars)
    
    print("\n✓ 图表已打开，可以测试以下功能：")
    print("=" * 60)
    print("1. 点击左侧面板的不同周期按钮切换周期")
    print("   - 1分钟：显示原始K线")
    print("   - 5分钟：5根1分钟K线聚合为1根")
    print("   - 15分钟：15根1分钟K线聚合为1根")
    print("   - 1小时：60根1分钟K线聚合为1根")
    print("   - 日线：所有日内K线聚合为1根")
    print()
    print("2. 观察K线数据是否正确聚合")
    print("   - K线数量应该减少")
    print("   - 开盘价、最高价、最低价、收盘价应该正确")
    print()
    print("3. 观察按钮激活状态是否正确")
    print("   - 只有一个按钮显示为激活状态（蓝色高亮）")
    print()
    print("4. 观察指标是否正确重新计算")
    print("   - 切换周期后，指标应该重新计算并显示")
    print("=" * 60)
    
    # 运行应用
    qapp.exec()


def test_multi_interval_with_db_data():
    """使用数据库数据测试多周期图表功能"""
    # 创建应用
    qapp = create_qapp()
    
    # 创建图表窗口
    chart = EnhancedChartWidget()
    chart.resize(1400, 800)
    chart.show()
    
    # 获取数据库
    database = get_database()
    
    # 优先使用 jm2601.DCE 的数据
    symbol = "jm2601"
    exchange = Exchange.DCE
    
    print(f"正在加载数据: {symbol}.{exchange.value}")
    
    # 加载最近的数据
    end = datetime.now()
    start = end - timedelta(days=30)  # 加载30天数据
    
    bars = database.load_bar_data(
        symbol=symbol,
        exchange=exchange,
        interval=Interval.MINUTE,
        start=start,
        end=end
    )
    
    if not bars:
        print(f"未找到 {symbol}.{exchange.value} 的数据")
        print("\n正在查询数据库中的其他数据...")
        overview = database.get_bar_overview()
        
        if not overview:
            print("数据库中没有数据，使用模拟数据")
            return test_multi_interval_with_sample_data()
        
        print(f"\n找到 {len(overview)} 个品种的数据：")
        for i, o in enumerate(overview[:10]):
            print(f"{i+1}. {o.symbol}.{o.exchange} - {o.interval} - {o.count}条")
        
        # 使用第一个1分钟数据
        minute_data = [o for o in overview if o.interval == Interval.MINUTE.value]
        if not minute_data:
            print("\n没有1分钟数据，使用模拟数据")
            return test_multi_interval_with_sample_data()
        
        first = minute_data[0]
        print(f"\n使用 {first.symbol}.{first.exchange} 的数据进行测试")
        
        bars = database.load_bar_data(
            symbol=first.symbol,
            exchange=Exchange(first.exchange),
            interval=Interval.MINUTE,
            start=start,
            end=end
        )
        
        if not bars:
            print("加载数据失败，使用模拟数据")
            return test_multi_interval_with_sample_data()
    
    print(f"✓ 加载了 {len(bars)} 条1分钟K线数据")
    print(f"  时间范围: {bars[0].datetime} ~ {bars[-1].datetime}")
    
    # 自动识别并设置交易时段
    chart.set_trading_session_by_symbol(symbol, exchange.value)
    
    # 显示交易时段信息
    if chart.trading_session:
        print(f"\n✓ 交易时段设置: {chart.trading_session.name}")
        print(f"  时区: {chart.trading_session.timezone}")
        print(f"  收盘时间: {chart.trading_session.daily_end.strftime('%H:%M')}")
        
        if chart.trading_session.hour_sessions:
            print(f"  日盘时段 ({len(chart.trading_session.hour_sessions)}个):")
            for i, (start, end) in enumerate(chart.trading_session.hour_sessions, 1):
                print(f"    时段{i}: {start.strftime('%H:%M')} - {end.strftime('%H:%M')}")
        
        if chart.trading_session.has_night_session and chart.trading_session.night_sessions:
            print(f"  夜盘时段 ({len(chart.trading_session.night_sessions)}个):")
            for i, (start, end) in enumerate(chart.trading_session.night_sessions, 1):
                print(f"    时段{i}: {start.strftime('%H:%M')} - {end.strftime('%H:%M')}")
    
    # 更新图表数据
    chart.update_history(bars)
    
    print("\n✓ 图表已打开，可以测试多周期切换功能")
    print("=" * 60)
    print("测试要点：")
    print("1. 点击左侧不同周期按钮，观察K线数量变化")
    print("2. 检查X轴时间是否正确显示对应周期的时间")
    print("3. 验证按钮激活状态（蓝色高亮）")
    print("4. 观察技术指标是否正确重新计算")
    print("=" * 60)
    
    # 运行应用
    qapp.exec()


if __name__ == "__main__":
    # 优先尝试使用数据库数据，如果没有则使用模拟数据
    try:
        test_multi_interval_with_db_data()
    except Exception as e:
        print(f"使用数据库数据失败: {e}")
        print("切换到模拟数据")
        test_multi_interval_with_sample_data()

