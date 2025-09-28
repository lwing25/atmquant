#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版K线图表对话框
使用EnhancedChartWidget替代原始ChartWidget，提供更丰富的技术指标功能
"""

import pyqtgraph as pg
from typing import List

from vnpy.trader.ui import QtCore, QtWidgets, QtGui
from vnpy.trader.constant import Direction
from vnpy.trader.object import BarData, TradeData
from vnpy.chart import CandleItem, VolumeItem

# 导入增强图表组件
try:
    from core.charts import EnhancedChartWidget
    ENHANCED_AVAILABLE = True
except ImportError:
    from vnpy.chart import ChartWidget
    ENHANCED_AVAILABLE = False
    print("Warning: EnhancedChartWidget not available, falling back to standard ChartWidget")

from ..locale import _


def generate_trade_pairs(trades: List[TradeData]) -> List[dict]:
    """
    Generate trade pairs from trade data.
    From original widget.py implementation.
    """
    long_trades: list = []
    short_trades: list = []
    trade_pairs: list = []

    for trade in trades:
        if trade.direction == Direction.LONG:
            long_trades.append(trade)
        else:
            short_trades.append(trade)

    # Long position trade pairs
    long_position_holding: int = 0
    long_position_price: float = 0

    for trade in long_trades:
        if trade.offset.value == "开仓":
            if long_position_holding == 0:
                long_position_price = trade.price
            else:
                long_position_price = (
                    long_position_price * long_position_holding + trade.price * trade.volume
                ) / (long_position_holding + trade.volume)
            long_position_holding += trade.volume
        else:
            if long_position_holding == 0:
                continue

            close_volume: int = min(trade.volume, long_position_holding)
            long_position_holding -= close_volume

            d: dict = {
                "open_dt": None,
                "open_price": long_position_price,
                "close_dt": trade.datetime,
                "close_price": trade.price,
                "direction": Direction.LONG,
                "volume": close_volume
            }
            trade_pairs.append(d)

    # Short position trade pairs
    short_position_holding: int = 0
    short_position_price: float = 0

    for trade in short_trades:
        if trade.offset.value == "开仓":
            if short_position_holding == 0:
                short_position_price = trade.price
            else:
                short_position_price = (
                    short_position_price * short_position_holding + trade.price * trade.volume
                ) / (short_position_holding + trade.volume)
            short_position_holding += trade.volume
        else:
            if short_position_holding == 0:
                continue

            close_volume = min(trade.volume, short_position_holding)
            short_position_holding -= close_volume

            d = {
                "open_dt": None,
                "open_price": short_position_price,
                "close_dt": trade.datetime,
                "close_price": trade.price,
                "direction": Direction.SHORT,
                "volume": close_volume
            }
            trade_pairs.append(d)

    return trade_pairs


class EnhancedCandleChartDialog(QtWidgets.QDialog):
    """
    增强版K线图表对话框
    使用EnhancedChartWidget提供丰富的技术指标功能
    """

    def __init__(self) -> None:
        """初始化对话框"""
        super().__init__()

        self.updated: bool = False

        self.dt_ix_map: dict = {}
        self.ix_bar_map: dict = {}

        self.high_price = 0
        self.low_price = 0
        self.price_range = 0

        self.items: List = []

        self.init_ui()

    def init_ui(self) -> None:
        """初始化UI界面"""
        self.setWindowTitle(_("回测K线图表(增强版)"))
        self.resize(1600, 900)  # 稍微增大窗口以容纳更多指标

        # 创建增强版图表组件
        if ENHANCED_AVAILABLE:
            self.chart = EnhancedChartWidget()
            # 添加主图和成交量图
            self.chart.add_plot("candle", hide_x_axis=True)
            self.chart.add_plot("volume", maximum_height=200)
            
            # 添加K线和成交量显示
            self.chart.add_item(CandleItem, "candle", "candle")
            self.chart.add_item(VolumeItem, "volume", "volume")
            
            # 添加光标
            self.chart.add_cursor()
            
            # 启用默认指标
            self._setup_default_indicators()
        else:
            # 回退到标准ChartWidget
            from vnpy.chart import ChartWidget
            self.chart = ChartWidget()
            self.chart.add_plot("candle", hide_x_axis=True)
            self.chart.add_plot("volume", maximum_height=200)
            self.chart.add_item(CandleItem, "candle", "candle")
            self.chart.add_item(VolumeItem, "volume", "volume")
            self.chart.add_cursor()

        # 设置布局 - 简化布局，只显示图表
        vbox: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.chart)
        self.setLayout(vbox)

    def _setup_default_indicators(self) -> None:
        """设置默认技术指标"""
        if not ENHANCED_AVAILABLE:
            return
            
        try:
            # 启用一些基础的技术指标
            # 由于EnhancedChartWidget会在数据加载后自动处理，这里不需要做特殊设置
            # 但可以在数据更新后手动添加一些默认指标
            pass
        except Exception as e:
            print(f"设置默认指标时出错: {e}")

    def _add_default_indicators_after_data_load(self) -> None:
        """在数据加载后添加默认指标"""
        if not ENHANCED_AVAILABLE or not hasattr(self.chart, 'add_indicator'):
            return
            
        try:
            # 如果EnhancedChartWidget有add_indicator方法，使用它
            if hasattr(self.chart, 'add_indicator'):
                # 添加布林带到主图
                self.chart.add_indicator('boll', 'candle')
                # 添加RSI到附图
                self.chart.add_indicator('rsi', 'rsi')
                # 添加MACD到附图
                self.chart.add_indicator('macd', 'macd')
            else:
                # 手动添加指标
                from core.charts import BollItem, RsiItem
                
                # 添加布林带
                boll_item = BollItem(self.chart._manager)
                if hasattr(self.chart, 'get_plot'):
                    candle_plot = self.chart.get_plot("candle")
                    if candle_plot:
                        candle_plot.addItem(boll_item)
                
                # 添加RSI附图
                if "rsi" not in getattr(self.chart, '_plots', {}):
                    self.chart.add_plot("rsi", maximum_height=150)
                rsi_item = RsiItem(self.chart._manager)
                rsi_plot = self.chart.get_plot("rsi")
                if rsi_plot:
                    rsi_plot.addItem(rsi_item)
                
        except Exception as e:
            print(f"添加默认指标时出错: {e}")


    def update_history(self, history: List[BarData]) -> None:
        """更新历史数据"""
        self.updated = True
        self.chart.update_history(history)

        for ix, bar in enumerate(history):
            self.ix_bar_map[ix] = bar
            self.dt_ix_map[bar.datetime] = ix

            if not self.high_price:
                self.high_price = bar.high_price
                self.low_price = bar.low_price
            else:
                self.high_price = max(self.high_price, bar.high_price)
                self.low_price = min(self.low_price, bar.low_price)

        self.price_range = self.high_price - self.low_price
        
        # 数据加载完成后，添加默认指标
        self._add_default_indicators_after_data_load()

    def update_trades(self, trades: List[TradeData]) -> None:
        """更新交易数据并绘制交易信号"""
        trade_pairs: list = generate_trade_pairs(trades)

        candle_plot: pg.PlotItem = self.chart.get_plot("candle")

        scatter_data: list = []

        y_adjustment: float = self.price_range * 0.001

        for d in trade_pairs:
            if d["open_dt"] not in self.dt_ix_map or d["close_dt"] not in self.dt_ix_map:
                continue
                
            open_ix = self.dt_ix_map[d["open_dt"]]
            close_ix = self.dt_ix_map[d["close_dt"]]
            open_price = d["open_price"]
            close_price = d["close_price"]

            # 交易连线
            x: list = [open_ix, close_ix]
            y: list = [open_price, close_price]

            if d["direction"] == Direction.LONG and close_price >= open_price:
                color: str = "r"
            elif d["direction"] == Direction.SHORT and close_price <= open_price:
                color = "r"
            else:
                color = "g"

            pen: QtGui.QPen = pg.mkPen(color, width=1.5, style=QtCore.Qt.PenStyle.DashLine)
            item: pg.PlotCurveItem = pg.PlotCurveItem(x, y, pen=pen)

            self.items.append(item)
            candle_plot.addItem(item)

            # 交易点标记
            if open_ix in self.ix_bar_map and close_ix in self.ix_bar_map:
                open_bar: BarData = self.ix_bar_map[open_ix]
                close_bar: BarData = self.ix_bar_map[close_ix]

                if d["direction"] == Direction.LONG:
                    scatter_color: str = "yellow"
                    open_symbol: str = "t1"
                    close_symbol: str = "t"
                    open_side: int = 1
                    close_side: int = -1
                    open_y: float = open_bar.low_price
                    close_y: float = close_bar.high_price
                else:
                    scatter_color = "magenta"
                    open_symbol = "t"
                    close_symbol = "t1"
                    open_side = -1
                    close_side = 1
                    open_y = open_bar.high_price
                    close_y = close_bar.low_price

                pen = pg.mkPen(QtGui.QColor(scatter_color))
                brush: QtGui.QBrush = pg.mkBrush(QtGui.QColor(scatter_color))
                size: int = 10

                open_scatter: dict = {
                    "pos": (open_ix, open_y - open_side * y_adjustment),
                    "size": size,
                    "pen": pen,
                    "brush": brush,
                    "symbol": open_symbol
                }

                close_scatter: dict = {
                    "pos": (close_ix, close_y - close_side * y_adjustment),
                    "size": size,
                    "pen": pen,
                    "brush": brush,
                    "symbol": close_symbol
                }

                scatter_data.append(open_scatter)
                scatter_data.append(close_scatter)

                # 交易量标签
                volume = d["volume"]
                text_color: QtGui.QColor = QtGui.QColor(scatter_color)
                open_text: pg.TextItem = pg.TextItem(f"[{volume}]", color=text_color, anchor=(0.5, 0.5))
                close_text: pg.TextItem = pg.TextItem(f"[{volume}]", color=text_color, anchor=(0.5, 0.5))

                open_text.setPos(open_ix, open_y - open_side * y_adjustment * 3)
                close_text.setPos(close_ix, close_y - close_side * y_adjustment * 3)

                self.items.append(open_text)
                self.items.append(close_text)

                candle_plot.addItem(open_text)
                candle_plot.addItem(close_text)

        if scatter_data:
            trade_scatter: pg.ScatterPlotItem = pg.ScatterPlotItem(scatter_data)
            self.items.append(trade_scatter)
            candle_plot.addItem(trade_scatter)

    def clear_data(self) -> None:
        """清除所有数据"""
        self.updated = False

        candle_plot: pg.PlotItem = self.chart.get_plot("candle")
        for item in self.items:
            candle_plot.removeItem(item)
        self.items.clear()

        self.chart.clear_all()

        self.dt_ix_map.clear()
        self.ix_bar_map.clear()

    def is_updated(self) -> bool:
        """检查是否已更新数据"""
        return self.updated


# 为了向后兼容，创建一个别名
CandleChartDialog = EnhancedCandleChartDialog
