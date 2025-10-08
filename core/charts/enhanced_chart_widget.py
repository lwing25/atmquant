#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版K线图表组件
继承自vnpy的ChartWidget，提供丰富的技术指标和交互功能
"""

from datetime import datetime, time
from typing import List, Tuple, Dict, Optional, Union, Any
from abc import ABC, abstractmethod
from functools import partial
import math

import numpy as np
import pyqtgraph as pg
import talib

from vnpy.trader.ui import QtCore, QtGui, QtWidgets
from vnpy.trader.database import get_database
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import BarData

from vnpy.chart import ChartWidget, VolumeItem, CandleItem
from vnpy.chart.item import ChartItem
from vnpy.chart.manager import BarManager
from vnpy.chart.base import NORMAL_FONT
from vnpy.chart.axis import DatetimeAxis
from vnpy.chart.widget import ChartCursor

from .boll_item import BollItem
from .multi_sma_item import MultiSmaItem
from .multi_ema_item import MultiEmaItem
from .rsi_item import RsiItem
from .macd_item import Macd3Item
from .dmi_item import DmiItem
from .indicator_base import ConfigurableIndicator


class ExtendableViewBox(pg.ViewBox):
    """
    增强版ViewBox，支持在最右边拖拽延伸x轴，在顶部/底部拖拽延伸y轴
    """
    def __init__(self, chart_widget, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chart_widget = chart_widget
        self._is_dragging_right = False
        self._is_dragging_top = False
        self._is_dragging_bottom = False
        self._drag_start_pos = None
        self._original_y_range = None

    def mousePressEvent(self, ev):
        """重写鼠标按下事件"""
        # 在Mac上，支持Command键和Control键
        is_ctrl_pressed = (
            ev.modifiers() == QtCore.Qt.ControlModifier or
            ev.modifiers() == QtCore.Qt.MetaModifier  # Mac上的Command键
        )

        if ev.button() == QtCore.Qt.LeftButton:
            # 检查是否按下了CTRL/CMD键，如果是，直接传递给父类处理，不拦截
            if is_ctrl_pressed:
                super().mousePressEvent(ev)
                return

            pos = self.mapSceneToView(ev.scenePos())
            x_pos = pos.x()
            y_pos = pos.y()

            # 获取当前视图范围
            view_range = self.viewRange()
            x_range = view_range[0]
            y_range = view_range[1]

            # 检查是否在数据范围的右边（X轴延伸）
            data_count = self.chart_widget._manager.get_count()
            if x_pos > data_count - 1:
                self._is_dragging_right = True
                self._drag_start_pos = x_pos
                ev.accept()
                return

            # 检查是否在Y轴区域
            y_range_height = y_range[1] - y_range[0]
            top_threshold = y_range[1] - y_range_height * 0.1  # 顶部10%区域
            bottom_threshold = y_range[0] + y_range_height * 0.1  # 底部10%区域

            # 检查是否在Y轴顶部区域（向下拖拽延伸上边界）
            if y_pos > top_threshold:
                self._is_dragging_top = True
                self._drag_start_pos = y_pos
                self._original_y_range = y_range
                ev.accept()
                return

            # 检查是否在Y轴底部区域（向上拖拽延伸下边界）
            elif y_pos < bottom_threshold:
                self._is_dragging_bottom = True
                self._drag_start_pos = y_pos
                self._original_y_range = y_range
                ev.accept()
                return

        # 调用父类的默认处理
        super().mousePressEvent(ev)

    def mouseMoveEvent(self, ev):
        """重写鼠标移动事件"""
        if self._is_dragging_right and self._drag_start_pos is not None:
            # X轴延伸逻辑
            pos = self.mapSceneToView(ev.scenePos())
            x_pos = pos.x()

            # 计算拖拽距离
            drag_distance = x_pos - self._drag_start_pos
            data_count = self.chart_widget._manager.get_count()

            # 更新右边界，允许延伸到数据范围之外
            new_right_ix = data_count - 1 + max(0, drag_distance)

            # 确保不会缩小到数据范围内
            if new_right_ix >= data_count - 1:
                self.chart_widget._right_ix = int(new_right_ix)
                self.chart_widget._update_x_range()

            ev.accept()
            return

        elif self._is_dragging_top and self._drag_start_pos is not None:
            # Y轴上边界延伸逻辑
            pos = self.mapSceneToView(ev.scenePos())
            y_pos = pos.y()

            # 计算拖拽距离
            drag_distance = y_pos - self._drag_start_pos

            # 计算新的Y轴范围
            original_height = self._original_y_range[1] - self._original_y_range[0]

            # 根据拖拽方向调整上边界
            if drag_distance > 0:  # 向下拖拽，扩展上边界
                extend_ratio = drag_distance / original_height
                extend_ratio = min(extend_ratio, 3.0)  # 最多延伸300%
                new_top = self._original_y_range[1] + original_height * extend_ratio
                new_bottom = self._original_y_range[0]
            else:  # 向上拖拽，收缩上边界
                shrink_ratio = abs(drag_distance) / original_height
                shrink_ratio = min(shrink_ratio, 0.8)  # 最多收缩80%
                new_top = self._original_y_range[1] - original_height * shrink_ratio
                new_bottom = self._original_y_range[0]

                # 确保上边界不会低于下边界
                if new_top <= new_bottom:
                    new_top = new_bottom + original_height * 0.1

            # 设置新的Y轴范围
            self.setYRange(new_bottom, new_top, padding=0)

            ev.accept()
            return

        elif self._is_dragging_bottom and self._drag_start_pos is not None:
            # Y轴下边界延伸逻辑
            pos = self.mapSceneToView(ev.scenePos())
            y_pos = pos.y()

            # 计算拖拽距离
            drag_distance = y_pos - self._drag_start_pos

            # 计算新的Y轴范围
            original_height = self._original_y_range[1] - self._original_y_range[0]

            # 根据拖拽方向调整下边界
            if drag_distance < 0:  # 向上拖拽，扩展下边界
                extend_ratio = abs(drag_distance) / original_height
                extend_ratio = min(extend_ratio, 3.0)  # 最多延伸300%
                new_top = self._original_y_range[1]
                new_bottom = self._original_y_range[0] - original_height * extend_ratio
            else:  # 向下拖拽，收缩下边界
                shrink_ratio = drag_distance / original_height
                shrink_ratio = min(shrink_ratio, 0.8)  # 最多收缩80%
                new_top = self._original_y_range[1]
                new_bottom = self._original_y_range[0] + original_height * shrink_ratio

                # 确保下边界不会高于上边界
                if new_bottom >= new_top:
                    new_bottom = new_top - original_height * 0.1

            # 设置新的Y轴范围
            self.setYRange(new_bottom, new_top, padding=0)

            ev.accept()
            return

        # 调用父类的默认处理
        super().mouseMoveEvent(ev)

    def mouseReleaseEvent(self, ev):
        """重写鼠标释放事件"""
        if self._is_dragging_right:
            self._is_dragging_right = False
            self._drag_start_pos = None
            ev.accept()
            return

        elif self._is_dragging_top:
            self._is_dragging_top = False
            self._drag_start_pos = None
            self._original_y_range = None
            ev.accept()
            return

        elif self._is_dragging_bottom:
            self._is_dragging_bottom = False
            self._drag_start_pos = None
            self._original_y_range = None
            ev.accept()
            return

        # 调用父类的默认处理
        super().mouseReleaseEvent(ev)

    def mouseDoubleClickEvent(self, ev):
        """重写鼠标双击事件，双击顶部或底部区域重置Y轴范围"""
        if ev.button() == QtCore.Qt.LeftButton:
            pos = self.mapSceneToView(ev.scenePos())
            y_pos = pos.y()

            # 获取当前视图范围
            view_range = self.viewRange()
            y_range = view_range[1]

            # 检查是否在Y轴顶部或底部区域
            y_range_height = y_range[1] - y_range[0]
            top_threshold = y_range[1] - y_range_height * 0.2  # 顶部20%区域
            bottom_threshold = y_range[0] + y_range_height * 0.2  # 底部20%区域

            if y_pos > top_threshold or y_pos < bottom_threshold:
                # 重置Y轴范围到自动适应
                self.enableAutoRange(axis=self.YAxis)
                ev.accept()
                return

        # 调用父类的默认处理
        super().mouseDoubleClickEvent(ev)


class EnhancedChartWidget(ChartWidget):
    """
    增强版K线图表组件
    继承自vnpy的ChartWidget，提供丰富的技术指标和交互功能
    """
    
    def __init__(self, parent: QtWidgets.QWidget = None):
        # 首先初始化配置，这些在父类初始化之前设置
        self.main_indicators = {
            "boll": [BollItem, "boll", True, True],
            "sma": [MultiSmaItem, "sma", True, True],
            "ema": [MultiEmaItem, "ema", True, True],
        }
        
        self.sub_indicators = {
            "volume": [VolumeItem, "volume", True, 120, 200, False],
            "macd": [Macd3Item, "macd", True, 120, 180, True],
            "rsi": [RsiItem, "rsi", False, 100, 150, True],
            "dmi": [DmiItem, "dmi", False, 100, 150, True],
        }
        
        # 记录指标可见状态
        self.main_indicator_visibility = {name: config[2] for name, config in self.main_indicators.items()}
        self.sub_indicator_visibility = {name: config[2] for name, config in self.sub_indicators.items()}
        
        # 保存绘图区域的原始高度，用于双击恢复
        self.original_heights = {}
        # 记录哪些绘图区域处于放大状态
        self.enlarged_plots = set()
        
        # 多周期相关属性
        self.current_interval = Interval.MINUTE  # 默认1分钟
        self._actual_interval = "1m"  # 实际周期字符串
        self.current_symbol = ""
        self.current_exchange = None
        self.base_minute_bars = []  # 保存原始1分钟K线数据
        self.interval_buttons = {}  # 保存周期按钮引用
        
        # 交易时段定义（可通过set_trading_session设置）
        self.trading_session = None  # 交易时段对象
        
        # 调用父类初始化
        super().__init__(parent)
        
        # 设置窗口标题
        self.setWindowTitle("增强版K线图表")
        
        # 初始化图表（父类初始化完成后）
        self._init_charts()
        
        # 创建控制界面
        self._create_controls()
        
        # 创建周期切换面板
        self._create_interval_panel()
        
        # 设置附图双击事件
        self._setup_double_click_handlers()
    
    def _setup_high_quality_rendering(self):
        """设置高质量渲染"""
        try:
            # 启用抗锯齿
            pg.setConfigOptions(antialias=True)
            pg.setConfigOptions(useOpenGL=True)
            pg.setConfigOptions(background='k')  # 黑色背景
            
            # 设置图表的渲染质量
            for plot_item in self._plots.values() if hasattr(self, '_plots') else []:
                if hasattr(plot_item, 'getViewBox'):
                    viewbox = plot_item.getViewBox()
                    if viewbox:
                        # 启用抗锯齿
                        viewbox.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
                        viewbox.setRenderHint(QtGui.QPainter.RenderHint.TextAntialiasing, True)
                        viewbox.setRenderHint(QtGui.QPainter.RenderHint.SmoothPixmapTransform, True)
                        
        except Exception as e:
            print(f"设置高质量渲染时出错: {e}")
    
    def _apply_high_quality_to_plots(self):
        """将高质量渲染设置应用到所有绘图区域"""
        try:
            for plot_name, plot_item in self._plots.items():
                if hasattr(plot_item, 'getViewBox'):
                    viewbox = plot_item.getViewBox()
                    if viewbox:
                        # 设置高质量变换
                        if hasattr(viewbox, 'setAspectLocked'):
                            viewbox.setAspectLocked(False)
                        
                        # 对于ExtendableViewBox，尝试设置其他质量选项
                        if hasattr(viewbox, 'setAntialiasing'):
                            viewbox.setAntialiasing(True)
                        
                        # 设置绘图项目的质量
                        if hasattr(plot_item, 'setAntialiasing'):
                            plot_item.setAntialiasing(True)
                            
        except Exception as e:
            print(f"应用高质量渲染到绘图区域时出错: {e}")
    
    def _init_charts(self):
        """初始化图表结构"""
        # 创建主图
        self.add_plot("candle", minimum_height=300, hide_x_axis=True)
        self.add_item(CandleItem, "candle", "candle")
        
        # 添加主图指标
        for name, config in self.main_indicators.items():
            item_class, item_key, default_visible, _ = config
            self.add_item(item_class, item_key, "candle")
            
            # 如果默认不可见，则隐藏
            if not default_visible:
                self._items[item_key].hide()
        
        # 创建附图
        for name, config in self.sub_indicators.items():
            item_class, item_key, default_visible, min_height, max_height, _ = config
            
            # 创建附图
            self.add_plot(name, minimum_height=min_height, maximum_height=max_height, hide_x_axis=(name != "volume"))
            self.add_item(item_class, name, item_key)
            
            # 保存原始高度
            self.original_heights[name] = {
                "minimum_height": min_height,
                "maximum_height": max_height
            }
            
            # 如果默认不可见，则隐藏附图
            if not default_visible:
                self._plots[name].hide()
        
        # 添加光标
        self.add_cursor()
    
    def add_plot(self, plot_name: str, minimum_height: int = 80, maximum_height: int = None, hide_x_axis: bool = False) -> None:
        """
        重写父类的add_plot方法，使用自定义的ExtendableViewBox
        """
        # 创建自定义ViewBox
        viewbox = ExtendableViewBox(self)
        
        # 创建plot对象，使用自定义ViewBox
        plot = pg.PlotItem(
            axisItems={'bottom': self._get_new_x_axis()},
            viewBox=viewbox,
            name=plot_name
        )
        plot.setMenuEnabled(False)
        plot.setClipToView(True)
        plot.hideAxis('left')
        plot.showAxis('right')
        plot.setDownsampling(mode='peak')
        plot.setRange(xRange=(0, 1), yRange=(0, 1))
        plot.hideButtons()
        plot.setMinimumHeight(minimum_height)
        
        if maximum_height:
            plot.setMaximumHeight(maximum_height)
        
        if hide_x_axis:
            plot.hideAxis("bottom")
        
        if not self._first_plot:
            self._first_plot = plot
        
        # 连接view change信号到更新y范围函数
        view = plot.getViewBox()
        view.sigXRangeChanged.connect(self._update_y_range)
        view.setMouseEnabled(x=True, y=True)
        
        # 设置右轴
        right_axis = plot.getAxis('right')
        right_axis.setWidth(60)
        right_axis.tickFont = NORMAL_FONT
        
        # 连接x轴链接
        if self._plots:
            first_plot = list(self._plots.values())[0]
            plot.setXLink(first_plot)
        
        # 保存plot对象
        self._plots[plot_name] = plot
        
        # 添加plot到布局
        self._layout.nextRow()
        self._layout.addItem(plot)
    
    def _create_controls(self):
        """创建控制界面"""
        # 创建主图指标控制面板
        self._create_main_indicator_controls()
        
        # 创建附图指标控制面板
        self._create_sub_indicator_controls()
    
    def _create_main_indicator_controls(self):
        """创建主图指标控制面板"""
        control_widget = QtWidgets.QWidget(self)
        control_layout = QtWidgets.QHBoxLayout(control_widget)
        control_layout.setContentsMargins(10, 0, 10, 0)
        control_layout.setSpacing(5)  # 减少控件间距
        
        # 创建标签
        label = QtWidgets.QLabel("主图指标：")
        control_layout.addWidget(label)
        
        # 创建复选框
        self.main_checkboxes = {}
        for name, config in self.main_indicators.items():
            # 为每个指标创建容器
            indicator_container = QtWidgets.QHBoxLayout()
            indicator_container.setContentsMargins(0, 0, 0, 0)
            indicator_container.setSpacing(0)  # 复选框、标签和按钮之间无间距
            indicator_container.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)  # 容器不拉伸
            
            # 创建复选框和标签的组合
            checkbox = QtWidgets.QCheckBox()
            checkbox.setChecked(config[2])  # 默认可见状态
            checkbox.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            checkbox.setFixedSize(16, 16)  # 固定复选框大小
            
            # 创建标签显示文本
            label = QtWidgets.QLabel(name)
            label.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
            label.setStyleSheet("QLabel { margin: 0; padding: 0; text-align: left; }")
            label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            label.setMinimumWidth(0)
            label.adjustSize()
            
            # 将复选框和标签添加到容器
            indicator_container.addWidget(checkbox)
            indicator_container.addWidget(label)
            # 使用partial避免闭包问题
            checkbox.stateChanged.connect(partial(self._toggle_main_indicator, name))
            self.main_checkboxes[name] = checkbox
            
            # 如果指标可配置，添加配置按钮
            if len(config) > 3 and config[3]:  # 可配置
                config_btn = QtWidgets.QPushButton("⚙️")
                config_btn.setFixedSize(20, 20)
                config_btn.setStyleSheet("""
                    QPushButton {
                        background: transparent;
                        border: none;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: rgba(128, 128, 128, 0.2);
                        border-radius: 3px;
                    }
                """)
                config_btn.setToolTip(f"配置{name}")
                config_btn.clicked.connect(partial(self._configure_indicator, name, True))
                indicator_container.addWidget(config_btn)
            
            # 将容器添加到主布局
            control_layout.addLayout(indicator_container)
        
        # 自适应宽度设置
        control_widget.adjustSize()
        control_widget.setFixedHeight(30)
        control_widget.move(10, 5)
        self.main_controls_widget = control_widget
    
    def _create_sub_indicator_controls(self):
        """创建附图指标控制面板"""
        control_widget = QtWidgets.QWidget(self)
        control_layout = QtWidgets.QHBoxLayout(control_widget)
        control_layout.setContentsMargins(10, 0, 10, 0)
        control_layout.setSpacing(5)  # 减少控件间距
        
        # 创建标签
        label = QtWidgets.QLabel("附图指标：")
        control_layout.addWidget(label)
        
        # 创建复选框
        self.sub_checkboxes = {}
        for name, config in self.sub_indicators.items():
            # 为每个指标创建容器
            indicator_container = QtWidgets.QHBoxLayout()
            indicator_container.setContentsMargins(0, 0, 0, 0)
            indicator_container.setSpacing(0)  # 复选框、标签和按钮之间无间距
            indicator_container.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)  # 容器不拉伸
            
            # 创建复选框和标签的组合
            checkbox = QtWidgets.QCheckBox()
            checkbox.setChecked(config[2])  # 默认可见状态
            checkbox.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            checkbox.setFixedSize(16, 16)  # 固定复选框大小
            
            # 创建标签显示文本
            label = QtWidgets.QLabel(name)
            label.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
            label.setStyleSheet("QLabel { margin: 0; padding: 0; text-align: left; }")
            label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            label.setMinimumWidth(0)
            label.adjustSize()
            
            # 将复选框和标签添加到容器
            indicator_container.addWidget(checkbox)
            indicator_container.addWidget(label)
            # 使用partial避免闭包问题
            checkbox.stateChanged.connect(partial(self._toggle_sub_indicator, name))
            self.sub_checkboxes[name] = checkbox
            
            # 如果指标可配置，添加配置按钮
            if len(config) > 5 and config[5]:  # 可配置
                config_btn = QtWidgets.QPushButton("⚙️")
                config_btn.setFixedSize(20, 20)
                config_btn.setStyleSheet("""
                    QPushButton {
                        background: transparent;
                        border: none;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: rgba(128, 128, 128, 0.2);
                        border-radius: 3px;
                    }
                """)
                config_btn.setToolTip(f"配置{name}")
                config_btn.clicked.connect(partial(self._configure_indicator, name, False))
                indicator_container.addWidget(config_btn)
            
            # 将容器添加到主布局
            control_layout.addLayout(indicator_container)
        
        # 自适应宽度设置
        control_widget.adjustSize()
        control_widget.setFixedHeight(30)
        control_widget.move(10, self.height() - 60)
        self.sub_controls_widget = control_widget
        
        # 重写resize事件以更新控件位置
        original_resize_event = self.resizeEvent
        
        def resize_event_handler(event):
            if original_resize_event:
                original_resize_event(event)
            
            # 更新附图控制面板位置
            if hasattr(self, 'sub_controls_widget'):
                self.sub_controls_widget.move(10, self.height() - 60)
        
        self.resizeEvent = resize_event_handler
    
    def _toggle_main_indicator(self, name: str, state: int):
        """切换主图指标的可见性"""
        if name not in self.main_indicators:
            return
        
        item_class, item_key, default_visible, configurable = self.main_indicators[name]
        is_checked = state == QtCore.Qt.Checked.value
        
        if is_checked:
            # 如果要显示但指标不存在，重新创建
            if item_key not in self._items:
                print(f"重新创建指标: {name}")
                self.add_item(item_class, item_key, "candle")
                # 立即更新数据
                history = self._manager.get_all_bars()
                if history:
                    self._items[item_key].update_history(history)
                    # 强制重绘
                    self._items[item_key].update()
            else:
                # 如果存在，确保它在绘图区域中
                print(f"重新显示指标: {name}")
                plot = self._plots["candle"]
                item = self._items[item_key]
                # 确保添加到绘图区域
                if item not in plot.items:
                    plot.addItem(item)
                # 确保可见并重绘
                item.show()
                # 重新计算数据
                history = self._manager.get_all_bars()
                if history:
                    item.update_history(history)
                    item.update()
        else:
            # 移除指标但保留在_items中以便重新显示
            if item_key in self._items:
                print(f"隐藏指标: {name}")
                plot = self._plots["candle"]
                item = self._items[item_key]
                plot.removeItem(item)
        
        self.main_indicator_visibility[name] = is_checked
        # 强制重绘整个图表
        self.update()
        # 刷新视图
        if hasattr(self, '_plots') and "candle" in self._plots:
            self._plots["candle"].update()
    
    def _toggle_sub_indicator(self, name: str, state: int):
        """切换附图指标的可见性"""
        if name not in self.sub_indicators:
            return
        
        item_class, item_key, default_visible, min_height, max_height, configurable = self.sub_indicators[name]
        is_checked = state == QtCore.Qt.Checked.value
        
        if is_checked:
            # 如果要显示但绘图区域不存在，重新创建
            if name not in self._plots:
                self.add_plot(name, minimum_height=min_height, maximum_height=max_height)
                self.add_item(item_class, name, item_key)
                # 立即更新数据
                history = self._manager.get_all_bars()
                if history and item_key in self._items:
                    self._items[item_key].update_history(history)
                    self._items[item_key].update()
            else:
                # 如果存在，确保可见
                plot = self._plots[name]
                plot.show()
                if item_key in self._items:
                    item = self._items[item_key]
                    item.setVisible(True)
                    # 重新计算数据
                    history = self._manager.get_all_bars()
                    if history:
                        item.update_history(history)
                        item.update()
        else:
            # 隐藏绘图区域
            if name in self._plots:
                plot = self._plots[name]
                plot.hide()
                if item_key in self._items:
                    item = self._items[item_key]
                    item.setVisible(False)
        
        self.sub_indicator_visibility[name] = is_checked
        self._layout.updateGeometry()
        # 强制重绘
        self.update()
    
    def _configure_indicator(self, name: str, is_main_indicator: bool):
        """配置指标参数"""
        if is_main_indicator:
            if name not in self.main_indicators:
                return
            item_key = self.main_indicators[name][1]
        else:
            if name not in self.sub_indicators:
                return
            item_key = self.sub_indicators[name][1]
        
        if item_key not in self._items:
            return
        
        item = self._items[item_key]
        if not isinstance(item, ConfigurableIndicator):
            QtWidgets.QMessageBox.information(self, "提示", f"{name} 指标不支持配置")
            return
        
        # 获取配置对话框
        dialog = item.get_config_dialog(self)
        
        # 保存原始的应用配置方法
        original_apply_config = item.apply_config
        
        # 包装应用配置方法，添加图表更新逻辑
        def wrapped_apply_config(config):
            # 调用原始配置方法
            original_apply_config(config)
            
            # 强制更新数据和重绘
            history = self._manager.get_all_bars()
            if history:
                item.update_history(history)
                item.update()
            
            # 刷新图表
            self.update()
            
            # 如果是主图指标，也刷新主图
            if is_main_indicator and "candle" in self._plots:
                self._plots["candle"].update()
            # 如果是附图指标，刷新对应的附图
            elif not is_main_indicator:
                for plot_name, plot in self._plots.items():
                    if plot_name != "candle" and item_key in self._items:
                        plot.update()
                        break
        
        # 临时替换应用配置方法
        item.apply_config = wrapped_apply_config
        
        try:
            result = dialog.exec_()
        finally:
            # 恢复原始方法
            item.apply_config = original_apply_config
        
        return result
    
    def _setup_double_click_handlers(self):
        """设置附图双击事件处理"""
        for plot_name, plot in self._plots.items():
            if plot_name != "candle":  # 跳过主图
                # 为plot设置双击事件处理
                original_double_click = getattr(plot, 'mouseDoubleClickEvent', None)
                
                def create_double_click_handler(name, original_handler):
                    def double_click_handler(event):
                        if original_handler:
                            original_handler(event)
                        self._toggle_plot_size(name)
                    return double_click_handler
                
                plot.mouseDoubleClickEvent = create_double_click_handler(plot_name, original_double_click)
    
    def _toggle_plot_size(self, plot_name: str):
        """切换附图的大小状态（放大/恢复原始大小）"""
        if plot_name not in self._plots:
            return
        
        # 保存当前的可见性状态
        current_visibility = {}
        for name, plot in self._plots.items():
            current_visibility[name] = plot.isVisible()
        
        plot = self._plots[plot_name]
        
        if plot_name in self.enlarged_plots:
            # 恢复原始大小
            if plot_name in self.original_heights:
                original = self.original_heights[plot_name]
                minimum_height = original["minimum_height"]
                maximum_height = original["maximum_height"]
                
                plot.setMinimumHeight(minimum_height)
                if maximum_height:
                    plot.setMaximumHeight(maximum_height)
                else:
                    plot.setMaximumHeight(16777215)
            
            self.enlarged_plots.remove(plot_name)
        else:
            # 放大
            self.enlarged_plots.add(plot_name)
            plot.setMinimumHeight(400)
            plot.setMaximumHeight(16777215)
        
        # 更新布局
        self._layout.updateGeometry()
        
        # 恢复可见性状态
        for name, visible in current_visibility.items():
            if name in self._plots:
                if visible:
                    self._plots[name].show()
                else:
                    self._plots[name].hide()
    
        else:
            QtWidgets.QMessageBox.information(self, "提示", "此指标暂不支持配置")
    
    def update_history(self, history: List[BarData]) -> None:
        """更新历史数据"""
        # 保存原始1分钟K线数据
        if history and history[0].interval == Interval.MINUTE:
            self.base_minute_bars = history.copy()
        
        # 如果当前不是1分钟周期，需要重新聚合数据
        if self.current_interval != Interval.MINUTE and self.base_minute_bars:
            aggregated_bars = self._aggregate_bars(self.base_minute_bars, self.current_interval)
            super().update_history(aggregated_bars)
        else:
            super().update_history(history)
        
        # 移动到最右侧显示最新数据
        self.move_to_right()
    
    def update_bar(self, bar: BarData) -> None:
        """更新单个K线数据"""
        super().update_bar(bar)
    
    def clear_all(self) -> None:
        """清空所有数据"""
        for item in self._items.values():
            if hasattr(item, 'clear_all'):
                item.clear_all()
        
        self.update()
    
    def _get_hour_session_index(self, bar_time: time) -> Optional[int]:
        """
        根据交易时段判断当前时间属于哪个小时时段
        
        注意：时段范围是闭区间，start和end分别表示该时段的第一分钟和最后一分钟
        例如：(time(9,0), time(9,59)) 表示 09:00-09:59 这一小时的所有分钟
        
        Args:
            bar_time: K线时间（1分钟K线的时间戳）
        
        Returns:
            时段索引，如果不在任何时段内则返回None（将按自然小时聚合）
        """
        if not self.trading_session or not self.trading_session.hour_sessions:
            # 如果没有定义交易时段，返回None（使用自然小时）
            return None
        
        # 先检查日盘时段
        for idx, (start, end) in enumerate(self.trading_session.hour_sessions):
            # 时段范围是闭区间 [start, end]
            # start和end都表示分钟级别的时间点
            if start <= bar_time <= end:
                return idx
        
        # 如果有夜盘，检查夜盘时段
        if self.trading_session.has_night_session and self.trading_session.night_sessions:
            offset = len(self.trading_session.hour_sessions)
            for idx, (start, end) in enumerate(self.trading_session.night_sessions):
                # 夜盘可能跨越午夜（例如 23:00 到次日 02:30）
                if start <= end:
                    # 不跨午夜的情况
                    if start <= bar_time <= end:
                        return offset + idx
                else:
                    # 跨午夜的情况（例如 23:00 > 02:30，表示23:00-23:59和00:00-02:30）
                    if bar_time >= start or bar_time <= end:
                        return offset + idx
        
        # 不在任何定义的时段内，返回None（按自然小时处理）
        return None
    
    def _aggregate_bars(self, minute_bars: List[BarData], target_interval: Interval) -> List[BarData]:
        """
        将1分钟K线聚合为目标周期的K线
        
        Args:
            minute_bars: 1分钟K线数据列表
            target_interval: 目标周期（5m, 15m, 1h, d）
        
        Returns:
            聚合后的K线数据列表
        """
        if not minute_bars:
            return []
        
        # 确定聚合周期的分钟数
        interval_minutes = {
            "1m": 1,
            "5m": 5,
            "15m": 15,
            "1h": 60,
            "d": 1440  # 一天
        }
        
        interval_str = target_interval.value if isinstance(target_interval, Interval) else target_interval
        minutes = interval_minutes.get(interval_str, 1)
        
        if minutes == 1:
            return minute_bars
        
        aggregated = []
        current_bar = None
        
        for bar in minute_bars:
            # 确定当前bar应该属于哪个聚合周期
            if interval_str == "d":
                # 日线：按照日期聚合
                bar_key = bar.datetime.date()
            elif interval_str == "1h":
                # 小时线：按照交易时段或自然小时聚合
                bar_time = bar.datetime.time()
                session_index = self._get_hour_session_index(bar_time)
                
                if session_index is not None:
                    # 使用交易时段索引作为key
                    bar_key = (bar.datetime.date(), f"session_{session_index}")
                else:
                    # 使用自然小时作为key（夜盘或未定义交易时段时）
                    bar_key = (bar.datetime.date(), bar.datetime.hour)
            else:
                # 其他周期：按照时间段聚合
                total_minutes = bar.datetime.hour * 60 + bar.datetime.minute
                period_index = total_minutes // minutes
                bar_key = (bar.datetime.date(), period_index)
            
            if current_bar is None:
                # 开始新的聚合周期
                current_bar = BarData(
                    symbol=bar.symbol,
                    exchange=bar.exchange,
                    datetime=bar.datetime,
                    interval=target_interval,
                    open_price=bar.open_price,
                    high_price=bar.high_price,
                    low_price=bar.low_price,
                    close_price=bar.close_price,
                    volume=bar.volume,
                    turnover=bar.turnover,
                    open_interest=bar.open_interest,
                    gateway_name=bar.gateway_name
                )
                current_bar_key = bar_key
            else:
                # 检查是否需要开始新的聚合周期
                if bar_key != current_bar_key:
                    # 保存当前聚合的bar
                    aggregated.append(current_bar)
                    
                    # 开始新的聚合周期
                    current_bar = BarData(
                        symbol=bar.symbol,
                        exchange=bar.exchange,
                        datetime=bar.datetime,
                        interval=target_interval,
                        open_price=bar.open_price,
                        high_price=bar.high_price,
                        low_price=bar.low_price,
                        close_price=bar.close_price,
                        volume=bar.volume,
                        turnover=bar.turnover,
                        open_interest=bar.open_interest,
                        gateway_name=bar.gateway_name
                    )
                    current_bar_key = bar_key
                else:
                    # 继续聚合到当前bar
                    current_bar.high_price = max(current_bar.high_price, bar.high_price)
                    current_bar.low_price = min(current_bar.low_price, bar.low_price)
                    current_bar.close_price = bar.close_price
                    current_bar.volume += bar.volume
                    current_bar.turnover += bar.turnover
                    current_bar.open_interest = bar.open_interest  # 使用最新的持仓量
        
        # 添加最后一个聚合的bar
        if current_bar is not None:
            aggregated.append(current_bar)
        
        return aggregated
    
    def set_trading_session(self, trading_session):
        """
        设置交易时段
        
        Args:
            trading_session: TradingSession对象或MarketType枚举
        """
        from config.trading_sessions_config import MarketType, get_trading_session
        
        if isinstance(trading_session, MarketType):
            self.trading_session = get_trading_session(trading_session)
        else:
            self.trading_session = trading_session
    
    def set_trading_session_by_symbol(self, symbol: str, exchange: str = ""):
        """
        根据品种代码自动设置交易时段
        
        Args:
            symbol: 品种代码
            exchange: 交易所代码
        """
        from config.trading_sessions_config import get_trading_session_by_symbol
        
        self.trading_session = get_trading_session_by_symbol(symbol, exchange)
        self.current_symbol = symbol
        self.current_exchange = exchange
    
    def _create_interval_panel(self):
        """创建时间周期切换面板"""
        # 创建透明的容器
        panel_widget = QtWidgets.QWidget(self)
        panel_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(30, 30, 30, 150);
                border-radius: 5px;
            }
        """)
        
        panel_layout = QtWidgets.QVBoxLayout(panel_widget)
        panel_layout.setContentsMargins(8, 10, 8, 10)
        panel_layout.setSpacing(10)
        
        # 定义周期选项 - 文字竖排显示
        intervals = [
            ("1m", "1\n分\n钟", Interval.MINUTE),
            ("5m", "5\n分\n钟", "5m"),
            ("15m", "15\n分\n钟", "15m"),
            ("1h", "1\n小\n时", Interval.HOUR),
            ("d", "日\n线", Interval.DAILY),
        ]
        
        # 创建按钮
        for key, label, interval in intervals:
            btn = QtWidgets.QPushButton(label)
            # 调整按钮大小以适应竖排文字
            if key == "15m":
                btn.setFixedSize(40, 70)  # 15分钟需要更高的按钮
            elif key == "d":
                btn.setFixedSize(40, 50)  # 日线只有两个字
            else:
                btn.setFixedSize(40, 60)
            
            btn.setCheckable(True)
            
            # 设置按钮样式
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(60, 60, 60, 200);
                    color: white;
                    border: 1px solid rgba(100, 100, 100, 200);
                    border-radius: 3px;
                    font-size: 11px;
                    line-height: 1.2;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: rgba(80, 80, 80, 220);
                    border: 1px solid rgba(120, 120, 120, 220);
                }
                QPushButton:checked {
                    background-color: rgba(0, 120, 215, 220);
                    border: 2px solid rgba(0, 150, 255, 255);
                    font-weight: bold;
                }
            """)
            
            # 默认选中1分钟
            if key == "1m":
                btn.setChecked(True)
            
            # 连接点击事件 - 使用 lambda 确保传递正确的参数
            btn.clicked.connect(lambda checked, i=interval, b=btn: self._on_interval_changed(i, b))
            
            # 保存按钮引用
            self.interval_buttons[key] = btn
            
            panel_layout.addWidget(btn)
        
        # 添加弹簧（用于居中）
        panel_layout.addStretch()
        
        # 设置面板位置和大小
        panel_widget.setFixedWidth(58)
        panel_widget.adjustSize()
        
        self.interval_panel = panel_widget
        
        # 重写resize事件以更新面板位置（垂直居中）
        original_resize = self.resizeEvent
        
        def resize_handler(event):
            if original_resize:
                original_resize(event)
            
            # 更新周期面板位置（垂直居中）
            if hasattr(self, 'interval_panel'):
                # 计算垂直居中位置
                panel_height = self.interval_panel.height()
                window_height = self.height()
                y_pos = (window_height - panel_height) // 2
                self.interval_panel.move(10, max(50, y_pos))  # 至少在顶部50px处
        
        self.resizeEvent = resize_handler
        
        # 初始位置
        panel_height = panel_widget.height()
        window_height = self.height()
        y_pos = (window_height - panel_height) // 2
        panel_widget.move(10, max(50, y_pos))
    
    def _on_interval_changed(self, interval, clicked_btn):
        """处理周期切换事件"""
        # 更新当前周期
        if isinstance(interval, str):
            # 自定义周期字符串转换
            interval_map = {
                "5m": Interval.MINUTE,  # 暂时用MINUTE表示
                "15m": Interval.MINUTE,
                "1h": Interval.HOUR,
                "d": Interval.DAILY
            }
            self.current_interval = interval_map.get(interval, Interval.MINUTE)
            # 保存实际的周期字符串用于聚合
            self._actual_interval = interval
        else:
            self.current_interval = interval
            self._actual_interval = interval.value
        
        # 更新按钮状态 - 只保持一个按钮被选中
        # 先取消所有按钮的选中状态
        for btn in self.interval_buttons.values():
            btn.setChecked(False)
        
        # 然后设置当前点击的按钮为选中状态
        if clicked_btn:
            clicked_btn.setChecked(True)
        
        # 如果有基础数据，重新聚合并更新图表
        if self.base_minute_bars:
            print(f"\n切换到周期: {self._actual_interval}")
            
            if self._actual_interval == "1m":
                # 显示原始1分钟数据
                bars_to_display = self.base_minute_bars
            else:
                # 聚合数据
                bars_to_display = self._aggregate_bars(self.base_minute_bars, self._actual_interval)
            
            print(f"聚合后K线数量: {len(bars_to_display)}")
            
            # 第一步：清空所有指标的数据缓存
            print("清空指标缓存...")
            for item_name, item in self._items.items():
                if hasattr(item, 'clear_all'):
                    try:
                        item.clear_all()
                    except Exception as e:
                        print(f"清空指标 {item_name} 时出错: {e}")
            
            # 第二步：清空管理器数据
            print("清空K线管理器...")
            self._manager.clear_all()
            
            # 第三步：重新添加数据到管理器
            print("重新加载K线数据...")
            for bar in bars_to_display:
                self._manager.update_bar(bar)
            
            # 第四步：强制更新所有指标 - 确保它们使用新的数据
            print("更新所有指标...")
            for item_name, item in self._items.items():
                try:
                    # 更新指标数据
                    if hasattr(item, 'update_history'):
                        item.update_history(bars_to_display)
                        print(f"  ✓ {item_name} 更新完成")
                    
                    # 强制重绘
                    if hasattr(item, 'update'):
                        item.update()
                except Exception as e:
                    print(f"  ✗ 更新指标 {item_name} 时出错: {e}")
                    import traceback
                    traceback.print_exc()
            
            # 第五步：更新图表范围
            print("更新图表范围...")
            self._update_plot_limits()
            
            # 第六步：移动到最右侧
            self.move_to_right()
            
            # 第七步：强制刷新所有绘图区域
            print("刷新所有绘图区域...")
            for plot_name, plot in self._plots.items():
                plot.update()
            
            # 第八步：刷新整个组件
            self.update()
            
            print("✓ 周期切换完成\n")
