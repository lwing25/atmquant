"""
增强的回测指标计算模块
在原有回测框架基础上增加更多重要的回测指标
"""
from typing import List, Dict, Tuple
from copy import copy
import numpy as np
from pandas import DataFrame
from vnpy.trader.object import TradeData
from vnpy.trader.constant import Direction


def generate_trade_pairs(trades: List[TradeData]) -> List[Dict]:
    """
    生成交易配对，用于计算交易级别的统计指标
    """
    long_trades: List[TradeData] = []
    short_trades: List[TradeData] = []
    trade_pairs: List[Dict] = []

    for trade in trades:
        trade: TradeData = copy(trade)

        if trade.direction == Direction.LONG:
            same_direction: List[TradeData] = long_trades
            opposite_direction: List[TradeData] = short_trades
        else:
            same_direction: List[TradeData] = short_trades
            opposite_direction: List[TradeData] = long_trades

        while trade.volume and opposite_direction:
            open_trade: TradeData = opposite_direction[0]

            close_volume = min(open_trade.volume, trade.volume)
            
            # 计算持仓时间（以小时为单位）
            holding_time_hours = (trade.datetime - open_trade.datetime).total_seconds() / 3600
            
            d: Dict = {
                "open_dt": open_trade.datetime,
                "open_price": open_trade.price,
                "close_dt": trade.datetime,
                "close_price": trade.price,
                "direction": open_trade.direction,
                "volume": close_volume,
                "holding_time_hours": holding_time_hours,
            }
            trade_pairs.append(d)

            open_trade.volume -= close_volume
            if not open_trade.volume:
                opposite_direction.pop(0)

            trade.volume -= close_volume

        if trade.volume:
            same_direction.append(trade)

    return trade_pairs


def calculate_trade_statistics(trade_pairs: List[Dict], size: float) -> Dict:
    """
    计算交易级别的统计指标
    """
    if not trade_pairs:
        return {
            "win_rate": 0.0,
            "average_win_loss_ratio": 0.0,
            "optimal_position_ratio": 0.0,
            "profit_factor": 0.0,
            "average_trade": 0.0,
            "max_consecutive_wins": 0,
            "max_consecutive_losses": 0,
            "average_holding_time_days": 0.0,
            "average_holding_time_hours": 0.0,
            "max_holding_time_hours": 0.0,
            "min_holding_time_hours": 0.0,
            "median_holding_time_hours": 0.0
        }

    # 计算每笔交易的盈亏
    trade_pnls = []
    holding_times = []
    
    for pair in trade_pairs:
        if pair["direction"] == Direction.LONG:
            pnl = (pair["close_price"] - pair["open_price"]) * pair["volume"] * size
        else:
            pnl = (pair["open_price"] - pair["close_price"]) * pair["volume"] * size
        
        trade_pnls.append(pnl)
        holding_times.append(pair["holding_time_hours"])

    # 基础统计
    winning_trades = [pnl for pnl in trade_pnls if pnl > 0]
    losing_trades = [pnl for pnl in trade_pnls if pnl < 0]

    win_rate = len(winning_trades) / len(trade_pnls)
    average_win = np.mean(winning_trades) if winning_trades else 0
    average_loss = abs(np.mean(losing_trades)) if losing_trades else 0
    average_win_loss_ratio = average_win / average_loss if average_loss else 0

    # 计算凯利公式最优仓位
    optimal_position = calculate_kelly_ratio(win_rate, average_win, average_loss)

    # 计算获利因子
    total_wins = np.sum(winning_trades) if winning_trades else 0
    total_losses = abs(np.sum(losing_trades)) if losing_trades else 0
    profit_factor = total_wins / total_losses if total_losses else 0

    # 计算平均每笔交易盈亏
    average_trade = np.mean(trade_pnls)

    # 计算最大连续盈利和亏损次数
    consecutive_wins = 0
    consecutive_losses = 0
    max_consecutive_wins = 0
    max_consecutive_losses = 0

    for pnl in trade_pnls:
        if pnl > 0:
            consecutive_wins += 1
            consecutive_losses = 0
            max_consecutive_wins = max(max_consecutive_wins, consecutive_wins)
        elif pnl < 0:
            consecutive_losses += 1
            consecutive_wins = 0
            max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
    
    # 确保返回的是整数类型
    max_consecutive_wins = int(max_consecutive_wins)
    max_consecutive_losses = int(max_consecutive_losses)

    # 持仓时间统计（同时提供小时和天为单位）
    average_holding_time_hours = np.mean(holding_times) if holding_times else 0
    max_holding_time_hours = np.max(holding_times) if holding_times else 0
    min_holding_time_hours = np.min(holding_times) if holding_times else 0
    median_holding_time_hours = np.median(holding_times) if holding_times else 0
    
    # 转换为天为单位（24小时=1天）
    average_holding_time_days = average_holding_time_hours / 24
    max_holding_time_days = max_holding_time_hours / 24
    min_holding_time_days = min_holding_time_hours / 24
    median_holding_time_days = median_holding_time_hours / 24

    return {
        "win_rate": win_rate,
        "average_win_loss_ratio": average_win_loss_ratio,
        "optimal_position_ratio": optimal_position,
        "profit_factor": profit_factor,
        "average_trade": average_trade,
        "max_consecutive_wins": max_consecutive_wins,
        "max_consecutive_losses": max_consecutive_losses,
        # 小时为单位的持仓时间
        "average_holding_time_hours": average_holding_time_hours,
        "max_holding_time_hours": max_holding_time_hours,
        "min_holding_time_hours": min_holding_time_hours,
        "median_holding_time_hours": median_holding_time_hours,
        # 天为单位的持仓时间
        "average_holding_time_days": average_holding_time_days,
        "max_holding_time_days": max_holding_time_days,
        "min_holding_time_days": min_holding_time_days,
        "median_holding_time_days": median_holding_time_days
    }


