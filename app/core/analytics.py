from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .config import settings
from .models import TickerResult


def _pct_rank(series: pd.Series, value: float) -> float | None:
    cleaned = series.dropna()
    if cleaned.empty or math.isnan(value):
        return None
    return float((cleaned <= value).mean() * 100)


def _format_metric(value: float | None, digits: int = 2) -> str:
    if value is None or (isinstance(value, float) and (math.isnan(value) or math.isinf(value))):
        return "—"
    return f"{value:.{digits}f}"


def compute_metrics(frame: pd.DataFrame, spy_returns: pd.Series | None) -> dict[str, float | None]:
    close = frame["Close"]
    high = frame["High"]
    low = frame["Low"]

    returns = close.pct_change()
    ret_1d = returns.iloc[-1] * 100 if len(returns) > 1 else None
    ret_5d = (close.iloc[-1] / close.iloc[-6] - 1) * 100 if len(close) > 5 else None
    ret_21d = (close.iloc[-1] / close.iloc[-22] - 1) * 100 if len(close) > 21 else None

    sma200 = close.rolling(200).mean()
    dist_200dma = (close.iloc[-1] / sma200.iloc[-1] - 1) * 100 if pd.notna(sma200.iloc[-1]) else None

    vol20 = returns.rolling(20).std() * np.sqrt(252) * 100
    vol20_latest = vol20.iloc[-1] if len(vol20) else None
    vol_window = vol20.iloc[-settings.percentile_window_days :]
    vol_pctile = _pct_rank(vol_window, vol20_latest) if vol20_latest is not None else None

    true_range_pct = ((high - low) / close) * 100
    tr_latest = true_range_pct.iloc[-1] if len(true_range_pct) else None
    tr_window = true_range_pct.iloc[-settings.percentile_window_days :]
    tr_pctile = _pct_rank(tr_window, tr_latest) if tr_latest is not None else None

    corr30 = None
    corr_change = None
    if spy_returns is not None:
        aligned = pd.concat([returns.rename("asset"), spy_returns.rename("spy")], axis=1).dropna()
        if len(aligned) >= 30:
            rolling_corr = aligned["asset"].rolling(30).corr(aligned["spy"]).dropna()
            if not rolling_corr.empty:
                corr30 = rolling_corr.iloc[-1]
            if len(rolling_corr) > 30:
                corr_change = rolling_corr.iloc[-1] - rolling_corr.iloc[-31]

    crossed_200dma = False
    if len(close) >= 205:
        above = close > sma200
        recent = above.iloc[-5:]
        crossed_200dma = bool((not recent.iloc[-1]) and recent.iloc[:-1].any())

    return {
        "ret_1d": ret_1d,
        "ret_5d": ret_5d,
        "ret_21d": ret_21d,
        "dist_200dma": dist_200dma,
        "vol20": vol20_latest,
        "vol_pctile": vol_pctile,
        "range_1d": tr_latest,
        "range_pctile": tr_pctile,
        "corr30": corr30 * 100 if corr30 is not None and not pd.isna(corr30) else None,
        "corr_change": corr_change * 100 if corr_change is not None and not pd.isna(corr_change) else None,
        "crossed_below_200dma": crossed_200dma,
    }


def attention_for(metrics: dict[str, float | None]) -> tuple[str, list[str]]:
    notes: list[str] = []

    ret_1d = metrics.get("ret_1d")
    range_pctile = metrics.get("range_pctile")
    vol_pctile = metrics.get("vol_pctile")
    corr30 = metrics.get("corr30")
    corr_change = metrics.get("corr_change")

    if ret_1d is not None and abs(ret_1d) >= settings.big_move_threshold_pct:
        notes.append(f"Big move ({ret_1d:.2f}%) — price shock vs normal daily drift")

    if range_pctile is not None and range_pctile >= settings.range_spike_percentile:
        notes.append(f"Range spike ({range_pctile:.1f}th pct) — intraday stress/liquidity deterioration")

    if vol_pctile is not None and vol_pctile >= settings.vol_spike_percentile:
        notes.append(f"Vol rising ({vol_pctile:.1f}th pct) — noise is elevated; size risk carefully")

    if metrics.get("crossed_below_200dma"):
        notes.append("Lost 200DMA — trend support weakened in the last week")

    if (
        corr30 is not None
        and corr_change is not None
        and (corr30 / 100) >= settings.diversifier_corr_threshold
        and (corr_change / 100) >= settings.diversifier_corr_change_threshold
    ):
        notes.append("Diversifier behaving risk-on — hedge may fail when needed")

    if not notes:
        return "NORMAL", notes

    extreme = range_pctile is not None and range_pctile >= settings.extreme_range_percentile
    if len(notes) >= 3:
        return "STRESS", notes
    if len(notes) >= 2 or extreme:
        return "ATTENTION", notes
    return "WATCH", notes


def analyze_ticker(ticker: str, frame: pd.DataFrame, spy_returns: pd.Series | None) -> TickerResult:
    metrics = compute_metrics(frame, spy_returns)
    status, notes = attention_for(metrics)
    pretty_metrics = {
        "1D %": _format_metric(metrics["ret_1d"]),
        "5D %": _format_metric(metrics["ret_5d"]),
        "21D %": _format_metric(metrics["ret_21d"]),
        "Dist 200DMA %": _format_metric(metrics["dist_200dma"]),
        "Vol20 %": _format_metric(metrics["vol20"]),
        "Vol pctile": _format_metric(metrics["vol_pctile"], 1),
        "Range 1D %": _format_metric(metrics["range_1d"]),
        "Range pctile": _format_metric(metrics["range_pctile"], 1),
        "Corr30 to SPY": _format_metric(metrics["corr30"]),
        "Corr change": _format_metric(metrics["corr_change"]),
    }
    return TickerResult(ticker=ticker, status=status, notes=notes, metrics=pretty_metrics)
