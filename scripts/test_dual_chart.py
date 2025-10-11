#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试双图并排显示功能
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from PySide6.QtWidgets import QApplication

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from vnpy.trader.object import BarData
from vnpy.trader.constant import Exchange, Interval
from core.charts import DualChartWidget


def generate_test_bars(count: int = 1000, start_time: datetime = None) -> list:
    """生成测试K线数据"""
    if start_time is None:
        start_time = datetime.now() - timedelta(days=30)

    bars = []
    for i in range(count):
        bar = BarData(
            symbol="rb2505",
            exchange=Exchange.SHFE,
            datetime=start_time + timedelta(minutes=i),
            interval=Interval.MINUTE,
            open_price=3500 + i * 0.5,
            high_price=3510 + i * 0.5,
            low_price=3490 + i * 0.5,
            close_price=3505 + i * 0.5,
            volume=1000 + i * 10,
            turnover=0,
            open_interest=50000,
            gateway_name="test"
        )
        bars.append(bar)

    return bars


def test_dual_chart():
    """测试双图组件"""
    app = QApplication(sys.argv)

    # 创建双图组件
    dual_chart = DualChartWidget(left_period="15m", right_period="1h")
    dual_chart.setWindowTitle("双图并排显示测试")
    dual_chart.resize(1600, 900)

    # 生成测试数据
    test_bars = generate_test_bars(count=2000)
    print(f"生成测试数据: {len(test_bars)} 根1分钟K线")

    # 更新数据
    dual_chart.update_history(test_bars)
    dual_chart.set_trading_session_by_symbol("rb2505", "SHFE")

    # 显示窗口
    dual_chart.show()

    print("\n双图组件测试启动成功！")
    print("- 左侧图表：15分钟周期")
    print("- 右侧图表：1小时周期")
    print("- 点击'启用同步'按钮可以同步两个图表的时间轴")
    print("- 可以在周期选择面板中切换不同的周期")

    sys.exit(app.exec())


if __name__ == "__main__":
    test_dual_chart()
