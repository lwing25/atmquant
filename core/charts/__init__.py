#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图表相关模块
包含定制化图表和技术指标的实现
"""

from .indicator_base import ConfigurableIndicator
from .boll_item import BollItem
from .multi_sma_item import MultiSmaItem
from .multi_ema_item import MultiEmaItem
from .rsi_item import RsiItem
from .macd_item import Macd3Item
from .dmi_item import DmiItem
from .dyna_array_manager import DynaArrayManager

# 保持向后兼容
try:
    from .enhanced_chart_widget import (
        EnhancedChartWidget,
        ExtendableViewBox,
        VolumeItem
    )
    _enhanced_available = True
except ImportError:
    # 如果enhanced_chart_widget有问题，只导出独立指标
    _enhanced_available = False

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
        "VolumeItem"
    ])