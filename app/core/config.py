from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    stooq_base_url: str = "https://stooq.com/q/d/l/"
    cache_path: Path = Path("data/cache.sqlite3")
    lookback_days: int = 5 * 365
    percentile_window_days: int = 3 * 365
    big_move_threshold_pct: float = 2.0
    vol_spike_percentile: float = 90.0
    range_spike_percentile: float = 95.0
    extreme_range_percentile: float = 98.0
    diversifier_corr_threshold: float = 0.6
    diversifier_corr_change_threshold: float = 0.2


settings = Settings()
