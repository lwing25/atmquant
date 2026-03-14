from __future__ import annotations
from __future__ import annotations
from datetime import datetime, timedelta
from tzlocal import get_localzone_name

from vnpy.event import EventEngine, Event
from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import QtWidgets, QtCore
from vnpy.trader.event import EVENT_TICK
from vnpy.trader.object import ContractData, TickData, BarData, SubscribeRequest
from vnpy.trader.utility import ZoneInfo
from vnpy.trader.constant import Interval, Exchange
from vnpy_spreadtrading.base import SpreadItem, EVENT_SPREAD_DATA

# 使用增强版图表组件
from core.charts.enhanced_chart_widget import EnhancedChartWidget
# 导入交易时段配置
from config.trading_sessions_config import get_trading_session_by_symbol

from ..engine import APP_NAME, EVENT_CHART_HISTORY, ChartWizardEngine


class ChartWizardWidget(QtWidgets.QWidget):
    """K线图表控件"""

    signal_tick: QtCore.Signal = QtCore.Signal(Event)
    signal_spread: QtCore.Signal = QtCore.Signal(Event)
    signal_history: QtCore.Signal = QtCore.Signal(Event)

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine) -> None:
        """构造函数"""
        super().__init__()

        self.main_engine: MainEngine = main_engine
        self.event_engine: EventEngine = event_engine
        self.chart_engine: ChartWizardEngine = main_engine.get_engine(APP_NAME)

        self.charts: dict[str, EnhancedChartWidget] = {}

        self.init_ui()
        self.register_event()

    def init_ui(self) -> None:
        """初始化界面"""
        self.setWindowTitle("实时K线图表")

        self.tab: QtWidgets.QTabWidget = QtWidgets.QTabWidget()

        self.tab.setTabsClosable(True)
        self.tab.tabCloseRequested.connect(self.close_tab)

        self.symbol_line: QtWidgets.QLineEdit = QtWidgets.QLineEdit()

        self.button: QtWidgets.QPushButton = QtWidgets.QPushButton("新建图表")
        self.button.clicked.connect(self.new_chart)

        hbox: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        hbox.addWidget(QtWidgets.QLabel("本地代码"))
        hbox.addWidget(self.symbol_line)
        hbox.addWidget(self.button)
        hbox.addStretch()

        vbox: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.tab)

        self.setLayout(vbox)

    def create_chart(self) -> EnhancedChartWidget:
        """创建增强版图表对象"""
        chart: EnhancedChartWidget = EnhancedChartWidget()
        # EnhancedChartWidget已经内置了K线、成交量和各种技术指标
        # 不需要手动添加，直接返回即可
        return chart

    def show(self) -> None:
        """最大化显示"""
        self.showMaximized()

    def close_tab(self, index: int) -> None:
        """关闭标签"""
        vt_symbol: str = self.tab.tabText(index)

        self.tab.removeTab(index)
        self.charts.pop(vt_symbol)

    def new_chart(self) -> None:
        """创建新的图表"""
        # Filter invalid vt_symbol
        vt_symbol: str = self.symbol_line.text()
        if not vt_symbol:
            return

        if vt_symbol in self.charts:
            return

        if "LOCAL" not in vt_symbol:
            contract: ContractData | None = self.main_engine.get_contract(vt_symbol)
            if not contract:
                return

        # Create new chart
        chart: EnhancedChartWidget = self.create_chart()
        self.charts[vt_symbol] = chart

        self.tab.addTab(chart, vt_symbol)

        # Query history data
        end: datetime = datetime.now(ZoneInfo(get_localzone_name()))
        start: datetime = end - timedelta(days=5)

        self.chart_engine.query_history(
            vt_symbol,
            Interval.MINUTE,
            start,
            end
        )

    def register_event(self) -> None:
        """注册事件监听"""
        self.signal_tick.connect(self.process_tick_event)
        self.signal_history.connect(self.process_history_event)
        self.signal_spread.connect(self.process_spread_event)

        self.event_engine.register(EVENT_CHART_HISTORY, self.signal_history.emit)
        self.event_engine.register(EVENT_TICK, self.signal_tick.emit)
        self.event_engine.register(EVENT_SPREAD_DATA, self.signal_spread.emit)

    def process_tick_event(self, event: Event) -> None:
        """处理Tick事件"""
        tick: TickData = event.data
        chart: EnhancedChartWidget | None = self.charts.get(tick.vt_symbol, None)

        if chart:
            # 直接让图表处理tick数据，根据当前周期合成到对应K线
            chart.update_tick(tick)

    def process_history_event(self, event: Event) -> None:
        """处理历史事件"""
        history: list[BarData] = event.data
        if not history:
            return

        bar: BarData = history[0]
        chart: EnhancedChartWidget = self.charts[bar.vt_symbol]

        # 根据合约设置交易时段（用于小时K线聚合）
        trading_session = get_trading_session_by_symbol(bar.symbol, bar.exchange.value)
        chart.trading_session = trading_session

        chart.update_history(history)

        # Subscribe following data update
        contract: ContractData | None = self.main_engine.get_contract(bar.vt_symbol)
        if contract:
            req: SubscribeRequest = SubscribeRequest(
                contract.symbol,
                contract.exchange
            )
            self.main_engine.subscribe(req, contract.gateway_name)

    def process_spread_event(self, event: Event) -> None:
        """处理价差事件"""
        spread_item: SpreadItem = event.data
        tick: TickData = TickData(
            symbol=spread_item.name,
            exchange=Exchange.LOCAL,
            datetime=spread_item.datetime,
            name=spread_item.name,
            last_price=(spread_item.bid_price + spread_item.ask_price) / 2,
            bid_price_1=spread_item.bid_price,
            ask_price_1=spread_item.ask_price,
            bid_volume_1=spread_item.bid_volume,
            ask_volume_1=spread_item.ask_volume,
            gateway_name="SPREAD"
        )

        chart: EnhancedChartWidget | None = self.charts.get(tick.vt_symbol, None)
        if chart:
            # 直接让图表处理tick数据
            chart.update_tick(tick)
