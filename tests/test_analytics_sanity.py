import numpy as np
import pandas as pd

from app.core.analytics import compute_metrics


def _frame(n=260, start=100.0):
    idx = pd.bdate_range('2024-01-01', periods=n)
    close = pd.Series(np.linspace(start, start + n - 1, n), index=idx)
    high = close * 1.01
    low = close * 0.99
    return pd.DataFrame({'Open': close, 'High': high, 'Low': low, 'Close': close}, index=idx)


def test_corr_and_change_in_unit_interval():
    frame = _frame()
    spy_returns = frame['Close'].pct_change()
    m = compute_metrics(frame, spy_returns)
    assert -1 <= m['corr30'] <= 1
    assert m['corr_change'] is None or -2 <= m['corr_change'] <= 2


def test_range_formula_latest_day():
    frame = _frame()
    m = compute_metrics(frame, frame['Close'].pct_change())
    expected = ((frame['High'].iloc[-1] - frame['Low'].iloc[-1]) / frame['Close'].iloc[-1]) * 100
    assert abs(m['range_1d'] - expected) < 1e-9


def test_sma200_requires_enough_history():
    short = _frame(n=120)
    m = compute_metrics(short, short['Close'].pct_change())
    assert m['dist_200dma'] is None
