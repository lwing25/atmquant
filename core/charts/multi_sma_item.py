#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多周期简单移动平均线指标 - 完全按照参考代码样式
"""

from typing import Dict, Tuple, Any
import numpy as np
import talib
from vnpy.trader.object import BarData
from vnpy.chart.item import CandleItem
from vnpy.trader.ui import QtGui, QtCore, QtWidgets
import pyqtgraph as pg

from .indicator_base import ConfigurableIndicator


class MultiSmaItem(CandleItem, ConfigurableIndicator):
    """
    绘制多条简单移动平均线(SMA)的类 - 参考原始代码样式
    """

    def __init__(self, manager, periods: Tuple[int, ...] = (5, 10, 20, 60)):
        """
        初始化
        """
        super().__init__(manager)

        self.periods = periods
        self.lines: Dict[int, QtGui.QPen] = {}  # 存储窗口大小和对应的画笔
        self.sma_data: Dict[int, Dict[int, float]] = {}  # 存储多个窗口的均线数据
        
        # 设置颜色
        colors = [
            (100, 100, 255),    # 蓝色
            (255, 255, 0),      # 黄色
            (255, 0, 255),      # 紫色
            (0, 255, 255),      # 青色
            (255, 128, 0),      # 橙色
            (128, 255, 128),    # 浅绿色
            (255, 128, 128),    # 浅红色
            (128, 128, 255),    # 浅蓝色
        ]
        
        # 为每个周期设置画笔 - 参考原始代码样式
        for i, period in enumerate(self.periods):
            color = colors[i % len(colors)]
            self.add_sma_line(period, color, 2)

    def add_sma_line(self, sma_window: int, color: Tuple[int, int, int] = (100, 100, 255), width: int = 2):
        """
        添加一条均线 - 参考原始代码样式
        """
        self.lines[sma_window] = pg.mkPen(color=color, width=width)
        self.sma_data[sma_window] = {}

    def get_sma_value(self, ix: int, sma_window: int) -> float:
        """
        获取指定窗口大小的 SMA 值 - 参考原始代码
        """
        if ix < 0:
            return np.nan

        # 计算所有 SMA 数据
        if not self.sma_data[sma_window]:
            bars = self._manager.get_all_bars()
            close_data = [bar.close_price for bar in bars]
            sma_array = talib.SMA(np.array(close_data), sma_window)

            for n, value in enumerate(sma_array):
                self.sma_data[sma_window][n] = value

        # 返回已计算值
        if ix in self.sma_data[sma_window]:
            return self.sma_data[sma_window][ix]

        # 计算新的值
        close_data = []
        for n in range(ix - sma_window + 1, ix + 1):
            bar = self._manager.get_bar(n)
            if bar is not None:  # 添加检查，确保bar不为None
                close_data.append(bar.close_price)
            else:
                # 如果bar为None，使用前一个有效值或默认值
                if close_data:
                    close_data.append(close_data[-1])  # 使用前一个值
                else:
                    close_data.append(0.0)  # 使用默认值

        sma_array = talib.SMA(np.array(close_data), sma_window)
        sma_value = sma_array[-1]
        self.sma_data[sma_window][ix] = sma_value

        return sma_value

    def _draw_bar_picture(self, ix: int, bar: BarData) -> QtGui.QPicture:
        """
        绘制K线与均线 - 完全按照参考代码样式
        """
        picture = QtGui.QPicture()
        painter = QtGui.QPainter(picture)

        for sma_window, pen in self.lines.items():
            sma_value = self.get_sma_value(ix, sma_window)
            last_sma_value = self.get_sma_value(ix - 1, sma_window)

            # 只有当前值和前一个值都有效且非NaN时才绘制线条
            if (not np.isnan(sma_value) and not np.isnan(last_sma_value) and 
                ix >= sma_window):
                
                # 设置画笔颜色
                painter.setPen(pen)

                # 绘制均线
                start_point = QtCore.QPointF(ix - 1, last_sma_value)
                end_point = QtCore.QPointF(ix, sma_value)
                painter.drawLine(start_point, end_point)

        painter.end()
        return picture

    def get_info_text(self, ix: int) -> str:
        """
        返回信息文本，显示所有 SMA 值和交易指导
        """
        info_lines = []
        sma_values = {}
        
        # 收集所有SMA值
        for sma_window, data in self.sma_data.items():
            if ix in data:
                sma_values[sma_window] = data[ix]
                info_lines.append(f"SMA({sma_window}): {data[ix]:.2f}")
        
        if not sma_values:
            return "SMA数据不足"

        # 基础信息
        text = "\n".join(info_lines)

        return text

    def clear_all(self) -> None:
        """清除所有数据"""
        super().clear_all()
        for sma_window in self.sma_data:
            self.sma_data[sma_window].clear()
        self._bar_picutures.clear()
        self.update()

    # ConfigurableIndicator接口实现
    def get_config_params(self) -> Dict:
        """返回可配置参数"""
        return {
            'periods': {
                'name': 'SMA周期组合',
                'type': 'str',
                'value': ','.join(map(str, self.periods)),
                'description': '用逗号分隔的周期，如: 5,10,20,60'
            }
        }

    def update_config(self, config: Dict) -> None:
        """更新配置"""
        if 'periods' in config:
            try:
                periods_str = config['periods']
                new_periods = tuple(int(p.strip()) for p in periods_str.split(',') if p.strip())
                if new_periods:
                    self.periods = new_periods
                    
                    # 重新设置画笔和数据
                    self.lines.clear()
                    self.sma_data.clear()
                    
                    colors = [
                        (100, 100, 255),    # 蓝色
                        (255, 255, 0),      # 黄色
                        (255, 0, 255),      # 紫色
                        (0, 255, 255),      # 青色
                        (255, 128, 0),      # 橙色
                        (128, 255, 128),    # 浅绿色
                        (255, 128, 128),    # 浅红色
                        (128, 128, 255),    # 浅蓝色
                    ]
                    
                    for i, period in enumerate(self.periods):
                        color = colors[i % len(colors)]
                        self.add_sma_line(period, color, 2)
                    
                    self.clear_all()
            except (ValueError, TypeError):
                pass  # 忽略无效输入
    
    def get_config_dialog(self, parent: QtWidgets.QWidget) -> QtWidgets.QDialog:
        """获取配置对话框"""
        periods_str = ",".join(str(p) for p in self.periods)
        config_items = [
            ("periods", "SMA周期", "lineedit", periods_str)
        ]
        
        return self.create_config_dialog(parent, "多周期SMA配置", config_items)
    
    def _get_config_help_text(self) -> str:
        """获取配置帮助文本"""
        return "SMA周期配置说明：\n• 用逗号分隔多个周期值\n• 例如：5,10,20,60\n• 支持最多8条SMA线"
    
    def apply_config(self, config: Dict[str, Any]) -> None:
        """应用配置"""
        if 'periods' in config:
            periods_value = config['periods']
            if isinstance(periods_value, str):
                # 解析逗号分隔的字符串
                try:
                    new_periods = tuple(int(p.strip()) for p in periods_value.split(',') if p.strip())
                    if new_periods:
                        self.periods = new_periods
                        
                        # 重新设置画笔和数据
                        self.lines.clear()
                        self.sma_data.clear()
                        
                        colors = [
                            (100, 100, 255),    # 蓝色
                            (255, 255, 0),      # 黄色
                            (255, 0, 255),      # 紫色
                            (0, 255, 255),      # 青色
                            (255, 128, 0),      # 橙色
                            (128, 255, 128),    # 浅绿色
                            (255, 128, 128),    # 浅红色
                            (128, 128, 255),    # 浅蓝色
                        ]
                        
                        for i, period in enumerate(self.periods):
                            color = colors[i % len(colors)]
                            self.add_sma_line(period, color, 2)
                        
                        self.clear_all()
                except (ValueError, TypeError):
                    pass  # 忽略无效输入
            elif isinstance(periods_value, (list, tuple)):
                # 直接设置周期列表
                self.periods = tuple(periods_value)
                # 重新初始化
                self.lines.clear()
                self.sma_data.clear()
                colors = [(100, 100, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
                for i, period in enumerate(self.periods):
                    color = colors[i % len(colors)]
                    self.add_sma_line(period, color, 2)
                self.clear_all()
    
    def get_current_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return {
            'periods': ",".join(str(p) for p in self.periods)
        }
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'periods': "5,10,20,60"
        }