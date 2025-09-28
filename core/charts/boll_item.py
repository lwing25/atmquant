#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
布林带指标 - 完全按照参考代码样式
"""

from typing import Dict, Tuple, Any
import numpy as np
import talib
from vnpy.trader.object import BarData
from vnpy.chart.item import CandleItem
from vnpy.trader.ui import QtGui, QtCore, QtWidgets
import pyqtgraph as pg

from .indicator_base import ConfigurableIndicator


class BollItem(CandleItem, ConfigurableIndicator):
    """
    布林带指标 - 参考原始代码样式
    """

    def __init__(self, manager, boll_window: int = 20, std_dev: float = 2.0):
        """
        初始化布林带指标
        """
        super().__init__(manager)
        
        # 参数设置
        self.boll_window = boll_window
        self.std_dev = std_dev
        
        # 创建画笔 - 完全按照参考代码
        # 创建代表中轨（移动平均线）的笔，灰白色，加粗
        self.white_pen: QtGui.QPen = pg.mkPen(color=(255, 255, 255), width=3)
        # 创建代表上轨的笔，亮蓝色，粗虚线
        self.upper_pen: QtGui.QPen = pg.mkPen(color=(0, 191, 255), width=2, style=QtCore.Qt.PenStyle.DashLine)
        # 创建代表下轨的笔，亮绿色，粗虚线
        self.lower_pen: QtGui.QPen = pg.mkPen(color=(50, 205, 50), width=2, style=QtCore.Qt.PenStyle.DashLine)
        # 区域填充颜色
        self.fill_brush = pg.mkBrush(color=(100, 149, 237, 35))  # 淡蓝色半透明
        
        # 数据缓存
        self.boll_data = {}

    def get_boll_value(self, ix: int):
        """
        获取指定窗口大小的 BOLL 值 - 参考原始代码
        """
        if ix < self.boll_window - 1:
            return 0

        # When initialize, calculate all boll value
        if not self.boll_data:
            bars = self._manager.get_all_bars()
            close_data = [bar.close_price for bar in bars]
            upper_array, middle_array, lower_array = talib.BBANDS(
                np.array(close_data),
                timeperiod=self.boll_window,
                # number of non-biased standard deviations from the mean
                nbdevup=self.std_dev,
                nbdevdn=self.std_dev,
                # Moving average type: simple moving average here
                matype=0
            )

            for n, value in enumerate(upper_array):
                if n < (self.boll_window - 1):
                    continue
                self.boll_data[n] = {
                    "upper": value,
                    "middle": middle_array[n],
                    "lower": lower_array[n]
                }

        # Return if already calculated
        if ix in self.boll_data:
            return self.boll_data[ix]

        # Else calculate new value
        close_data = []
        for n in range(ix - self.boll_window, ix + 1):
            bar = self._manager.get_bar(n)
            if bar is not None:  # 添加检查，确保bar不为None
                close_data.append(bar.close_price)
            else:
                # 如果bar为None，使用前一个有效值或默认值
                if close_data:
                    close_data.append(close_data[-1])  # 使用前一个值
                else:
                    close_data.append(0.0)  # 使用默认值

        upper_array, middle_array, lower_array = talib.BBANDS(
            np.array(close_data),
            timeperiod=self.boll_window,
            # number of non-biased standard deviations from the mean
            nbdevup=self.std_dev,
            nbdevdn=self.std_dev,
            # Moving average type: simple moving average here
            matype=0
        )
        boll_value = {
            "upper": upper_array[-1],
            "middle": middle_array[-1],
            "lower": lower_array[-1]
        }
        self.boll_data[ix] = boll_value

        return boll_value

    def _draw_bar_picture(self, ix: int, bar: BarData) -> QtGui.QPicture:
        """
        绘制K线与布林带 - 完全按照参考代码样式
        """
        boll_value = self.get_boll_value(ix)
        last_boll_value = self.get_boll_value(ix - 1)

        # Create objects
        picture = QtGui.QPicture()
        painter = QtGui.QPainter(picture)

        if last_boll_value == 0:
            # 如果没有前一个值，不绘制任何内容
            pass
        else:
            # 填充上下轨之间的区域
            path = QtGui.QPainterPath()
            path.moveTo(ix - 1, last_boll_value["upper"])
            path.lineTo(ix, boll_value["upper"])
            path.lineTo(ix, boll_value["lower"])
            path.lineTo(ix - 1, last_boll_value["lower"])
            path.closeSubpath()
            painter.setBrush(self.fill_brush)
            painter.setPen(pg.mkPen(None))  # 无边框
            painter.drawPath(path)
            
            # 绘制上轨线
            start_point = QtCore.QPointF(ix - 1, last_boll_value["upper"])
            end_point = QtCore.QPointF(ix, boll_value["upper"])
            painter.setPen(self.upper_pen)
            painter.drawLine(start_point, end_point)

            # 绘制中轨线（注释掉，和参考代码一致）
            # start_point = QtCore.QPointF(ix - 1, last_boll_value["middle"])
            # end_point = QtCore.QPointF(ix, boll_value["middle"])
            # painter.setPen(self.white_pen)
            # painter.drawLine(start_point, end_point)

            # 绘制下轨线
            start_point = QtCore.QPointF(ix - 1, last_boll_value["lower"])
            end_point = QtCore.QPointF(ix, boll_value["lower"])
            painter.setPen(self.lower_pen)
            painter.drawLine(start_point, end_point)

        # Finish
        painter.end()
        return picture

    def get_info_text(self, ix: int) -> str:
        """获取布林带信息文本，包含数值和交易指导"""
        if ix in self.boll_data:
            boll_value = self.boll_data[ix]
            text = f"BOLL({self.boll_window}) {boll_value['middle']:.1f}\n"
            text += f"UPPER: {boll_value['upper']:.1f}\n"
            text += f"LOWER: {boll_value['lower']:.1f}"
            return text
        else:
            return "BOLL数据不足"

    def clear_all(self) -> None:
        """清除所有数据"""
        super().clear_all()
        self.boll_data.clear()
        self._bar_picutures.clear()
        self.update()

    # ConfigurableIndicator接口实现
    def get_config_params(self) -> Dict:
        """返回可配置参数"""
        return {
            'boll_window': {
                'name': '布林带周期',
                'type': 'int',
                'value': self.boll_window,
                'min': 5,
                'max': 200,
                'step': 1
            },
            'std_dev': {
                'name': '标准差倍数',
                'type': 'float',
                'value': self.std_dev,
                'min': 0.5,
                'max': 3.0,
                'step': 0.1
            }
        }

    def update_config(self, config: Dict) -> None:
        """更新配置"""
        if 'boll_window' in config:
            self.boll_window = config['boll_window']
        if 'std_dev' in config:
            self.std_dev = config['std_dev']
        
        # 清空缓存，重新计算
        self.boll_data.clear()
        self.clear_all()
    
    def get_config_dialog(self, parent: QtWidgets.QWidget) -> QtWidgets.QDialog:
        """获取配置对话框"""
        config_items = [
            ("boll_window", "布林带周期", "spinbox", {"min": 5, "max": 200, "value": self.boll_window}),
            ("std_dev", "标准差倍数", "doublespinbox", {"min": 0.5, "max": 3.0, "step": 0.1, "value": self.std_dev})
        ]
        
        return self.create_config_dialog(parent, "布林带配置", config_items)
    
    def _get_config_help_text(self) -> str:
        """获取配置帮助文本"""
        return "布林带参数说明：\n• 周期越大，布林带越平滑\n• 标准差倍数越大，布林带越宽"
    
    def apply_config(self, config: Dict[str, Any]) -> None:
        """应用配置"""
        if 'boll_window' in config:
            self.boll_window = config['boll_window']
        if 'std_dev' in config:
            self.std_dev = config['std_dev']
        
        # 清空缓存，重新计算
        self.boll_data.clear()
        self.clear_all()
    
    def get_current_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return {
            'boll_window': self.boll_window,
            'std_dev': self.std_dev
        }
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'boll_window': 20,
            'std_dev': 2.0
        }