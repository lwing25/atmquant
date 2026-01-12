"""
渐进式测试版本 - 用于排查 RedesignedBacktesterManager 的 bus error 问题

使用方法：
在 widget.py 的末尾修改 BacktesterManager 继承的父类：
    class BacktesterManager(TestVersion1):  # 从 TestVersion1 开始测试
        pass

如果某个版本测试通过，就测试下一个版本，直到找到导致 bus error 的具体组件。
"""
from datetime import datetime, timedelta
from typing import Any, Dict

from vnpy.trader.constant import Interval, Direction, Exchange
from vnpy.trader.engine import MainEngine, BaseEngine
from vnpy.trader.ui import QtCore, QtWidgets, QtGui
from vnpy.trader.utility import load_json, save_json
from vnpy.event import Event, EventEngine

from ..locale import _
from ..engine import (
    APP_NAME,
    EVENT_BACKTESTER_LOG,
    EVENT_BACKTESTER_BACKTESTING_FINISHED,
    EVENT_BACKTESTER_OPTIMIZATION_FINISHED,
)


class TestVersion1(QtWidgets.QWidget):
    """
    测试版本 1: 最小化框架
    - 只有基本窗口和标题
    - 无样式表
    - 无复杂组件

    测试目的：验证基本 Qt Widget 是否能正常初始化
    """

    setting_filename: str = "cta_backtester_setting.json"

    signal_log: QtCore.Signal = QtCore.Signal(Event)
    signal_backtesting_finished: QtCore.Signal = QtCore.Signal(Event)
    signal_optimization_finished: QtCore.Signal = QtCore.Signal(Event)

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine) -> None:
        super().__init__()

        self.main_engine: MainEngine = main_engine
        self.event_engine: EventEngine = event_engine
        self.backtester_engine: BaseEngine = main_engine.get_engine(APP_NAME)

        # 延迟初始化标志
        self._engine_initialized: bool = False

        self.init_ui()
        self.register_event()
        self.load_backtesting_setting()

    def init_ui(self) -> None:
        """初始化界面 - 最小化版本"""
        self.setWindowTitle("CTA回测 - 测试版本1（最小化）")
        self.setMinimumSize(800, 600)

        # 只显示一个简单的标签
        layout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel("测试版本1：最小化框架\n\n如果看到这个界面没有闪退，说明基本框架正常。\n请继续测试 TestVersion2。")
        label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(label)

        self.setLayout(layout)

    def register_event(self) -> None:
        """注册事件监听"""
        self.signal_log.connect(self.process_log_event)
        self.event_engine.register(EVENT_BACKTESTER_LOG, self.signal_log.emit)

    def process_log_event(self, event: Event) -> None:
        """处理日志事件"""
        pass

    def load_backtesting_setting(self) -> None:
        """加载回测设置"""
        pass

    def ensure_engine_initialized(self) -> None:
        """确保引擎已初始化"""
        if not self._engine_initialized:
            self.backtester_engine.init_engine()
            self._engine_initialized = True


