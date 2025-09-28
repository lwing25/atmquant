#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DMI方向性运动指标
基于vnpy ChartItem实现的DMI技术指标
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
from .dyna_array_manager import DynaArrayManager


class DmiItem(ChartItem, ConfigurableIndicator):
    """
    DMI方向性运动指标
    参考原始代码风格，支持参数配置
    """
    
    def __init__(self, manager: BarManager, N: int = 14, M: int = 7):
        """初始化DMI指标"""
        super().__init__(manager)
        
        # 参数设置
        self.N = N
        self.M = M
        
        # 颜色配置
        self.white_pen: QtGui.QPen = pg.mkPen(color=(255, 255, 255), width=1)
        self.yellow_pen: QtGui.QPen = pg.mkPen(color=(255, 255, 0), width=1)
        self.magenta_pen: QtGui.QPen = pg.mkPen(color=(255, 0, 255), width=1)
        self.red_pen: QtGui.QPen = pg.mkPen(color=(255, 0, 0), width=1)
        self.green_pen: QtGui.QPen = pg.mkPen(color=(0, 255, 0), width=1)
        self.ref_pen: QtGui.QPen = pg.mkPen(color=(127, 127, 127, 127), width=1, style=QtCore.Qt.DashLine)
        
        # 缓存设置
        self._values_ranges: Dict[Tuple[int, int], Tuple[float, float]] = {}
        
        # 动态数组管理器
        self.dyna_am = DynaArrayManager(2*max(N, M))
        
        # 数据缓存
        self.dmi_data: Dict[int, Tuple[float, float, float, float]] = {}  # (PDI,MDI,ADX,ADXR)
        self._to_update = True  # 标记需要更新

    def update_history(self, history) -> None:
        """重写update_history方法"""
        self.dmi_data.clear()  # 清除旧数据
        self.dyna_am = DynaArrayManager(2*max(self.N, self.M))  # 重新初始化
        for bar in history:
            self.dyna_am.update_bar(bar)
        super().update_history(history)
        self._to_update = True  # 标记需要更新

    def update_bar(self, bar: BarData) -> None:
        """重写update_bar方法"""
        self.dyna_am.update_bar(bar)
        # 主动触发最新值的计算
        if self.dyna_am.inited:
            ix = len(self._manager._bars) - 1
            try:
                pdi, mdi, adx, adxr = self.dyna_am.dmi(N=self.N, M=self.M)
                self.dmi_data[ix] = (pdi, mdi, adx, adxr)
            except:
                pass
            self._to_update = True  # 标记需要更新
        super().update_bar(bar)

    def _get_dmi_value(self, ix: int) -> Tuple[float, float, float, float]:
        """获取指定索引的 DMI 值"""
        max_ix = self._manager.get_count()-1
        invalid_data = (np.nan, np.nan, np.nan, np.nan)
        
        # 检查索引有效性
        if ix < 0 or ix > max_ix:
            return invalid_data

        # 初始化计算所有值 - 确保在任何情况下都会重新计算所有值
        if not self.dmi_data or self._to_update:
            bars = self._manager.get_all_bars()
            if not bars or len(bars) < self.N + self.M:
                return invalid_data
                
            highs = np.array([bar.high_price for bar in bars])
            lows = np.array([bar.low_price for bar in bars])
            closes = np.array([bar.close_price for bar in bars])
            
            # 使用talib计算DMI指标
            try:
                pdi = talib.PLUS_DI(highs, lows, closes, timeperiod=self.N)
                mdi = talib.MINUS_DI(highs, lows, closes, timeperiod=self.N)
                adx = talib.ADX(highs, lows, closes, timeperiod=self.N)
                adxr = talib.ADXR(highs, lows, closes, timeperiod=self.M)

                for n in range(len(adx)):
                    if not (np.isnan(pdi[n]) or np.isnan(mdi[n]) or np.isnan(adx[n]) or np.isnan(adxr[n])):
                        self.dmi_data[n] = (pdi[n], mdi[n], adx[n], adxr[n])
            except Exception as e:
                print(f"DMI计算错误: {str(e)}")
            
            self._to_update = False  # 重置更新标记

        # 返回已计算的值
        if ix in self.dmi_data:
            return self.dmi_data[ix]

        # 对于新的K线，使用动态计算
        if self.dyna_am.inited:
            try:
                pdi, mdi, adx, adxr = self.dyna_am.dmi(N=self.N, M=self.M)
                # 确保返回tuple类型
                dmi_value = (pdi, mdi, adx, adxr)
                self.dmi_data[ix] = dmi_value
                return dmi_value
            except:
                pass

        return invalid_data

    def _draw_bar_picture(self, ix: int, bar: BarData) -> QtGui.QPicture:
        """绘制DMI"""
        # 创建绘图对象
        picture = QtGui.QPicture()
        painter = QtGui.QPainter(picture)

        if ix > self.N + self.M:
            # 画参考线
            painter.setPen(self.ref_pen)
            for ref in [20.0, 50, 80]:
                painter.drawLine(QtCore.QPointF(ix-0.5, ref), QtCore.QPointF(ix+0.5, ref))

            # 画4根线
            dmi_value = self._get_dmi_value(ix)
            last_dmi_value = self._get_dmi_value(ix - 1)
            
            # 确保获取了有效的DMI值
            if np.isnan(dmi_value[0]) or np.isnan(last_dmi_value[0]):
                # 如果无效，尝试重新计算整个数据集
                self._to_update = True
                dmi_value = self._get_dmi_value(ix)
                last_dmi_value = self._get_dmi_value(ix - 1)
            
            pens = [self.white_pen, self.yellow_pen, self.magenta_pen, self.green_pen]
            for i in range(4):
                if np.isnan(dmi_value[i]) or np.isnan(last_dmi_value[i]):
                    continue
                end_point0 = QtCore.QPointF(ix, dmi_value[i])
                start_point0 = QtCore.QPointF(ix - 1, last_dmi_value[i])
                painter.setPen(pens[i])
                painter.drawLine(start_point0, end_point0)

            # 多空颜色标示
            pdi, mdi = dmi_value[0], dmi_value[1]
            if not(np.isnan(pdi) or np.isnan(mdi)):
                if abs(pdi - mdi) > 1e-2:
                    painter.setPen(pg.mkPen(color=(168, 0, 0) if pdi > mdi else (0, 168, 0), width=3))
                    painter.drawLine(QtCore.QPointF(ix, pdi), QtCore.QPointF(ix, mdi))

        painter.end()
        return picture

    def boundingRect(self) -> QtCore.QRectF:
        """返回边界矩形"""
        min_y, max_y = self.get_y_range()
        rect = QtCore.QRectF(
            0,
            min_y,
            len(self._bar_picutures),
            max_y - min_y
        )
        return rect

    def get_y_range(self, min_ix: int = None, max_ix: int = None) -> Tuple[float, float]:
        """获取Y轴范围"""
        return (0.0, 100.0)  # DMI指标范围固定为0-100

    def get_info_text(self, ix: int) -> str:
        """获取DMI信息文本，包含数值和交易指导"""
        if ix in self.dmi_data:
            pdi, mdi, adx, adxr = self.dmi_data[ix]
            
            # 基础信息
            words = [
                f"DMI({self.N},{self.M}):",
                f"PDI: {pdi:.2f}",
                f"MDI: {mdi:.2f}",
                f"ADX: {adx:.2f}",
                f"ADXR: {adxr:.2f}",
            ]
            
            # 添加状态信息
            if pdi > mdi:
                words.append("趋势: 多头")
            elif mdi > pdi:
                words.append("趋势: 空头")
            else:
                words.append("趋势: 平衡")
            
            return "\n".join(words)
        
        return f"DMI({self.N},{self.M})"
    
    def clear_all(self) -> None:
        """清除所有数据"""
        super().clear_all()
        self.dmi_data.clear()
        self._bar_picutures.clear()
        self.dyna_am = DynaArrayManager(2*max(self.N, self.M))
        self._to_update = True  # 标记需要更新
        self.update()

    # 配置相关方法
    def get_config_dialog(self, parent: QtWidgets.QWidget) -> QtWidgets.QDialog:
        """获取配置对话框"""
        config_items = [
            ("N", "PDI/MDI周期", "spinbox", {"min": 5, "max": 50, "value": self.N}),
            ("M", "ADX/ADXR周期", "spinbox", {"min": 3, "max": 30, "value": self.M})
        ]
        return self.create_config_dialog(parent, "DMI配置", config_items)

    def apply_config(self, config: Dict[str, Any]) -> None:
        """应用配置"""
        self.N = config.get('N', self.N)
        self.M = config.get('M', self.M)
        
        # 重新初始化
        self.dmi_data.clear()
        self._values_ranges.clear()
        self.dyna_am = DynaArrayManager(2*max(self.N, self.M))
        self._to_update = True
        self.update()

    def get_current_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return {'N': self.N, 'M': self.M}

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {'N': 14, 'M': 7}

    def _get_config_help_text(self) -> str:
        """获取配置帮助文本"""
        return """
参数说明：
• PDI/MDI周期: 正负方向指标的计算周期(建议14)
• ADX/ADXR周期: 平均趋向指标的计算周期(建议7)

颜色说明：
• 白色线: PDI(正方向指标)
• 黄色线: MDI(负方向指标)
• 紫色线: ADX(平均趋向指标)
• 绿色线: ADXR(趋向平均值)
• 红/绿连线: PDI与MDI的强弱关系
        """
