#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
四图视图组件测试脚本
测试QuadChartWidget的基本功能
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_quad_chart_import():
    """测试四图组件导入"""
    print("=" * 50)
    print("测试1: 导入四图组件")
    print("=" * 50)

    try:
        from core.charts import QuadChartWidget, QuadChartTimeAxisSync
        print("✓ QuadChartWidget 导入成功")
        print("✓ QuadChartTimeAxisSync 导入成功")
        return True
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False

def test_quad_chart_creation():
    """测试四图组件创建"""
    print("\n" + "=" * 50)
    print("测试2: 创建四图组件实例")
    print("=" * 50)

    try:
        from core.charts import QuadChartWidget

        # 创建四图组件（使用默认周期）
        quad_chart = QuadChartWidget()

        print(f"✓ 四图组件创建成功")
        print(f"  - 左上周期: {quad_chart.periods['top_left']}")
        print(f"  - 右上周期: {quad_chart.periods['top_right']}")
        print(f"  - 左下周期: {quad_chart.periods['bottom_left']}")
        print(f"  - 右下周期: {quad_chart.periods['bottom_right']}")
        print(f"  - 同步管理器: {type(quad_chart.sync_manager).__name__}")

        return True
    except Exception as e:
        print(f"✗ 创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_quad_chart_structure():
    """测试四图组件结构"""
    print("\n" + "=" * 50)
    print("测试3: 检查四图组件结构")
    print("=" * 50)

    try:
        from core.charts import QuadChartWidget

        quad_chart = QuadChartWidget()

        # 检查四个图表是否存在
        charts_ok = all([
            hasattr(quad_chart, 'top_left_chart'),
            hasattr(quad_chart, 'top_right_chart'),
            hasattr(quad_chart, 'bottom_left_chart'),
            hasattr(quad_chart, 'bottom_right_chart')
        ])

        if charts_ok:
            print("✓ 四个图表组件都存在")
        else:
            print("✗ 缺少某些图表组件")
            return False

        # 检查同步管理器
        if hasattr(quad_chart, 'sync_manager'):
            print("✓ 同步管理器存在")
            print(f"  - 同步状态: {'启用' if quad_chart.sync_manager.sync_enabled else '禁用'}")
        else:
            print("✗ 同步管理器不存在")
            return False

        # 检查方法是否存在
        methods = [
            'update_history',
            'set_trading_session_by_symbol',
            'clear_all',
            'set_period',
            '_aggregate_bars',
            '_on_period_changed'
        ]

        for method_name in methods:
            if hasattr(quad_chart, method_name):
                print(f"✓ 方法 {method_name} 存在")
            else:
                print(f"✗ 方法 {method_name} 不存在")
                return False

        return True

    except Exception as e:
        print(f"✗ 检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_quad_chart_in_widget():
    """测试四图在CandleChartDialog中的集成"""
    print("\n" + "=" * 50)
    print("测试4: 检查CandleChartDialog集成")
    print("=" * 50)

    try:
        # 检查widget.py中是否有quad_chart相关代码
        widget_file = project_root / "vnpy_ctabacktester" / "ui" / "widget.py"

        if not widget_file.exists():
            print("✗ widget.py 文件不存在")
            return False

        content = widget_file.read_text(encoding='utf-8')

        checks = [
            ("QuadChartWidget导入", "from core.charts import QuadChartWidget"),
            ("四图组件创建", "self.quad_chart = QuadChartWidget"),
            ("四图按钮", "self.quad_mode_btn"),
            ("四图模式切换", "mode_id == 2"),
            ("四图周期按钮激活", "_activate_quad_chart_period_buttons"),
            ("四图交易连线", "_draw_quad_chart_trades")
        ]

        all_ok = True
        for check_name, check_str in checks:
            if check_str in content:
                print(f"✓ {check_name}: 已实现")
            else:
                print(f"✗ {check_name}: 未找到")
                all_ok = False

        return all_ok

    except Exception as e:
        print(f"✗ 检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print(" 四图视图组件测试 ")
    print("=" * 60)

    results = []

    # 运行测试
    results.append(("导入测试", test_quad_chart_import()))
    results.append(("创建测试", test_quad_chart_creation()))
    results.append(("结构测试", test_quad_chart_structure()))
    results.append(("集成测试", test_quad_chart_in_widget()))

    # 汇总结果
    print("\n" + "=" * 60)
    print(" 测试结果汇总 ")
    print("=" * 60)

    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print("\n" + "=" * 60)
    print(f"测试完成: {passed}/{total} 通过")
    print("=" * 60)

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