class TestVersion2(TestVersion1):
    """
    测试版本 2: 添加左侧面板
    - 基本框架 + 左侧参数设置面板
    - 无样式表
    - 无 emoji

    测试目的：验证表单控件是否导致问题
    """

    def init_ui(self) -> None:
        """初始化界面 - 添加左侧面板"""
        self.setWindowTitle("CTA回测 - 测试版本2（基本表单）")
        self.setMinimumSize(1000, 700)

        main_layout = QtWidgets.QHBoxLayout()

        # 左侧面板
        left_widget = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout()

        # 参数设置组
        param_group = QtWidgets.QGroupBox("回测参数设置")
        param_layout = QtWidgets.QFormLayout()

        # 创建基本控件（无特殊样式）
        self.class_combo = QtWidgets.QComboBox()
        self.symbol_line = QtWidgets.QLineEdit("jm2601.DCE")
        self.interval_combo = QtWidgets.QComboBox()

        for interval in Interval:
            self.interval_combo.addItem(interval.value)

        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=365)

        self.start_date_edit = QtWidgets.QDateEdit(
            QtCore.QDate(start_dt.year, start_dt.month, start_dt.day)
        )
        self.end_date_edit = QtWidgets.QDateEdit(QtCore.QDate.currentDate())

        self.rate_line = QtWidgets.QLineEdit("0.0001")
        self.capital_line = QtWidgets.QLineEdit("100000.0")

        # 添加到布局
        param_layout.addRow("交易策略:", self.class_combo)
        param_layout.addRow("本地代码:", self.symbol_line)
        param_layout.addRow("K线周期:", self.interval_combo)
        param_layout.addRow("开始日期:", self.start_date_edit)
        param_layout.addRow("结束日期:", self.end_date_edit)
        param_layout.addRow("手续费率:", self.rate_line)
        param_layout.addRow("回测资金:", self.capital_line)

        param_group.setLayout(param_layout)
        left_layout.addWidget(param_group)
        left_layout.addStretch()

        left_widget.setLayout(left_layout)
        left_widget.setMaximumWidth(350)

        # 右侧信息
        right_widget = QtWidgets.QLabel(
            "测试版本2：基本表单控件\n\n"
            "如果看到左侧表单没有闪退，说明表单控件正常。\n"
            "请继续测试 TestVersion3。"
        )
        right_widget.setAlignment(QtCore.Qt.AlignCenter)

        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget, 1)

        self.setLayout(main_layout)


class TestVersion3(TestVersion2):
    """
    测试版本 3: 添加右侧选项卡
    - 左侧面板 + 右侧 QTabWidget
    - 无样式表
    - 无复杂表格组件

    测试目的：验证 QTabWidget 是否导致问题
    """

    def init_ui(self) -> None:
        """初始化界面 - 添加选项卡"""
        self.setWindowTitle("CTA回测 - 测试版本3（选项卡）")
        self.setMinimumSize(1200, 800)

        main_layout = QtWidgets.QHBoxLayout()

        # 左侧面板（复用 TestVersion2）
        left_widget = self._create_left_panel()

        # 右侧选项卡
        right_widget = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout()

        tab_widget = QtWidgets.QTabWidget()

        # 添加简单的选项卡
        tab1 = QtWidgets.QLabel("选项卡1：核心指标")
        tab1.setAlignment(QtCore.Qt.AlignCenter)
        tab_widget.addTab(tab1, "核心指标")

        tab2 = QtWidgets.QLabel("选项卡2：详细指标")
        tab2.setAlignment(QtCore.Qt.AlignCenter)
        tab_widget.addTab(tab2, "详细指标")

        tab3 = QtWidgets.QLabel("选项卡3：优化结果")
        tab3.setAlignment(QtCore.Qt.AlignCenter)
        tab_widget.addTab(tab3, "优化结果")

        right_layout.addWidget(tab_widget)
        right_widget.setLayout(right_layout)

        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget, 1)

        self.setLayout(main_layout)

    def _create_left_panel(self) -> QtWidgets.QWidget:
        """创建左侧面板"""
        left_widget = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout()

        param_group = QtWidgets.QGroupBox("回测参数设置")
        param_layout = QtWidgets.QFormLayout()

        self.class_combo = QtWidgets.QComboBox()
        self.symbol_line = QtWidgets.QLineEdit("jm2601.DCE")
        self.interval_combo = QtWidgets.QComboBox()

        for interval in Interval:
            self.interval_combo.addItem(interval.value)

        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=365)

        self.start_date_edit = QtWidgets.QDateEdit(
            QtCore.QDate(start_dt.year, start_dt.month, start_dt.day)
        )
        self.end_date_edit = QtWidgets.QDateEdit(QtCore.QDate.currentDate())

        self.rate_line = QtWidgets.QLineEdit("0.0001")
        self.capital_line = QtWidgets.QLineEdit("100000.0")

        param_layout.addRow("交易策略:", self.class_combo)
        param_layout.addRow("本地代码:", self.symbol_line)
        param_layout.addRow("K线周期:", self.interval_combo)
        param_layout.addRow("开始日期:", self.start_date_edit)
        param_layout.addRow("结束日期:", self.end_date_edit)
        param_layout.addRow("手续费率:", self.rate_line)
        param_layout.addRow("回测资金:", self.capital_line)

        param_group.setLayout(param_layout)
        left_layout.addWidget(param_group)
        left_layout.addStretch()

        left_widget.setLayout(left_layout)
        left_widget.setMaximumWidth(350)

        return left_widget


