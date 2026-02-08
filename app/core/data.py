from __future__ import annotations

from io import StringIO

import pandas as pd
import requests

from .cache import PriceCache
from .config import settings
from .tickers import stooq_candidates


class StooqClient:
    def __init__(self, cache: PriceCache) -> None:
        self.cache = cache

    def _download_csv(self, symbol: str) -> str | None:
        params = {"s": symbol, "i": "d"}
        response = requests.get(settings.stooq_base_url, params=params, timeout=20)
        if response.status_code != 200:
            return None
        text = response.text.strip()
        if not text or "No data" in text:
            return None
        return text

    def fetch(self, ticker: str) -> tuple[pd.DataFrame | None, str | None, str | None]:
        """Returns dataframe, resolved symbol, and error reason."""
        for symbol in stooq_candidates(ticker):
            cached_today = self.cache.get_today(symbol)
            csv_blob = cached_today
            if csv_blob is None:
                try:
                    csv_blob = self._download_csv(symbol)
                    if csv_blob:
                        self.cache.set_today(symbol, csv_blob)
                except requests.RequestException:
                    csv_blob = self.cache.get_latest(symbol)

            if not csv_blob:
                continue

            try:
                frame = pd.read_csv(StringIO(csv_blob))
            except Exception:
                continue

            required = {"Date", "Open", "High", "Low", "Close"}
            if frame.empty or not required.issubset(frame.columns):
                continue

            frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce")
            frame = frame.dropna(subset=["Date"]).sort_values("Date").set_index("Date")
            frame = frame.apply(pd.to_numeric, errors="coerce").dropna(subset=["Close", "High", "Low"])
            if frame.empty:
                continue
            return frame, symbol, None

        return None, None, "No Stooq data found for ticker"
