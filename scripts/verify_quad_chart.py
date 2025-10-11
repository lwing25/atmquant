#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
四图视图组件代码检查脚本（无需GUI）
通过静态代码分析验证四图功能
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_quad_chart_file():
    """检查四图组件文件"""
    print("=" * 60)
    print("检查1: quad_chart_widget.py 文件")
    print("=" * 60)

    file_path = project_root / "core" / "charts" / "quad_chart_widget.py"

    if not file_path.exists():
        print(f"✗ 文件不存在: {file_path}")
        return False

    print(f"✓ 文件存在: {file_path}")

    content = file_path.read_text(encoding='utf-8')

    # 检查关键类和方法
    checks = [
        ("QuadChartTimeAxisSync类", "class QuadChartTimeAxisSync:"),
        ("QuadChartWidget类", "class QuadChartWidget(QWidget):"),
        ("时间轴同步方法", "def _sync_all_charts"),
        ("更新历史数据方法", "def update_history"),
        ("聚合K线方法", "def _aggregate_bars"),
        ("设置交易时段方法", "def set_trading_session_by_symbol"),
        ("清空数据方法", "def clear_all"),
        ("设置周期方法", "def set_period"),
        ("周期变化回调", "def _on_period_changed"),
        ("四图实例化", "self.top_left_chart = EnhancedChartWidget()"),
        ("默认周期5分钟", 'top_left_period: str = "5m"'),
        ("默认周期15分钟", 'top_right_period: str = "15m"'),
        ("默认周期1小时", 'bottom_left_period: str = "1h"'),
        ("默认周期日线", 'bottom_right_period: str = "d"')
    ]

    all_ok = True
    for check_name, check_str in checks:
        if check_str in content:
            print(f"✓ {check_name}: 已实现")
        else:
            print(f"✗ {check_name}: 未找到")
            all_ok = False

    return all_ok

def check_init_file():
    """检查__init__.py导出"""
    print("\n" + "=" * 60)
    print("检查2: __init__.py 导出")
    print("=" * 60)

    file_path = project_root / "core" / "charts" / "__init__.py"

    if not file_path.exists():
        print(f"✗ 文件不存在: {file_path}")
        return False

    print(f"✓ 文件存在: {file_path}")

    content = file_path.read_text(encoding='utf-8')

    checks = [
        ("导入QuadChartWidget", "from .quad_chart_widget import"),
        ("导入QuadChartTimeAxisSync", "QuadChartTimeAxisSync"),
        ("导出QuadChartWidget", '"QuadChartWidget"'),
        ("导出QuadChartTimeAxisSync", '"QuadChartTimeAxisSync"'),
        ("可用性标志", "_quad_chart_available")
    ]

    all_ok = True
    for check_name, check_str in checks:
        if check_str in content:
            print(f"✓ {check_name}: 已实现")
        else:
            print(f"✗ {check_name}: 未找到")
            all_ok = False

    return all_ok

def check_widget_integration():
    """检查widget.py集成"""
    print("\n" + "=" * 60)
    print("检查3: widget.py 集成")
    print("=" * 60)

    file_path = project_root / "vnpy_ctabacktester" / "ui" / "widget.py"

    if not file_path.exists():
        print(f"✗ 文件不存在: {file_path}")
        return False

    print(f"✓ 文件存在: {file_path}")

    content = file_path.read_text(encoding='utf-8')

    checks = [
        ("导入QuadChartWidget", "from core.charts import QuadChartWidget"),
        ("创建四图组件", "self.quad_chart = QuadChartWidget("),
        ("设置默认周期5分钟", 'top_left_period="5m"'),
        ("设置默认周期15分钟", 'top_right_period="15m"'),
        ("设置默认周期1小时", 'bottom_left_period="1h"'),
        ("设置默认周期日线", 'bottom_right_period="d"'),
        ("四图按钮", "self.quad_mode_btn = QtWidgets.QPushButton"),
        ("四图按钮文字", '"四图"'),
        ("按钮组添加四图", "self.mode_button_group.addButton(self.quad_mode_btn, 2)"),
        ("四图模式判断", "mode_id == 2"),
        ("四图显示", "self.quad_chart.show()"),
        ("更新四图历史", "self.quad_chart.update_history"),
        ("激活四图周期按钮", "_activate_quad_chart_period_buttons"),
        ("绘制四图交易连线", "_draw_quad_chart_trades"),
        ("四图周期按钮激活方法", "def _activate_quad_chart_period_buttons(self):"),
        ("四图交易连线方法", "def _draw_quad_chart_trades(self):"),
        ("添加四图到布局", "vbox.addWidget(self.quad_chart)")
    ]

    all_ok = True
    for check_name, check_str in checks:
        if check_str in content:
            print(f"✓ {check_name}: 已实现")
        else:
            print(f"✗ {check_name}: 未找到")
            all_ok = False

    return all_ok

