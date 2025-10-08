#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多周期图表容器
管理多个EnhancedChartWidget实例的容器组件
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
                               QMessageBox, QProgressBar, QLabel, QFrame)
from PySide6.QtCore import Qt, Signal, QTimer, QThread, QMutex
from PySide6.QtGui import QFont, QPalette, QColor
from loguru import logger

from core.charts.enhanced_chart_widget import EnhancedChartWidget
from core.charts.time_period_selector import TimePeriodSelector
from core.charts.chart_sync_manager import ChartSyncManager
from core.charts.multi_chart_layout import MultiChartLayout, LayoutConfig
from core.charts.chart_view_modes import ViewMode
from core.charts.time_period import TimePeriod
from core.charts.time_range import TimeRange
from core.data.period_data_loader import PeriodDataLoader
from core.data.data_preloader import DataPreloader
from core.data.data_system_manager import get_data_system_manager
from core.data.kline_data import KLineData
from vnpy.trader.constant import Interval, Exchange
from vnpy.trader.object import BarData


@dataclass
class ChartConfig:
    """图表配置类"""
    chart_id: str
    period_id: str
    symbol: str
    visible: bool = True
    auto_update: bool = True
    sync_enabled: bool = True


@dataclass
class ContainerState:
    """容器状态类"""
    current_symbol: str = ""
    current_periods: List[str] = field(default_factory=list)
    view_mode: ViewMode = ViewMode.SINGLE
    sync_enabled: bool = False
    data_loading: bool = False
    last_update: Optional[datetime] = None


class DataLoadingThread(QThread):
    """数据加载线程"""
    
    data_loaded = Signal(str, str, list)  # symbol, period_id, data
    loading_finished = Signal()
    loading_error = Signal(str, str)  # error_type, error_message
    
    def __init__(self, data_system_manager, symbol: str, 
                 periods: List[str], start_time: datetime, end_time: datetime):
        """
        初始化数据加载线程
        
        Args:
            data_system_manager: 数据系统管理器
            symbol: 合约代码
            periods: 周期列表
            start_time: 开始时间
            end_time: 结束时间
        """
        super().__init__()
        self.data_system_manager = data_system_manager
        self.symbol = symbol
        self.periods = periods
        self.start_time = start_time
        self.end_time = end_time
        self.is_cancelled = False
    
    def run(self):
        """运行数据加载"""
        try:
            for period_id in self.periods:
                if self.is_cancelled:
                    break
                
                # 使用数据系统管理器加载数据
                data = self.data_system_manager.get_kline_data(
                    symbol=self.symbol,
                    period_id=period_id,
                    start_time=self.start_time,
                    end_time=self.end_time,
                    use_cache=True
                )
                
                if not self.is_cancelled:
                    self.data_loaded.emit(self.symbol, period_id, data)
            
            if not self.is_cancelled:
                self.loading_finished.emit()
                
        except Exception as e:
            if not self.is_cancelled:
                self.loading_error.emit("DataLoadError", str(e))
                logger.error(f"数据加载失败: {e}")
    
    def cancel(self):
        """取消加载"""
        self.is_cancelled = True


