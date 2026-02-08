from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TickerResult:
    ticker: str
    status: str = "UNAVAILABLE"
    notes: list[str] = field(default_factory=list)
    reason: str | None = None
    metrics: dict[str, Any] = field(default_factory=dict)

    @property
    def attention_text(self) -> str:
        if self.reason:
            return self.reason
        if self.notes:
            return " | ".join(self.notes)
        return "No notable flags"