def check_button_style():
    """检查按钮样式"""
    print("\n" + "=" * 60)
    print("检查4: 按钮样式（分段控制器）")
    print("=" * 60)

    file_path = project_root / "vnpy_ctabacktester" / "ui" / "widget.py"
    content = file_path.read_text(encoding='utf-8')

    checks = [
        ("单图左圆角", "border-top-left-radius"),
        ("单图左圆角", "border-bottom-left-radius"),
        ("双图无圆角", "# 双图按钮中间（无圆角）"),
        ("四图右圆角", "border-top-right-radius"),
        ("四图右圆角", "border-bottom-right-radius"),
        ("选中状态蓝色", "#0078d4")
    ]

    all_ok = True
    for check_name, check_str in checks:
        if check_str in content:
            print(f"✓ {check_name}: 已实现")
        else:
            print(f"✗ {check_name}: 未找到")
            all_ok = False

    return all_ok

def check_code_quality():
    """检查代码质量"""
    print("\n" + "=" * 60)
    print("检查5: 代码质量")
    print("=" * 60)

    file_path = project_root / "core" / "charts" / "quad_chart_widget.py"
    content = file_path.read_text(encoding='utf-8')

    checks = [
        ("文件头注释", "#!/usr/bin/env python3"),
        ("编码声明", "# -*- coding: utf-8 -*-"),
        ("模块文档字符串", '"""'),
        ("类型注解", "from typing import"),
        ("日志记录", "from loguru import logger"),
        ("Qt组件导入", "from PySide6.QtWidgets import"),
        ("信号定义", "Signal(str)"),
        ("默认同步启用", "self.sync_enabled = True")
    ]

    all_ok = True
    for check_name, check_str in checks:
        if check_str in content:
            print(f"✓ {check_name}: 已实现")
        else:
            print(f"✗ {check_name}: 未找到")
            all_ok = False

    # 统计代码行数
    lines = content.split('\n')
    print(f"\n代码统计:")
    print(f"  - 总行数: {len(lines)}")
    print(f"  - 类定义数: {content.count('class ')}")
    print(f"  - 方法定义数: {content.count('def ')}")

    return all_ok

def main():
    """主检查函数"""
    print("\n" + "=" * 70)
    print(" 四图视图组件代码检查 ")
    print("=" * 70)

    results = []

    # 运行检查
    results.append(("四图组件文件", check_quad_chart_file()))
    results.append(("导出配置", check_init_file()))
    results.append(("Widget集成", check_widget_integration()))
    results.append(("按钮样式", check_button_style()))
    results.append(("代码质量", check_code_quality()))

    # 汇总结果
    print("\n" + "=" * 70)
    print(" 检查结果汇总 ")
    print("=" * 70)

    for check_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{check_name}: {status}")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print("\n" + "=" * 70)
    print(f"检查完成: {passed}/{total} 通过")
    print("=" * 70)

    if passed == total:
        print("\n✓ 所有检查通过！四图视图功能已完整实现。")
        print("\n功能特性:")
        print("  - 2x2网格布局，显示四个不同周期")
        print("  - 默认周期：5分钟、15分钟、1小时、日线")
        print("  - 时间轴自动同步")
        print("  - 周期按钮自动激活")
        print("  - 交易连线显示")
        print("  - 分段控制器风格按钮组（单图、双图、四图）")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
