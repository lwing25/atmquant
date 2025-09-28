#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动态数组管理器
扩展vnpy的ArrayManager，支持临时K线更新
"""

from datetime import datetime
from typing import List, Union, Tuple
import numpy as np
import talib

from vnpy.trader.utility import ArrayManager
from vnpy.trader.object import BarData


def SUM(data: np.ndarray, period: int) -> np.ndarray:
    """计算滑动窗口求和"""
    if len(data) < period:
        return np.full_like(data, np.nan)
    
    result = np.full_like(data, np.nan)
    for i in range(period - 1, len(data)):
        result[i] = np.sum(data[i - period + 1:i + 1])
    return result


def REF(data: np.ndarray, period: int) -> np.ndarray:
    """获取N周期前的数据"""
    result = np.full_like(data, np.nan)
    if period < len(data):
        result[period:] = data[:-period]
    return result


class DynaArrayManager(ArrayManager):
    """
    DynaArrayManager是对ArrayManager的扩展，解决它无法用于临时K线的指标计算问题。
    作者：hxxjava（经过适配）
    """
    
    def __init__(self, size: int = 100) -> None:
        super().__init__(size)
        self.bar_datetimes: List[datetime] = []

    def update_bar(self, bar: BarData) -> None:
        if not self.bar_datetimes or self.bar_datetimes[-1] < bar.datetime:
            self.bar_datetimes.append(bar.datetime)
            super().update_bar(bar)
        else:
            """
            Only Update all arrays in array manager with temporary bar data.
            """
            self.open_array[-1] = bar.open_price
            self.high_array[-1] = bar.high_price
            self.low_array[-1] = bar.low_price
            self.close_array[-1] = bar.close_price
            self.volume_array[-1] = bar.volume
            self.turnover_array[-1] = bar.turnover
            self.open_interest_array[-1] = bar.open_interest

    def dmi(self, N: int = 14, M: int = 7, array: bool = False) -> Union[Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray], Tuple[float, float, float, float]]:
        """
        Directional Movement Indicator:
        """
        TR = talib.TRANGE(self.high, self.low, self.close)
        TR_sum = SUM(TR, N)

        HD = self.high - REF(self.high, 1)
        LD = REF(self.low, 1) - self.low

        DMP = SUM(np.where((HD > 0) & (HD > LD), HD, 0), N)
        DMM = SUM(np.where((LD > 0) & (LD > HD), LD, 0), N)

        # 避免除零错误
        PDI = np.where(TR_sum != 0, DMP * 100 / TR_sum, 0)
        MDI = np.where(TR_sum != 0, DMM * 100 / TR_sum, 0)

        # 在计算 ADX 之前，检查数据
        denominator = MDI + PDI
        adx_input = np.where(denominator != 0, np.abs(MDI - PDI) / denominator * 100, 0)
        
        if np.all(np.isnan(adx_input)) or np.all(adx_input == 0):
            ADX = np.full_like(adx_input, np.nan)
        else:
            ADX = talib.MA(adx_input, M)
        
        ADXR = (ADX + REF(ADX, M)) / 2

        if array:
            return PDI, MDI, ADX, ADXR

        return PDI[-1], MDI[-1], ADX[-1], ADXR[-1]

    def macd3(self, fast_period: int, slow_period: int, signal_period: int, array: bool = False) -> Union[Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray], Tuple[float, float, float, float]]:
        """
        MACD having three lines:(diff,dea,slow_dea) and macd histogram
        """
        diff, dea, macd = talib.MACD(
            self.close, fast_period, slow_period, signal_period
        )
        slow_dea = talib.EMA(dea, signal_period)

        if array:
            return diff, dea, macd, slow_dea
        return diff[-1], dea[-1], macd[-1], slow_dea[-1]

    def xma(self, select: str = "C", N: int = 3, array: bool = False) -> np.ndarray:
        """XMA函数的实现"""
        if select.upper() == "C":
            src = self.close
        elif select.upper() == "O":
            src = self.open
        elif select.upper() == "H":
            src = self.high
        elif select.upper() == "L":
            src = self.low
        else:
            raise ValueError(f"Invalid select parameter: {select}")

        data_len = len(src)
        half_len: int = (N // 2) + (1 if N % 2 else 0)
        
        if data_len < half_len:
            out = np.array([np.nan for i in range(data_len)], dtype=float)
            if array:
                return out
            return out[-half_len:] if len(out) else np.array([], dtype=float)

        head = np.array([talib.MA(src[0:ilen], ilen)[-1] for ilen in range(half_len, N)])
        out = head
        
        if data_len >= N:
            body = talib.MA(src, N)[N-1:]
            out = np.append(out, body)
            tail = np.array([talib.MA(src[-ilen:], ilen)[-1] for ilen in range(N-1, half_len-1, -1)])
            out = np.append(out, tail)

        if array:
            return out

        return out[-half_len:]
