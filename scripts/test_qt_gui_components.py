#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ATMQuant GUI测试脚本

使用qt-testing skill测试图表组件和指标的渲染效果
"""

import sys
from pathlib import Path

# 添加qt-testing skill脚本路径
sys.path.insert(0, "/Users/mac/.claude/skills/qt-testing/scripts")

from atmquant_helpers import (
    create_sample_bars,
    create_test_chart,
    test_indicator,
    test_chart_views,
)
from qt_capture import capture_widget, init_qt


def test_basic_chart():
    """测试基础图表组件"""
    print("\n" + "=" * 60)
    print("Test 1: Basic Chart Component")
    print("=" * 60)

    try:
        # 生成测试数据
        print("Generating test data...")
        bars = create_sample_bars(count=100, symbol="RB2505", interval="5m")
        print(f"  ✓ Generated {len(bars)} bars")

        # 创建图表
        print("Creating chart...")
        chart, app = create_test_chart(bars)
        print("  ✓ Chart created")

        # 捕获截图
        print("Capturing screenshot...")
        path = capture_widget(chart, "test_basic_chart")
        print(f"  ✓ Screenshot saved: {path}")

        # 清理
        try:
            chart.close()
        except AttributeError:
            pass  # 忽略pyqtgraph清理错误

        return path

    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return None


def test_chart_with_boll():
    """测试BOLL指标"""
    print("\n" + "=" * 60)
    print("Test 2: Chart with BOLL Indicator")
    print("=" * 60)

    try:
        # 生成测试数据
        bars = create_sample_bars(count=100, symbol="RB2505", interval="15m")
        print(f"  ✓ Generated {len(bars)} bars")

        # 测试BOLL指标
        print("Testing BOLL indicator...")
        path = test_indicator("boll", bars)
        print(f"  ✓ Screenshot saved: {path}")

        return path

    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return None


def test_chart_views_layout():
    """测试多图表视图布局"""
    print("\n" + "=" * 60)
    print("Test 3: Chart View Layouts (Single/Dual/Quad)")
    print("=" * 60)

    try:
        results = test_chart_views()

        print("\nResults:")
        for view_name, path in results.items():
            if path:
                print(f"  ✓ {view_name} view: {path}")
            else:
                print(f"  ✗ {view_name} view: Failed")

        return results

    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return None


def test_enhanced_chart_widget():
    """测试EnhancedChartWidget的详细功能"""
    print("\n" + "=" * 60)
    print("Test 4: EnhancedChartWidget Detailed Test")
    print("=" * 60)

    try:
        from core.charts.enhanced_chart_widget import EnhancedChartWidget

        app = init_qt()

        # 创建图表
        print("Creating EnhancedChartWidget...")
        chart = EnhancedChartWidget()

        # 生成测试数据
        print("Loading test data...")
        bars = create_sample_bars(count=150, base_price=3500.0, volatility=0.03)
        chart.update_history(bars)

        # 捕获初始状态
        path1 = capture_widget(chart, "enhanced_chart_step1_with_data")
        print(f"  ✓ Step 1 - With data: {path1}")

        # 注意：这里不能直接调用add_indicator，因为EnhancedChartWidget的实际API可能不同
        # 这只是演示测试流程

        try:
            chart.close()
        except AttributeError:
            pass  # 忽略pyqtgraph清理错误

        return path1

    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return None


def main():
    """运行所有测试"""
    print("ATMQuant GUI Testing Suite")
    print("Using qt-testing skill for visual inspection")
    print("")

    # 确保输出目录存在
    output_dir = Path("scratch/.qt-screenshots")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Screenshots will be saved to: {output_dir.absolute()}\n")

    # 运行测试
    results = []

    # 测试1: 基础图表
    result1 = test_basic_chart()
    results.append(("Basic Chart", result1))

    # 测试2: BOLL指标
    result2 = test_chart_with_boll()
    results.append(("BOLL Indicator", result2))

    # 测试3: 图表视图布局
    result3 = test_chart_views_layout()
    if result3:
        for view_name, path in result3.items():
            results.append((f"{view_name.capitalize()} View", path))

    # 测试4: EnhancedChartWidget详细测试
    result4 = test_enhanced_chart_widget()
    results.append(("EnhancedChartWidget", result4))

    # 汇总结果
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    success_count = 0
    for test_name, result in results:
        if result:
            print(f"✓ {test_name}: PASSED")
            success_count += 1
        else:
            print(f"✗ {test_name}: FAILED")

    total_tests = len(results)
    print(f"\nTotal: {success_count}/{total_tests} tests passed")

    # 提示如何查看截图
    print("\n" + "=" * 60)
    print("Next Steps")
    print("=" * 60)
    print("1. Use the Read tool to view each screenshot")
    print("2. Analyze with vision to verify rendering correctness")
    print("3. Check for:")
    print("   - No emoji characters (macOS crash prevention)")
    print("   - Correct K-line rendering")
    print("   - Proper indicator display")
    print("   - Clear axis labels and legends")
    print("\nScreenshots location:")
    print(f"  {output_dir.absolute()}")


if __name__ == "__main__":
    main()
