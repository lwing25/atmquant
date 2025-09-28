#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RSI相对强弱指标
基于vnpy ChartItem实现的RSI技术指标
"""

from typing import Dict, Any, Tuple
import numpy as np
import talib
import pyqtgraph as pg

from vnpy.trader.ui import QtCore, QtGui, QtWidgets
from vnpy.trader.object import BarData
from vnpy.chart.item import ChartItem
from vnpy.chart.manager import BarManager

from .indicator_base import ConfigurableIndicator


class RsiItem(ChartItem, ConfigurableIndicator):
    """
    RSI相对强弱指标
    参考原始代码风格，支持参数配置
    """

    def __init__(self, manager: BarManager, rsi_window: int = 14, 
                 rsi_long_threshold: float = 70, rsi_short_threshold: float = 30):
        """初始化RSI指标"""
        super().__init__(manager)
        
        # 参数设置
        self.rsi_window = rsi_window
        self.rsi_long_threshold = rsi_long_threshold
        self.rsi_short_threshold = rsi_short_threshold
        
        # 颜色配置
        self.white_pen: QtGui.QPen = pg.mkPen(color=(255, 255, 255, 90), width=1)
        self.yellow_pen: QtGui.QPen = pg.mkPen(color=(255, 255, 0), width=2)
        self.gold_pen: QtGui.QPen = pg.mkPen(color=(252, 173, 4), width=5)  # 金色
        self.purple_pen: QtGui.QPen = pg.mkPen(color=(128, 0, 128), width=5)
        
        # 添加新的笔用于超买超卖区域
        self.overbought_pen: QtGui.QPen = pg.mkPen(color=(255, 50, 50), width=3)  # 红色粗线
        self.oversold_pen: QtGui.QPen = pg.mkPen(color=(50, 255, 50), width=3)    # 绿色粗线
        
        # 数据缓存
        self.rsi_data: Dict[int, float] = {}
        
        # 背离数据
        self.start_bull_indices = []
        self.end_bull_indices = []
        self.start_bear_indices = []
        self.end_bear_indices = []

    def add_divergence_pairs(self, rsi_window, bull_divergence_pairs, bear_divergence_pairs):
        """添加背离对"""
        self.rsi_window = rsi_window
        self.start_bull_indices = [pair[1] for pair in bull_divergence_pairs]
        self.end_bull_indices = [pair[0] for pair in bull_divergence_pairs]
        self.start_bear_indices = [pair[1] for pair in bear_divergence_pairs]
        self.end_bear_indices = [pair[0] for pair in bear_divergence_pairs]
        
    def set_thresholds(self, long_threshold: float = 70, short_threshold: float = 30):
        """设置RSI的超买超卖阈值"""
        self.rsi_long_threshold = long_threshold
        self.rsi_short_threshold = short_threshold

    def get_rsi_value(self, ix: int) -> float:
        """获取RSI值"""
        if ix < 0:
            return 50

        # 当初始化时，计算所有rsi值
        if not self.rsi_data:
            bars = self._manager.get_all_bars()
            close_data = [bar.close_price for bar in bars]
            rsi_array = talib.RSI(np.array(close_data), self.rsi_window)

            for n, value in enumerate(rsi_array):
                if not np.isnan(value):
                    self.rsi_data[n] = value

        # 返回已计算的值
        if ix in self.rsi_data:
            return self.rsi_data[ix]

        # 计算新值
        close_data = []
        for n in range(max(0, ix - self.rsi_window), ix + 1):
            bar = self._manager.get_bar(n)
            if bar is not None:
                close_data.append(bar.close_price)
            else:
                # 如果bar为None，使用前一个有效值或默认值
                if close_data:
                    close_data.append(close_data[-1])
                else:
                    close_data.append(0.0)

        if len(close_data) >= self.rsi_window:
            rsi_array = talib.RSI(np.array(close_data), self.rsi_window)
            rsi_value = rsi_array[-1]
            if not np.isnan(rsi_value):
                self.rsi_data[ix] = rsi_value
                return rsi_value

        return 50.0

    def _draw_bar_picture(self, ix: int, bar: BarData) -> QtGui.QPicture:
        """绘制RSI"""
        rsi_value = self.get_rsi_value(ix)
        last_rsi_value = self.get_rsi_value(ix - 1)

        # 创建绘图对象
        picture = QtGui.QPicture()
        painter = QtGui.QPainter(picture)

        # 绘制RSI线
        if not (np.isnan(last_rsi_value) or np.isnan(rsi_value)):
            end_point = QtCore.QPointF(ix, rsi_value)
            start_point = QtCore.QPointF(ix - 1, last_rsi_value)
            
            # 根据RSI值选择合适的笔
            if rsi_value >= self.rsi_long_threshold or last_rsi_value >= self.rsi_long_threshold:
                # 超买区域使用红色粗线
                painter.setPen(self.overbought_pen)
            elif rsi_value <= self.rsi_short_threshold or last_rsi_value <= self.rsi_short_threshold:
                # 超卖区域使用绿色粗线
                painter.setPen(self.oversold_pen)
            else:
                # 正常区域使用标准黄线
                painter.setPen(self.yellow_pen)
                
            painter.drawLine(start_point, end_point)

        # 绘制超买/超卖线
        painter.setPen(self.white_pen)
        ob_end_point = QtCore.QPointF(ix, self.rsi_long_threshold)
        ob_start_point = QtCore.QPointF(ix - 1, self.rsi_long_threshold)
        painter.drawLine(ob_start_point, ob_end_point)
        
        os_end_point = QtCore.QPointF(ix, self.rsi_short_threshold)
        os_start_point = QtCore.QPointF(ix - 1, self.rsi_short_threshold)
        painter.drawLine(os_start_point, os_end_point)

        # 绘制背离线
        if ix in self.start_bull_indices:
            start_index = self.start_bull_indices.index(ix)
            if start_index < len(self.end_bull_indices):
                end_index = self.end_bull_indices[start_index]
                last_rsi_value = self.get_rsi_value(end_index)
                start_point = QtCore.QPointF(ix, rsi_value)
                end_point = QtCore.QPointF(end_index, last_rsi_value)
                painter.setPen(self.purple_pen)
                painter.drawLine(start_point, end_point)

        if ix in self.start_bear_indices:
            start_index = self.start_bear_indices.index(ix)
            if start_index < len(self.end_bear_indices):
                end_index = self.end_bear_indices[start_index]
                last_rsi_value = self.get_rsi_value(end_index)
                start_point = QtCore.QPointF(ix, rsi_value)
                end_point = QtCore.QPointF(end_index, last_rsi_value)
                painter.setPen(self.gold_pen)
                painter.drawLine(start_point, end_point)

        painter.end()
        return picture

    def boundingRect(self) -> QtCore.QRectF:
        """返回边界矩形"""
        rect = QtCore.QRectF(
            0,
            15,
            len(self._bar_picutures),
            85
        )
        return rect

    def get_y_range(self, min_ix: int = None, max_ix: int = None) -> Tuple[float, float]:
        """获取Y轴范围"""
        return (15.0, 85.0)

    def get_info_text(self, ix: int) -> str:
        """获取RSI信息文本，包含数值和交易指导"""
        if ix in self.rsi_data:
            rsi_value = self.rsi_data[ix]
            
            # 基础信息
            words = [f"RSI ({self.rsi_window}): {rsi_value:.1f}"]
            
            # 添加状态信息
            if rsi_value > self.rsi_long_threshold:
                words.append("状态: 超买")
            elif rsi_value < self.rsi_short_threshold:
                words.append("状态: 超卖")
            else:
                words.append("状态: 正常")
            
            return "\n".join(words)
        
        return f"RSI({self.rsi_window})"

    def clear_all(self) -> None:
        """清除所有数据"""
        super().clear_all()
        self.rsi_data.clear()
        self._bar_picutures.clear()
        self.update()

    def update_history(self, history) -> None:
        """更新历史数据时清空缓存"""
        self.rsi_data.clear()
        super().update_history(history)

    def update_bar(self, bar: BarData) -> None:
        """更新单个K线时清理缓存"""
        # 清理最后几个数据点的缓存
        bar_count = self._manager.get_count()
        keys_to_remove = [k for k in self.rsi_data.keys() if k >= bar_count - 10]
        for key in keys_to_remove:
            self.rsi_data.pop(key, None)
        super().update_bar(bar)

    # 配置相关方法
    def get_config_dialog(self, parent: QtWidgets.QWidget) -> QtWidgets.QDialog:
        """获取配置对话框"""
        config_items = [
            ("rsi_window", "RSI周期", "spinbox", {"min": 5, "max": 100, "value": self.rsi_window}),
            ("rsi_long_threshold", "超买阈值", "doublespinbox", {"min": 60.0, "max": 90.0, "step": 1.0, "value": self.rsi_long_threshold}),
            ("rsi_short_threshold", "超卖阈值", "doublespinbox", {"min": 10.0, "max": 40.0, "step": 1.0, "value": self.rsi_short_threshold})
        ]
        return self.create_config_dialog(parent, "RSI配置", config_items)

    def apply_config(self, config: Dict[str, Any]) -> None:
        """应用配置"""
        self.rsi_window = config.get('rsi_window', self.rsi_window)
        self.rsi_long_threshold = config.get('rsi_long_threshold', self.rsi_long_threshold)
        self.rsi_short_threshold = config.get('rsi_short_threshold', self.rsi_short_threshold)
        self.rsi_data.clear()
        self.update()

    def get_current_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return {
            'rsi_window': self.rsi_window,
            'rsi_long_threshold': self.rsi_long_threshold,
            'rsi_short_threshold': self.rsi_short_threshold
        }

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'rsi_window': 14,
            'rsi_long_threshold': 70.0,
            'rsi_short_threshold': 30.0
        }

    def _get_config_help_text(self) -> str:
        """获取配置帮助文本"""
        return """
参数说明：
• RSI周期: 计算RSI的K线数量(建议14)
• 超买阈值: RSI超买线位置(通常70)
• 超卖阈值: RSI超卖线位置(通常30)

颜色说明：
• 黄色: 正常区域RSI线
• 红色: 超买区域RSI线
• 绿色: 超卖区域RSI线
• 白色虚线: 超买超卖参考线
        """
