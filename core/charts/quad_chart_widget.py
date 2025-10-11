#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
四图视图显示组件（2x2排列）
支持同时显示四个不同周期的图表，默认启用时间轴同步
"""

from datetime import datetime
from typing import List, Dict, Tuple
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSplitter
from PySide6.QtCore import Qt, Signal
from loguru import logger

from vnpy.trader.object import BarData

from .enhanced_chart_widget import EnhancedChartWidget


class QuadChartTimeAxisSync:
    """四图时间轴同步管理器"""

    def __init__(self,
                 top_left_chart: EnhancedChartWidget,
                 top_right_chart: EnhancedChartWidget,
                 bottom_left_chart: EnhancedChartWidget,
                 bottom_right_chart: EnhancedChartWidget):
        """
        初始化四图时间轴同步管理器

        Args:
            top_left_chart: 左上图表
            top_right_chart: 右上图表
            bottom_left_chart: 左下图表
            bottom_right_chart: 右下图表
        """
        self.charts = {
            'top_left': top_left_chart,
            'top_right': top_right_chart,
            'bottom_left': bottom_left_chart,
            'bottom_right': bottom_right_chart
        }

        self.sync_enabled = True  # 默认启用同步
        self.is_syncing = False  # 防止循环同步

        # 存储时间映射关系
        self.time_maps: Dict[str, Dict[datetime, int]] = {
            'top_left': {},
            'top_right': {},
            'bottom_left': {},
            'bottom_right': {}
        }

        # 连接信号
        self._connect_signals()

    def _connect_signals(self):
        """连接图表信号"""
        for chart_name, chart in self.charts.items():
            plot = chart._plots.get("candle")
            if plot:
                viewbox = plot.getViewBox()
                # 连接X轴范围变化信号
                viewbox.sigXRangeChanged.connect(
                    lambda view, range_, name=chart_name: self._on_x_range_changed(name, range_)
                )

    def build_time_maps(self, bars_dict: Dict[str, List[BarData]]):
        """
        构建时间映射关系

        Args:
            bars_dict: 各图表的K线数据字典
                格式: {'top_left': bars, 'top_right': bars, ...}
        """
        # 清空旧的映射
        for key in self.time_maps:
            self.time_maps[key].clear()

        # 构建各图表时间映射
        for chart_name, bars in bars_dict.items():
            for idx, bar in enumerate(bars):
                self.time_maps[chart_name][bar.datetime] = idx

        logger.debug(f"四图时间映射构建完成: " +
                    ", ".join([f"{k}={len(bars_dict.get(k, []))}根" for k in self.time_maps.keys()]))

    def _on_x_range_changed(self, source_chart: str, range_: Tuple[float, float]):
        """
        某个图表X轴范围变化处理

        Args:
            source_chart: 触发变化的图表名称
            range_: X轴范围 (min_x, max_x)
        """
        if not self.sync_enabled or self.is_syncing:
            return

        self.is_syncing = True
        try:
            self._sync_all_charts(source_chart, range_)
        finally:
            self.is_syncing = False

    def _sync_all_charts(self, source_chart: str, source_range: Tuple[float, float]):
        """
        同步所有图表到源图表的时间范围

        Args:
            source_chart: 源图表名称
            source_range: 源图表的X轴范围
        """
        # 获取源图表数据
        source_chart_widget = self.charts[source_chart]
        source_bars = source_chart_widget._manager.get_all_bars()
        if not source_bars:
            return

        # 边界检查
        source_min_idx = max(0, int(source_range[0]))
        source_max_idx = min(len(source_bars) - 1, int(source_range[1]))

        # 获取源图表的时间范围
        source_start_time = source_bars[source_min_idx].datetime
        source_end_time = source_bars[source_max_idx].datetime

        # 同步其他图表
        for chart_name, chart in self.charts.items():
            if chart_name == source_chart:
                continue

            bars = chart._manager.get_all_bars()
            if not bars:
                continue

            # 找到最接近的起始和结束索引
            start_idx = self._find_nearest_index(bars, source_start_time)
            end_idx = self._find_nearest_index(bars, source_end_time)

            # 更新图表的X轴范围
            plot = chart._plots.get("candle")
            if plot:
                viewbox = plot.getViewBox()
                viewbox.setXRange(start_idx, end_idx, padding=0)

    def _find_nearest_index(self, bars: List[BarData], target_time: datetime) -> int:
        """
        找到最接近目标时间的K线索引

        Args:
            bars: K线数据列表
            target_time: 目标时间

        Returns:
            最接近的索引
        """
        if not bars:
            return 0

        # 二分查找最接近的时间
        left, right = 0, len(bars) - 1

        while left <= right:
            mid = (left + right) // 2
            bar_time = bars[mid].datetime

            if bar_time == target_time:
                return mid
            elif bar_time < target_time:
                left = mid + 1
            else:
                right = mid - 1

        # 返回最接近的索引
        if left >= len(bars):
            return len(bars) - 1
        if right < 0:
            return 0

        # 比较left和right哪个更接近
        left_diff = abs((bars[left].datetime - target_time).total_seconds())
        right_diff = abs((bars[right].datetime - target_time).total_seconds())

        return left if left_diff <= right_diff else right


class QuadChartWidget(QWidget):
    """
    四图视图显示组件（2x2排列）

    特性：
    - 2x2网格布局，可拖拽调整比例
    - 默认四个周期：5分钟、15分钟、1小时、日线
    - 默认启用时间轴同步
    - 使用EnhancedChartWidget原有的左侧周期面板
    """

    # 信号定义
    top_left_period_changed = Signal(str)
    top_right_period_changed = Signal(str)
    bottom_left_period_changed = Signal(str)
    bottom_right_period_changed = Signal(str)

    def __init__(self,
                 top_left_period: str = "5m",
                 top_right_period: str = "15m",
                 bottom_left_period: str = "1h",
                 bottom_right_period: str = "d",
                 parent: QWidget = None):
        """
        初始化四图组件

        Args:
            top_left_period: 左上图表默认周期（默认5分钟）
            top_right_period: 右上图表默认周期（默认15分钟）
            bottom_left_period: 左下图表默认周期（默认1小时）
            bottom_right_period: 右下图表默认周期（默认日线）
            parent: 父组件
        """
        super().__init__(parent)

        self.periods = {
            'top_left': top_left_period,
            'top_right': top_right_period,
            'bottom_left': bottom_left_period,
            'bottom_right': bottom_right_period
        }

        # 创建图表组件
        self.top_left_chart = EnhancedChartWidget()
        self.top_right_chart = EnhancedChartWidget()
        self.bottom_left_chart = EnhancedChartWidget()
        self.bottom_right_chart = EnhancedChartWidget()

        self.charts = {
            'top_left': self.top_left_chart,
            'top_right': self.top_right_chart,
            'bottom_left': self.bottom_left_chart,
            'bottom_right': self.bottom_right_chart
        }

        # 创建同步管理器（默认启用）
        self.sync_manager = QuadChartTimeAxisSync(
            self.top_left_chart,
            self.top_right_chart,
            self.bottom_left_chart,
            self.bottom_right_chart
        )

        # 基础数据
        self.base_minute_bars: List[BarData] = []
        self.current_symbol = ""
        self.current_exchange = None

        # 初始化UI
        self._init_ui()

        # 连接周期切换回调
        self._connect_period_callbacks()

        logger.info(f"四图组件初始化完成: 左上{top_left_period}, 右上{top_right_period}, "
                   f"左下{bottom_left_period}, 右下{bottom_right_period}, 同步已启用")

    def _init_ui(self):
        """初始化UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 垂直分割器（上下分栏）
        v_splitter = QSplitter(Qt.Vertical)
        v_splitter.setHandleWidth(3)
        v_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #444;
            }
            QSplitter::handle:hover {
                background-color: #666;
            }
        """)

        # 上半部分水平分割器（左右分栏）
        top_h_splitter = QSplitter(Qt.Horizontal)
        top_h_splitter.setHandleWidth(3)
        top_h_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #444;
            }
            QSplitter::handle:hover {
                background-color: #666;
            }
        """)
        top_h_splitter.addWidget(self.top_left_chart)
        top_h_splitter.addWidget(self.top_right_chart)
        top_h_splitter.setSizes([500, 500])

        # 下半部分水平分割器（左右分栏）
        bottom_h_splitter = QSplitter(Qt.Horizontal)
        bottom_h_splitter.setHandleWidth(3)
        bottom_h_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #444;
            }
            QSplitter::handle:hover {
                background-color: #666;
            }
        """)
        bottom_h_splitter.addWidget(self.bottom_left_chart)
        bottom_h_splitter.addWidget(self.bottom_right_chart)
        bottom_h_splitter.setSizes([500, 500])

        # 添加到垂直分割器
        v_splitter.addWidget(top_h_splitter)
        v_splitter.addWidget(bottom_h_splitter)
        v_splitter.setSizes([500, 500])

        main_layout.addWidget(v_splitter)

    def _connect_period_callbacks(self):
        """连接周期切换回调"""
        # 左上图表周期切换回调
        self.top_left_chart.on_interval_changed_callback = lambda bars, interval: self._on_period_changed('top_left', bars, interval)  # type: ignore

        # 右上图表周期切换回调
        self.top_right_chart.on_interval_changed_callback = lambda bars, interval: self._on_period_changed('top_right', bars, interval)  # type: ignore

        # 左下图表周期切换回调
        self.bottom_left_chart.on_interval_changed_callback = lambda bars, interval: self._on_period_changed('bottom_left', bars, interval)  # type: ignore

        # 右下图表周期切换回调
        self.bottom_right_chart.on_interval_changed_callback = lambda bars, interval: self._on_period_changed('bottom_right', bars, interval)  # type: ignore

    def _on_period_changed(self, chart_name: str, bars: List[BarData], interval: str):
        """
        图表周期切换回调

        Args:
            chart_name: 图表名称
            bars: 新周期的K线数据
            interval: 新周期
        """
        self.periods[chart_name] = interval
        logger.info(f"{chart_name}图表周期切换: {interval}")

        # 重建时间映射
        bars_dict = {
            name: chart._manager.get_all_bars()
            for name, chart in self.charts.items()
        }

        if all(bars_dict.values()):
            self.sync_manager.build_time_maps(bars_dict)

        # 发射对应的信号
        signal_map = {
            'top_left': self.top_left_period_changed,
            'top_right': self.top_right_period_changed,
            'bottom_left': self.bottom_left_period_changed,
            'bottom_right': self.bottom_right_period_changed
        }
        signal_map[chart_name].emit(interval)

    def update_history(self, bars: List[BarData]):
        """
        更新历史数据

        Args:
            bars: K线数据（建议使用1分钟K线）
        """
        # 保存原始数据
        self.base_minute_bars = bars.copy()

        # 聚合各图表数据
        bars_dict = {}
        for chart_name, period in self.periods.items():
            aggregated_bars = self._aggregate_bars(bars, period)
            self.charts[chart_name].update_history(aggregated_bars)
            bars_dict[chart_name] = aggregated_bars

        # 构建时间映射（同步已默认启用）
        self.sync_manager.build_time_maps(bars_dict)

        logger.info(f"四图数据更新: 基础{len(bars)}根, " +
                   ", ".join([f"{k}={len(v)}根" for k, v in bars_dict.items()]))

    def _aggregate_bars(self, minute_bars: List[BarData], target_period: str) -> List[BarData]:
        """
        聚合K线数据

        Args:
            minute_bars: 1分钟K线数据
            target_period: 目标周期

        Returns:
            聚合后的K线数据
        """
        # 使用第一个图表的聚合方法（EnhancedChartWidget已实现）
        return self.top_left_chart._aggregate_bars(minute_bars, target_period)

    def set_trading_session_by_symbol(self, symbol: str, exchange: str = ""):
        """
        根据品种代码设置交易时段

        Args:
            symbol: 品种代码
            exchange: 交易所代码
        """
        self.current_symbol = symbol
        self.current_exchange = exchange

        # 为所有图表设置交易时段
        for chart in self.charts.values():
            chart.set_trading_session_by_symbol(symbol, exchange)

    def clear_all(self):
        """清空所有数据"""
        for chart in self.charts.values():
            chart.clear_all()
        self.base_minute_bars.clear()
        logger.info("四图数据已清空")

    def set_period(self, chart_name: str, period: str):
        """
        设置指定图表的周期

        Args:
            chart_name: 图表名称 ('top_left', 'top_right', 'bottom_left', 'bottom_right')
            period: 周期字符串（如"15m", "1h"）
        """
        if chart_name not in self.charts:
            logger.warning(f"无效的图表名称: {chart_name}")
            return

        chart = self.charts[chart_name]

        # 触发图表的周期切换
        if self.base_minute_bars:
            aggregated_bars = self._aggregate_bars(self.base_minute_bars, period)
            if hasattr(chart, '_on_interval_changed'):
                chart._on_interval_changed(period, None)  # 触发按钮状态更新
