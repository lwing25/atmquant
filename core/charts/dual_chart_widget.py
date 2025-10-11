#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双图并排显示组件（优化版）
支持同时显示两个不同周期的图表，默认启用时间轴同步
"""

from datetime import datetime
from typing import List, Dict, Tuple
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSplitter
from PySide6.QtCore import Qt, Signal
from loguru import logger

from vnpy.trader.object import BarData

from .enhanced_chart_widget import EnhancedChartWidget


class ChartTimeAxisSync:
    """图表时间轴同步管理器"""

    def __init__(self, left_chart: EnhancedChartWidget, right_chart: EnhancedChartWidget):
        """
        初始化时间轴同步管理器

        Args:
            left_chart: 左侧图表
            right_chart: 右侧图表
        """
        self.left_chart = left_chart
        self.right_chart = right_chart
        self.sync_enabled = True  # 默认启用同步
        self.is_syncing = False  # 防止循环同步

        # 存储时间映射关系
        self.left_time_map: Dict[datetime, int] = {}  # datetime -> index
        self.right_time_map: Dict[datetime, int] = {}  # datetime -> index

        # 连接信号
        self._connect_signals()

    def _connect_signals(self):
        """连接图表信号"""
        # 获取图表的ViewBox
        left_plot = self.left_chart._plots.get("candle")
        right_plot = self.right_chart._plots.get("candle")

        if left_plot and right_plot:
            left_viewbox = left_plot.getViewBox()
            right_viewbox = right_plot.getViewBox()

            # 连接X轴范围变化信号
            left_viewbox.sigXRangeChanged.connect(self._on_left_x_range_changed)
            right_viewbox.sigXRangeChanged.connect(self._on_right_x_range_changed)

    def build_time_maps(self, left_bars: List[BarData], right_bars: List[BarData]):
        """
        构建时间映射关系

        Args:
            left_bars: 左侧图表的K线数据
            right_bars: 右侧图表的K线数据
        """
        # 清空旧的映射
        self.left_time_map.clear()
        self.right_time_map.clear()

        # 构建左侧时间映射
        for idx, bar in enumerate(left_bars):
            self.left_time_map[bar.datetime] = idx

        # 构建右侧时间映射
        for idx, bar in enumerate(right_bars):
            self.right_time_map[bar.datetime] = idx

        logger.debug(f"时间映射构建完成: 左侧{len(left_bars)}根K线, 右侧{len(right_bars)}根K线")

    def _on_left_x_range_changed(self, view, range_):
        """左侧图表X轴范围变化处理"""
        if not self.sync_enabled or self.is_syncing:
            return

        self.is_syncing = True
        try:
            self._sync_right_to_left(range_)
        finally:
            self.is_syncing = False

    def _on_right_x_range_changed(self, view, range_):
        """右侧图表X轴范围变化处理"""
        if not self.sync_enabled or self.is_syncing:
            return

        self.is_syncing = True
        try:
            self._sync_left_to_right(range_)
        finally:
            self.is_syncing = False

    def _sync_right_to_left(self, left_range: Tuple[float, float]):
        """
        将右侧图表同步到左侧

        Args:
            left_range: 左侧图表的X轴范围 (min_x, max_x)
        """
        # 获取左侧显示的时间范围
        left_min_idx = int(left_range[0])
        left_max_idx = int(left_range[1])

        # 获取左侧数据
        left_bars = self.left_chart._manager.get_all_bars()
        if not left_bars:
            return

        # 边界检查
        left_min_idx = max(0, left_min_idx)
        left_max_idx = min(len(left_bars) - 1, left_max_idx)

        # 获取时间范围
        left_start_time = left_bars[left_min_idx].datetime
        left_end_time = left_bars[left_max_idx].datetime

        # 在右侧找到对应的时间索引
        right_bars = self.right_chart._manager.get_all_bars()
        if not right_bars:
            return

        # 找到右侧最接近的起始和结束索引
        right_start_idx = self._find_nearest_index(right_bars, left_start_time)
        right_end_idx = self._find_nearest_index(right_bars, left_end_time)

        # 更新右侧图表的X轴范围
        right_plot = self.right_chart._plots.get("candle")
        if right_plot:
            right_viewbox = right_plot.getViewBox()
            right_viewbox.setXRange(right_start_idx, right_end_idx, padding=0)

    def _sync_left_to_right(self, right_range: Tuple[float, float]):
        """
        将左侧图表同步到右侧

        Args:
            right_range: 右侧图表的X轴范围 (min_x, max_x)
        """
        # 获取右侧显示的时间范围
        right_min_idx = int(right_range[0])
        right_max_idx = int(right_range[1])

        # 获取右侧数据
        right_bars = self.right_chart._manager.get_all_bars()
        if not right_bars:
            return

        # 边界检查
        right_min_idx = max(0, right_min_idx)
        right_max_idx = min(len(right_bars) - 1, right_max_idx)

        # 获取时间范围
        right_start_time = right_bars[right_min_idx].datetime
        right_end_time = right_bars[right_max_idx].datetime

        # 在左侧找到对应的时间索引
        left_bars = self.left_chart._manager.get_all_bars()
        if not left_bars:
            return

        # 找到左侧最接近的起始和结束索引
        left_start_idx = self._find_nearest_index(left_bars, right_start_time)
        left_end_idx = self._find_nearest_index(left_bars, right_end_time)

        # 更新左侧图表的X轴范围
        left_plot = self.left_chart._plots.get("candle")
        if left_plot:
            left_viewbox = left_plot.getViewBox()
            left_viewbox.setXRange(left_start_idx, left_end_idx, padding=0)

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


class DualChartWidget(QWidget):
    """
    双图并排显示组件（优化版）

    特性：
    - 左右分栏布局，可拖拽调整比例
    - 默认左侧15分钟，右侧1小时
    - 默认启用时间轴同步
    - 使用EnhancedChartWidget原有的左侧周期面板
    """

    # 信号定义
    left_period_changed = Signal(str)
    right_period_changed = Signal(str)

    def __init__(self,
                 left_period: str = "15m",
                 right_period: str = "1h",
                 parent: QWidget = None):
        """
        初始化双图组件

        Args:
            left_period: 左侧图表默认周期（默认15分钟）
            right_period: 右侧图表默认周期（默认1小时）
            parent: 父组件
        """
        super().__init__(parent)

        self.left_period = left_period
        self.right_period = right_period

        # 创建图表组件
        self.left_chart = EnhancedChartWidget()
        self.right_chart = EnhancedChartWidget()

        # 创建同步管理器（默认启用）
        self.sync_manager = ChartTimeAxisSync(self.left_chart, self.right_chart)

        # 基础数据
        self.base_minute_bars: List[BarData] = []
        self.current_symbol = ""
        self.current_exchange = None

        # 初始化UI
        self._init_ui()

        # 连接周期切换回调
        self._connect_period_callbacks()

        logger.info(f"双图组件初始化完成: 左侧{left_period}, 右侧{right_period}, 同步已启用")

    def _init_ui(self):
        """初始化UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 图表分割器（左右分栏）
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(3)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #444;
            }
            QSplitter::handle:hover {
                background-color: #666;
            }
        """)

        # 添加左右图表（直接添加，不需要额外的容器）
        splitter.addWidget(self.left_chart)
        splitter.addWidget(self.right_chart)

        # 设置默认比例 1:1
        splitter.setSizes([500, 500])

        main_layout.addWidget(splitter)

    def _connect_period_callbacks(self):
        """连接周期切换回调"""
        # 左侧图表周期切换回调
        # 注意：这里赋值的是可调用对象，运行时类型检查会通过
        self.left_chart.on_interval_changed_callback = self._on_left_interval_changed  # type: ignore

        # 右侧图表周期切换回调
        self.right_chart.on_interval_changed_callback = self._on_right_interval_changed  # type: ignore

    def _on_left_interval_changed(self, bars: List[BarData], interval: str):
        """
        左侧图表周期切换回调

        Args:
            bars: 新周期的K线数据
            interval: 新周期
        """
        self.left_period = interval
        logger.info(f"左侧图表周期切换: {interval}")

        # 重建时间映射
        right_bars = self.right_chart._manager.get_all_bars()
        if right_bars:
            self.sync_manager.build_time_maps(bars, right_bars)

        self.left_period_changed.emit(interval)

    def _on_right_interval_changed(self, bars: List[BarData], interval: str):
        """
        右侧图表周期切换回调

        Args:
            bars: 新周期的K线数据
            interval: 新周期
        """
        self.right_period = interval
        logger.info(f"右侧图表周期切换: {interval}")

        # 重建时间映射
        left_bars = self.left_chart._manager.get_all_bars()
        if left_bars:
            self.sync_manager.build_time_maps(left_bars, bars)

        self.right_period_changed.emit(interval)

    def update_history(self, bars: List[BarData]):
        """
        更新历史数据

        Args:
            bars: K线数据（建议使用1分钟K线）
        """
        # 保存原始数据
        self.base_minute_bars = bars.copy()

        # 聚合左侧数据
        left_bars = self._aggregate_bars(bars, self.left_period)
        self.left_chart.update_history(left_bars)

        # 聚合右侧数据
        right_bars = self._aggregate_bars(bars, self.right_period)
        self.right_chart.update_history(right_bars)

        # 构建时间映射（同步已默认启用）
        self.sync_manager.build_time_maps(left_bars, right_bars)

        logger.info(f"双图数据更新: 基础{len(bars)}根, 左侧{len(left_bars)}根, 右侧{len(right_bars)}根")

    def _aggregate_bars(self, minute_bars: List[BarData], target_period: str) -> List[BarData]:
        """
        聚合K线数据

        Args:
            minute_bars: 1分钟K线数据
            target_period: 目标周期

        Returns:
            聚合后的K线数据
        """
        # 使用左侧图表的聚合方法（EnhancedChartWidget已实现）
        return self.left_chart._aggregate_bars(minute_bars, target_period)

    def set_trading_session_by_symbol(self, symbol: str, exchange: str = ""):
        """
        根据品种代码设置交易时段

        Args:
            symbol: 品种代码
            exchange: 交易所代码
        """
        self.current_symbol = symbol
        self.current_exchange = exchange

        # 为两个图表设置交易时段
        self.left_chart.set_trading_session_by_symbol(symbol, exchange)
        self.right_chart.set_trading_session_by_symbol(symbol, exchange)

    def clear_all(self):
        """清空所有数据"""
        self.left_chart.clear_all()
        self.right_chart.clear_all()
        self.base_minute_bars.clear()
        logger.info("双图数据已清空")

    def set_left_period(self, period: str):
        """
        设置左侧图表周期

        Args:
            period: 周期字符串（如"15m", "1h"）
        """
        # 触发左侧图表的周期切换
        period_map = {
            "1m": "1m",
            "5m": "5m",
            "15m": "15m",
            "1h": "1h",
            "d": "d"
        }

        if period in period_map and hasattr(self.left_chart, '_on_interval_changed'):
            # 直接调用周期切换逻辑
            if self.base_minute_bars:
                aggregated_bars = self._aggregate_bars(self.base_minute_bars, period)
                self.left_chart._on_interval_changed(period, None)  # 触发按钮状态更新

    def set_right_period(self, period: str):
        """
        设置右侧图表周期

        Args:
            period: 周期字符串（如"15m", "1h"）
        """
        # 触发右侧图表的周期切换
        if self.base_minute_bars:
            aggregated_bars = self._aggregate_bars(self.base_minute_bars, period)
            self.right_chart._on_interval_changed(period, None)  # 触发按钮状态更新
