#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图表相关模块
包含定制化图表和技术指标的实现
"""

from core.indicators.indicator_base import ConfigurableIndicator
from core.indicators.boll_item import BollItem
from core.indicators.multi_sma_item import MultiSmaItem
from core.indicators.multi_ema_item import MultiEmaItem
from core.indicators.rsi_item import RsiItem
from core.indicators.macd_item import Macd3Item
from core.indicators.dmi_item import DmiItem
from core.indicators.dyna_array_manager import DynaArrayManager

# 保持向后兼容
try:
    from .enhanced_chart_widget import (
        EnhancedChartWidget,
        VolumeItem
    )
    from .components.extendable_viewbox import ExtendableViewBox
    from .components.cursor_manager import CursorManager
    _enhanced_available = True
except ImportError:
    # 如果enhanced_chart_widget有问题，只导出独立指标
    _enhanced_available = False

# 导入双图组件
try:
    from .dual_chart_widget import (
        DualChartWidget,
        ChartTimeAxisSync
    )
    _dual_chart_available = True
except ImportError:
    _dual_chart_available = False

# 导入四图组件
try:
    from .quad_chart_widget import (
        QuadChartWidget,
        QuadChartTimeAxisSync
    )
    _quad_chart_available = True
except ImportError:
    _quad_chart_available = False

__all__ = [
    # 基础配置接口
    "ConfigurableIndicator",
    
    # 独立技术指标
    "BollItem",
    "MultiSmaItem",
    "MultiEmaItem", 
    "RsiItem",
    "Macd3Item",
    "DmiItem",
    
    # 工具类
    "DynaArrayManager",
]

# 如果增强图表可用，添加到导出列表
if _enhanced_available:
    __all__.extend([
        "EnhancedChartWidget",
        "ExtendableViewBox",
        "CursorManager",
        "VolumeItem"
    ])

# 如果双图组件可用，添加到导出列表
if _dual_chart_available:
    __all__.extend([
        "DualChartWidget",
        "ChartTimeAxisSync"
    ])

# 如果四图组件可用，添加到导出列表
if _quad_chart_available:
    __all__.extend([
        "QuadChartWidget",
        "QuadChartTimeAxisSync"
    ])