class MultiChartContainer(QWidget):
    """
    多周期图表容器
    
    管理多个EnhancedChartWidget实例，提供多周期图表显示功能
    """
    
    # 信号定义
    chart_created = Signal(str)  # 图表创建信号
    chart_removed = Signal(str)  # 图表移除信号
    period_changed = Signal(str)  # 周期切换信号
    view_mode_changed = Signal(str)  # 视图模式切换信号
    data_loaded = Signal(str, str)  # 数据加载完成信号 (symbol, period_id)
    sync_state_changed = Signal(bool)  # 同步状态变化信号
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        初始化多周期图表容器
        
        Args:
            parent: 父组件
        """
        super().__init__(parent)
        
        # 基本属性
        self.container_id = f"container_{int(datetime.now().timestamp())}"
        self.chart_widgets: Dict[str, EnhancedChartWidget] = {}
        self.chart_configs: Dict[str, ChartConfig] = {}
        self.state = ContainerState()
        
        # 组件
        self.period_selector: Optional[TimePeriodSelector] = None
        self.sync_manager: Optional[ChartSyncManager] = None
        self.layout_manager: Optional[MultiChartLayout] = None
        self.data_system_manager = get_data_system_manager()
        
        # 数据加载线程
        self.loading_thread: Optional[DataLoadingThread] = None
        self.loading_mutex = QMutex()
        
        # 初始化UI
        self._init_ui()
        self._setup_connections()
        self._initialize_components()
        
        logger.info(f"多周期图表容器初始化: {self.container_id}")
    
    def _init_ui(self):
        """初始化用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # 状态栏
        self._create_status_bar(main_layout)
        
        # 图表区域
        self._create_chart_area(main_layout)
        
        # 进度条
        self._create_progress_bar(main_layout)
    
    def _create_status_bar(self, parent_layout: QVBoxLayout):
        """创建状态栏"""
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.StyledPanel)
        status_frame.setMaximumHeight(30)
        
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(5, 2, 5, 2)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setFont(QFont("Microsoft YaHei", 8))
        status_layout.addWidget(self.status_label)
        
        # 分隔符
        status_layout.addStretch()
        
        # 同步状态标签
        self.sync_status_label = QLabel("同步: 关闭")
        self.sync_status_label.setFont(QFont("Microsoft YaHei", 8))
        self.sync_status_label.setStyleSheet("color: #666;")
        status_layout.addWidget(self.sync_status_label)
        
        parent_layout.addWidget(status_frame)
    
    def _create_chart_area(self, parent_layout: QVBoxLayout):
        """创建图表区域"""
        self.chart_area = QWidget()
        self.chart_area.setMinimumSize(800, 600)
        parent_layout.addWidget(self.chart_area)
    
    def _create_progress_bar(self, parent_layout: QVBoxLayout):
        """创建进度条"""
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumHeight(20)
        parent_layout.addWidget(self.progress_bar)
    
    def _setup_connections(self):
        """设置信号连接"""
        # 定时器用于状态更新
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(1000)  # 每秒更新一次
    
    def _initialize_components(self):
        """初始化组件"""
        # 创建布局管理器
        layout_config = LayoutConfig(
            view_mode=ViewMode.SINGLE,
            chart_spacing=5,
            margin=5,
            auto_resize=True,
            preserve_aspect_ratio=True
        )
        self.layout_manager = MultiChartLayout(self.chart_area, layout_config)
        self.layout_manager.initialize_layout()
        
        # 创建同步管理器
        self.sync_manager = ChartSyncManager(self)
        
        # 数据系统管理器已在初始化时创建
        
        logger.info("组件初始化完成")
    
    def set_period_selector(self, selector: TimePeriodSelector):
        """
        设置时间周期选择器
        
        Args:
            selector: 时间周期选择器
        """
        self.period_selector = selector
        
        # 连接信号
        if self.period_selector:
            self.period_selector.period_changed.connect(self._on_period_changed)
            self.period_selector.view_mode_changed.connect(self._on_view_mode_changed)
        
        logger.info("设置时间周期选择器")
    
    def create_chart(self, period_id: str, symbol: str) -> str:
        """
        创建图表
        
        Args:
            period_id: 周期ID
            symbol: 合约代码
            
        Returns:
            str: 图表ID
        """
        chart_id = f"chart_{period_id}_{symbol}_{int(datetime.now().timestamp())}"
        
        # 创建图表组件
        chart_widget = EnhancedChartWidget()
        chart_widget.setObjectName(chart_id)
        
        # 创建图表配置
        chart_config = ChartConfig(
            chart_id=chart_id,
            period_id=period_id,
            symbol=symbol,
            visible=True,
            auto_update=True,
            sync_enabled=True
        )
        
        # 存储图表信息
        self.chart_widgets[chart_id] = chart_widget
        self.chart_configs[chart_id] = chart_config
        
        # 添加到布局
        self.layout_manager.add_chart(chart_id, chart_widget)
        
        # 添加到同步组
        if self.sync_manager:
            self.sync_manager.add_chart(chart_id)
        
        # 发送创建信号
        self.chart_created.emit(chart_id)
        
        logger.info(f"创建图表: {chart_id}")
        return chart_id
    
    def remove_chart(self, chart_id: str):
        """
        移除图表
        
        Args:
            chart_id: 图表ID
        """
        if chart_id not in self.chart_widgets:
            logger.warning(f"图表 {chart_id} 不存在")
            return
        
        # 从同步组移除
        if self.sync_manager:
            self.sync_manager.remove_chart(chart_id)
        
        # 从布局移除
        self.layout_manager.remove_chart(chart_id)
        
        # 清理图表组件
        chart_widget = self.chart_widgets[chart_id]
        chart_widget.deleteLater()
        
        # 清理数据
        del self.chart_widgets[chart_id]
        del self.chart_configs[chart_id]
        
        # 发送移除信号
        self.chart_removed.emit(chart_id)
        
        logger.info(f"移除图表: {chart_id}")
    
    def switch_period(self, period_id: str):
        """
        切换周期
        
        Args:
            period_id: 周期ID
        """
        if self.state.view_mode == ViewMode.SINGLE:
            # 单图模式：替换当前图表
            self._switch_single_period(period_id)
        else:
            # 多图模式：添加到当前视图
            self._add_period_to_view(period_id)
        
        self.state.current_periods = [period_id] if self.state.view_mode == ViewMode.SINGLE else self.state.current_periods
        
        # 发送周期切换信号
        self.period_changed.emit(period_id)
        
        logger.info(f"切换周期: {period_id}")
    
    def set_view_mode(self, view_mode: ViewMode):
        """
        设置视图模式
        
        Args:
            view_mode: 视图模式
        """
        if self.state.view_mode == view_mode:
            return
        
        self.state.view_mode = view_mode
        
        # 更新布局管理器
        if self.layout_manager:
            self.layout_manager.set_view_mode(view_mode)
        
        # 根据视图模式调整图表
        self._adjust_charts_for_view_mode()
        
        # 发送视图模式切换信号
        self.view_mode_changed.emit(view_mode.value)
        
        logger.info(f"设置视图模式: {view_mode}")
    
    def load_data(self, symbol: str, start_time: datetime, end_time: datetime):
        """
        加载数据
        
        Args:
            symbol: 合约代码
            start_time: 开始时间
            end_time: 结束时间
        """
        if self.state.data_loading:
            logger.warning("数据正在加载中，请稍候")
            return
        
        self.state.current_symbol = symbol
        self.state.data_loading = True
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 不确定进度
        self._update_status("正在加载数据...")
        
        # 获取需要加载的周期
        periods_to_load = self._get_periods_to_load()
        
        if not periods_to_load:
            self._finish_data_loading()
            return
        
        # 启动数据加载线程
        self._start_data_loading(symbol, periods_to_load, start_time, end_time)
        
        logger.info(f"开始加载数据: {symbol}, 周期: {periods_to_load}")
    
    def enable_sync(self, enabled: bool):
        """
        启用/禁用同步
        
        Args:
            enabled: 是否启用
        """
        self.state.sync_enabled = enabled
        
        if self.sync_manager:
            if enabled:
                # 启用同步
                self.sync_manager.set_sync_type("intelligent")
                # 添加所有图表到同步组
                for chart_id in self.chart_widgets.keys():
                    self.sync_manager.add_chart(chart_id)
            else:
                # 禁用同步
                self.sync_manager.stop_sync()
        
        # 更新同步状态显示
        self.sync_status_label.setText(f"同步: {'开启' if enabled else '关闭'}")
        self.sync_status_label.setStyleSheet(
            f"color: {'#0078d4' if enabled else '#666'};"
        )
        
        # 发送同步状态变化信号
        self.sync_state_changed.emit(enabled)
        
        logger.info(f"同步状态: {'开启' if enabled else '关闭'}")
    
    def sync_charts(self, time_range: Optional[TimeRange] = None):
        """
        同步图表
        
        Args:
            time_range: 时间范围（可选）
        """
        if not self.state.sync_enabled or not self.sync_manager:
            return
        
        try:
            if time_range:
                # 同步指定时间范围
                self.sync_manager.sync_time_range(time_range)
            else:
                # 同步当前时间范围
                current_time = datetime.now()
                default_range = TimeRange(
                    start_time=current_time - timedelta(days=30),
                    end_time=current_time
                )
                self.sync_manager.sync_time_range(default_range)
            
            logger.info("图表同步完成")
            
        except Exception as e:
            logger.error(f"图表同步失败: {e}")
    
    def get_sync_status(self) -> Dict[str, Any]:
        """
        获取同步状态
        
        Returns:
            Dict[str, Any]: 同步状态信息
        """
        if not self.sync_manager:
            return {"enabled": False, "error": "同步管理器未初始化"}
        
        return {
            "enabled": self.state.sync_enabled,
            "is_syncing": self.sync_manager.is_syncing,
            "chart_count": len(self.sync_manager.chart_ids),
            "sync_stats": self.sync_manager.get_sync_stats()
        }
    
    def get_current_period(self) -> Optional[str]:
        """
        获取当前周期
        
        Returns:
            Optional[str]: 当前周期ID
        """
        if self.state.current_periods:
            return self.state.current_periods[0]
        return None
    
    def get_current_symbol(self) -> str:
        """
        获取当前合约代码
        
        Returns:
            str: 当前合约代码
        """
        return self.state.current_symbol
    
    def get_chart_count(self) -> int:
        """
        获取图表数量
        
        Returns:
            int: 图表数量
        """
        return len(self.chart_widgets)
    
    def get_visible_chart_count(self) -> int:
        """
        获取可见图表数量
        
        Returns:
            int: 可见图表数量
        """
        return len([config for config in self.chart_configs.values() if config.visible])
    
    def _switch_single_period(self, period_id: str):
        """切换单图周期"""
        # 清空当前图表
        self._clear_all_charts()
        
        # 创建新图表
        if self.state.current_symbol:
            self.create_chart(period_id, self.state.current_symbol)
    
    def _add_period_to_view(self, period_id: str):
        """添加周期到视图"""
        max_charts = self.state.view_mode.get_max_charts()
        
        # 检查是否超过最大图表数量
        if len(self.chart_widgets) >= max_charts:
            # 移除最旧的图表
            oldest_chart_id = min(self.chart_widgets.keys())
            self.remove_chart(oldest_chart_id)
        
        # 创建新图表
        if self.state.current_symbol:
            self.create_chart(period_id, self.state.current_symbol)
    
    def _adjust_charts_for_view_mode(self):
        """根据视图模式调整图表"""
        max_charts = self.state.view_mode.get_max_charts()
        
        # 如果当前图表数量超过限制，移除多余的图表
        while len(self.chart_widgets) > max_charts:
            oldest_chart_id = min(self.chart_widgets.keys())
            self.remove_chart(oldest_chart_id)
    
    def _get_periods_to_load(self) -> List[str]:
        """获取需要加载的周期"""
        if self.state.view_mode == ViewMode.SINGLE:
            # 单图模式：加载当前选中的周期
            current_period = self.get_current_period()
            return [current_period] if current_period else []
        else:
            # 多图模式：加载所有图表的周期
            return list(set(config.period_id for config in self.chart_configs.values()))
    
    def _start_data_loading(self, symbol: str, periods: List[str], 
                           start_time: datetime, end_time: datetime):
        """启动数据加载"""
        if self.loading_thread and self.loading_thread.isRunning():
            self.loading_thread.cancel()
            self.loading_thread.wait()
        
        self.loading_thread = DataLoadingThread(
            self.data_system_manager, symbol, periods, start_time, end_time
        )
        
        # 连接信号
        self.loading_thread.data_loaded.connect(self._on_data_loaded)
        self.loading_thread.loading_finished.connect(self._on_loading_finished)
        self.loading_thread.loading_error.connect(self._on_loading_error)
        
        # 启动线程
        self.loading_thread.start()
    
    def _on_data_loaded(self, symbol: str, period_id: str, data: List):
        """数据加载完成处理"""
        # 找到对应的图表
        chart_id = None
        for cid, config in self.chart_configs.items():
            if config.period_id == period_id and config.symbol == symbol:
                chart_id = cid
                break
        
        if chart_id and chart_id in self.chart_widgets:
            # 更新图表数据
            chart_widget = self.chart_widgets[chart_id]
            
            # 将KLineData转换为BarData
            bar_data = self._convert_kline_to_bar_data(data, symbol)
            
            # 调用图表组件的数据更新方法
            chart_widget.update_history(bar_data)
            
            # 发送数据加载完成信号
            self.data_loaded.emit(symbol, period_id)
        
        logger.info(f"数据加载完成: {symbol}, {period_id}, {len(data)} 条")
    
    def _on_loading_finished(self):
        """加载完成处理"""
        self._finish_data_loading()
        logger.info("所有数据加载完成")
    
    def _on_loading_error(self, error_type: str, error_message: str):
        """加载错误处理"""
        self._finish_data_loading()
        self._update_status(f"数据加载失败: {error_message}")
        logger.error(f"数据加载错误: {error_type} - {error_message}")
    
    def _finish_data_loading(self):
        """完成数据加载"""
        self.state.data_loading = False
        self.state.last_update = datetime.now()
        
        # 隐藏进度条
        self.progress_bar.setVisible(False)
        
        # 更新状态
        self._update_status("数据加载完成")
    
    def _on_period_changed(self, period_id: str):
        """周期切换处理"""
        self.switch_period(period_id)
    
    def _on_view_mode_changed(self, view_mode_str: str):
        """视图模式切换处理"""
        try:
            view_mode = ViewMode(view_mode_str)
            self.set_view_mode(view_mode)
        except ValueError:
            logger.error(f"无效的视图模式: {view_mode_str}")
    
    def _convert_kline_to_bar_data(self, kline_data: List[KLineData], symbol: str) -> List[BarData]:
        """
        将KLineData转换为BarData
        
        Args:
            kline_data: K线数据列表
            symbol: 合约代码
            
        Returns:
            List[BarData]: BarData列表
        """
        bar_data = []
        
        for kline in kline_data:
            try:
                bar = BarData(
                    symbol=symbol,
                    exchange=Exchange.LOCAL,  # 使用本地交易所
                    datetime=kline.datetime,
                    interval=Interval.MINUTE,  # 默认使用分钟间隔
                    volume=kline.volume,
                    turnover=kline.turnover,
                    open_price=kline.open_price,
                    high_price=kline.high_price,
                    low_price=kline.low_price,
                    close_price=kline.close_price,
                    gateway_name="multi_chart"
                )
                bar_data.append(bar)
            except Exception as e:
                logger.warning(f"转换K线数据失败: {kline}, 错误: {e}")
                continue
        
        return bar_data
    
    def _clear_all_charts(self):
        """清空所有图表"""
        chart_ids = list(self.chart_widgets.keys())
        for chart_id in chart_ids:
            self.remove_chart(chart_id)
    
    def _update_status(self, message: str = None):
        """更新状态显示"""
        if message:
            self.status_label.setText(message)
        else:
            # 自动状态更新
            if self.state.data_loading:
                self.status_label.setText("正在加载数据...")
            elif self.chart_widgets:
                chart_count = len(self.chart_widgets)
                visible_count = self.get_visible_chart_count()
                self.status_label.setText(f"图表: {visible_count}/{chart_count}")
            else:
                self.status_label.setText("就绪")
    
    def cleanup(self):
        """清理资源"""
        # 停止数据加载
        if self.loading_thread and self.loading_thread.isRunning():
            self.loading_thread.cancel()
            self.loading_thread.wait()
        
        # 清理同步管理器
        if self.sync_manager:
            self.sync_manager.cleanup()
        
        # 清理布局管理器
        if self.layout_manager:
            self.layout_manager.cleanup()
        
        # 清理图表组件
        self._clear_all_charts()
        
        # 清理数据
        self.chart_widgets.clear()
        self.chart_configs.clear()
        
        logger.info("多周期图表容器清理完成")
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"MultiChartContainer(id={self.container_id}, charts={len(self.chart_widgets)})"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return (f"MultiChartContainer(container_id='{self.container_id}', "
                f"chart_count={len(self.chart_widgets)}, "
                f"view_mode={self.state.view_mode}, "
                f"sync_enabled={self.state.sync_enabled})")


# 风险提示
"""
多周期图表容器风险提示：

1. 容器管理是核心功能，需要仔细处理组件生命周期
2. 数据加载线程需要正确管理，防止资源泄漏
3. 同步功能确保多图表协调一致
4. 内存管理防止图表组件泄漏
5. 状态管理确保界面响应性

投资有风险，容器管理确保系统稳定性！
"""