class TestVersion4(TestVersion3):
    """
    测试版本 4: 添加简单图表区域
    - 左侧面板 + 右侧选项卡 + 图表占位符
    - 无 emoji
    - 无 pyqtgraph

    测试目的：验证图表区域布局是否导致问题
    """

    def init_ui(self) -> None:
        """初始化界面 - 添加图表区域"""
        self.setWindowTitle("CTA回测 - 测试版本4（图表占位符）")
        self.setMinimumSize(1400, 800)

        main_layout = QtWidgets.QHBoxLayout()

        # 左侧面板
        left_widget = self._create_left_panel()

        # 右侧布局
        right_widget = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout()

        # 选项卡（上半部分）
        tab_widget = QtWidgets.QTabWidget()
        tab1 = QtWidgets.QLabel("选项卡1：核心指标")
        tab1.setAlignment(QtCore.Qt.AlignCenter)
        tab_widget.addTab(tab1, "核心指标")

        # 图表区域（下半部分）
        charts_widget = QtWidgets.QWidget()
        charts_layout = QtWidgets.QVBoxLayout()

        chart1_label = QtWidgets.QLabel("图表1：账户净值（占位符）")
        chart1_label.setAlignment(QtCore.Qt.AlignCenter)
        chart1_label.setStyleSheet("border: 1px solid gray; padding: 20px;")

        chart2_label = QtWidgets.QLabel("图表2：每日盈亏（占位符）")
        chart2_label.setAlignment(QtCore.Qt.AlignCenter)
        chart2_label.setStyleSheet("border: 1px solid gray; padding: 20px;")

        charts_layout.addWidget(chart1_label)
        charts_layout.addWidget(chart2_label)
        charts_widget.setLayout(charts_layout)

        # 上下布局
        right_layout.addWidget(tab_widget, 1)
        right_layout.addWidget(charts_widget, 1)
        right_widget.setLayout(right_layout)

        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget, 1)

        self.setLayout(main_layout)


class TestVersion5(TestVersion4):
    """
    测试版本 5: 添加深色样式表
    - 完整布局 + 深色主题样式
    - 无 emoji
    - 无复杂图表组件

    测试目的：验证样式表是否导致问题
    """

    def init_ui(self) -> None:
        """初始化界面 - 添加样式表"""
        self.setWindowTitle("CTA回测 - 测试版本5（深色样式）")
        self.setMinimumSize(1400, 800)

        # 应用深色样式表
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #444;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QLineEdit, QComboBox, QDateEdit {
                background-color: #333;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px 8px;
                color: #fff;
            }
            QPushButton {
                background-color: #007acc;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                color: white;
                font-weight: bold;
            }
            QLabel {
                color: #ccc;
            }
        """)

        # 调用父类的布局创建
        super().init_ui()


class TestVersion6(TestVersion5):
    """
    测试版本 6: 添加 emoji 字符
    - 完整布局 + 样式 + emoji
    - 测试 emoji 是否导致问题
    """

    def init_ui(self) -> None:
        """初始化界面 - 添加 emoji（用于测试emoji导致的崩溃）"""
        super().init_ui()
        self.setWindowTitle("CTA回测 - 测试版本6（含emoji）")

        # 在窗口顶部添加带 emoji 的标签（故意保留用于测试）
        if self.layout():
            emoji_label = QtWidgets.QLabel("📊 回测系统 📈")
            emoji_label.setStyleSheet("font-size: 16px; padding: 10px;")
            emoji_label.setAlignment(QtCore.Qt.AlignCenter)
            self.layout().insertWidget(0, emoji_label)