def calculate_kelly_ratio(win_rate: float, average_win: float, average_loss: float) -> float:
    """计算凯利公式最优仓位"""
    if not average_loss or average_win <= 0 or win_rate <= 0:
        return 0

    p = win_rate
    q = 1 - p
    b = average_win / average_loss

    # 凯利公式计算
    f_star = (b * p - q) / b

    # 限制仓位在0-1之间
    f_star = max(0, min(1, f_star))

    # 使用半凯利仓位
    return f_star * 0.5


def calculate_advanced_metrics(daily_df: DataFrame, capital: float, risk_free: float = 0.02, annual_days: int = 240) -> Dict:
    """
    计算高级风险指标
    """
    if daily_df.empty:
        return {}

    # 计算日收益率
    daily_returns = daily_df["net_pnl"] / capital
    
    # 计算下行波动率
    mar = risk_free / annual_days  # 日度最小可接受收益率
    downside_returns = []
    for daily_return in daily_returns:
        downside_diff = daily_return - mar
        if downside_diff < 0:
            downside_returns.append(downside_diff)

    down_std = np.sqrt(np.mean(np.square(downside_returns))) if downside_returns else 0
    annual_down_std = down_std * np.sqrt(annual_days)  # 年化下行波动率

    # 计算索提诺比率
    annual_return = daily_returns.mean() * annual_days
    if annual_down_std:
        sortino_ratio = (annual_return - risk_free) / annual_down_std
    else:
        sortino_ratio = 0

    # 计算卡尔马比率
    max_ddpercent = daily_df["ddpercent"].min() if "ddpercent" in daily_df.columns else 0
    calmar_ratio = abs(annual_return * 100 / max_ddpercent) if max_ddpercent else 0

    return {
        "sortino_ratio": sortino_ratio,
        "calmar_ratio": calmar_ratio,
        "annual_down_std": annual_down_std,
    }


