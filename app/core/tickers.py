from __future__ import annotations

from collections import OrderedDict


def parse_tickers(raw_text: str) -> list[str]:
    seen: OrderedDict[str, None] = OrderedDict()
    for line in raw_text.splitlines():
        cleaned = line.strip()
        if not cleaned:
            continue
        if cleaned.lower() == "ticker":
            continue
        normalized = cleaned.upper()
        if normalized not in seen:
            seen[normalized] = None
    return list(seen.keys())


def stooq_candidates(ticker: str) -> list[str]:
    stripped = ticker.strip().lower()
    if not stripped:
        return []

    candidates = [stripped]
    if "." not in stripped:
        candidates.append(f"{stripped}.us")
    return list(OrderedDict((c, None) for c in candidates).keys())
