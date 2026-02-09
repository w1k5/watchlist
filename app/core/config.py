from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


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

    # Security / abuse controls
    app_access_token: str = field(default_factory=lambda: os.getenv("APP_ACCESS_TOKEN", ""))
    requests_per_minute: int = field(default_factory=lambda: _env_int("REQUESTS_PER_MINUTE", 12))


settings = Settings()