def calculate_monthly_statistics(trade_pairs: List[Dict], size: float) -> DataFrame:
    """
    计算月度统计数据
    """
    if not trade_pairs:
        return DataFrame()

    # 计算每笔交易的盈亏
    trade_data = []
    for pair in trade_pairs:
        if pair["direction"] == Direction.LONG:
            pnl = (pair["close_price"] - pair["open_price"]) * pair["volume"] * size
        else:
            pnl = (pair["open_price"] - pair["close_price"]) * pair["volume"] * size
        
        trade_data.append({
            "close_dt": pair["close_dt"],
            "pnl": pnl
        })

    if not trade_data:
        return DataFrame()

    # 创建DataFrame
    trade_df = DataFrame(trade_data)
    trade_df["close_dt"] = trade_df["close_dt"].dt.tz_localize(None)
    trade_df["month"] = trade_df["close_dt"].dt.to_period("M")

    # 计算每月的统计数据
    monthly_stats = trade_df.groupby("month").agg(
        total_trades=("pnl", "size"),
        win_rate=("pnl", lambda x: (x > 0).sum() / x.size if x.size > 0 else 0),
        total_pnl=("pnl", "sum")
    ).reset_index()

    # 将win_rate转换为百分比
    monthly_stats["win_rate"] = (monthly_stats["win_rate"] * 100).apply(lambda x: f"{x:.2f}%")

    return monthly_stats


def calculate_interval_statistics(trade_pairs: List[Dict], size: float) -> DataFrame:
    """
    计算每个半小时交易区间的统计数据
    """
    if not trade_pairs:
        return DataFrame()

    # 计算每笔交易的盈亏
    trade_data = []
    for pair in trade_pairs:
        if pair["direction"] == Direction.LONG:
            pnl = (pair["close_price"] - pair["open_price"]) * pair["volume"] * size
        else:
            pnl = (pair["open_price"] - pair["close_price"]) * pair["volume"] * size
        
        # 创建半小时区间标识
        open_dt = pair["open_dt"]
        interval_start = f"{open_dt.hour:02d}:{open_dt.minute // 30 * 30:02d}"
        
        trade_data.append({
            "interval_start": interval_start,
            "pnl": pnl
        })

    if not trade_data:
        return DataFrame()

    # 创建DataFrame
    trade_df = DataFrame(trade_data)

    # 按半小时区间分组计算统计数据
    interval_stats = trade_df.groupby("interval_start").agg(
        total_trades=("pnl", "size"),
        win_rate=("pnl", lambda x: (x > 0).sum() / x.size if x.size > 0 else 0),
        total_pnl=("pnl", "sum")
    ).reset_index()

    # 格式化胜率
    interval_stats["win_rate"] = (interval_stats["win_rate"] * 100).apply(lambda x: f"{x:.2f}%")

    # 按total_pnl升序排序
    interval_stats = interval_stats.sort_values(by="total_pnl", ascending=True)

    return interval_stats


def calculate_comprehensive_rating(statistics: Dict) -> float:
    """
    计算综合评分
    基于多个指标的加权平均，使用对数变换处理极端值
    """
    try:
        # 获取关键指标
        ewm_sharpe = statistics.get("ewm_sharpe", 0)
        max_ddpercent = statistics.get("max_ddpercent", 0)
        win_rate = statistics.get("win_rate", 0)
        average_win_loss_ratio = statistics.get("average_win_loss_ratio", 0)
        calmar_ratio = statistics.get("calmar_ratio", 0)
        
        # 归一化处理
        normalized_sharpe = (
            0 if ewm_sharpe <= 0
            else np.log1p(ewm_sharpe)  # 使用log1p避免极端值影响
        )

        # 最大回撤处理（越小越好）
        normalized_drawdown = 1 - min(abs(max_ddpercent) / 100, 1)  # 限制在0-1之间

        # 盈亏比处理
        normalized_winloss = (
            0 if average_win_loss_ratio <= 1
            else np.log1p(average_win_loss_ratio - 1)
        )

        # 胜率处理
        normalized_winrate = (
            0 if win_rate < 0.35  # 保留最低门槛
            else win_rate
        )

        # 卡尔马比率处理
        normalized_calmar = (
            0 if calmar_ratio <= 0
            else np.log1p(calmar_ratio)
        )

        # 综合评分
        overall_rating = (
            0.35 * normalized_sharpe +     # EWM Sharpe权重35%
            0.30 * normalized_drawdown +   # 最大回撤权重30%
            0.20 * normalized_winrate +    # 胜率权重20%
            0.10 * normalized_winloss +    # 盈亏比权重10%
            0.05 * normalized_calmar       # 卡尔马比率权重5%
        )

        return overall_rating

    except Exception:
        return 0