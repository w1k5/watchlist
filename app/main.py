from __future__ import annotations

import time
from collections import defaultdict, deque
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .core.analytics import analyze_ticker
from .core.cache import PriceCache
from .core.config import settings
from .core.data import StooqClient
from .core.models import TickerResult
from .core.tickers import parse_tickers

app = FastAPI(title="Watchlist Heatmap")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

cache = PriceCache(Path(settings.cache_path))
client = StooqClient(cache)

DEFAULT_TEXT = """Ticker
GLD
QACDS
VAW
IBIT
"""

# Simple in-memory rate limiter per client IP.
request_windows: dict[str, deque[float]] = defaultdict(deque)


def _client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    if request.client is not None:
        return request.client.host
    return "unknown"


def _enforce_rate_limit(request: Request) -> None:
    limit = max(settings.requests_per_minute, 1)
    now = time.monotonic()
    window_start = now - 60
    ip = _client_ip(request)

    hits = request_windows[ip]
    while hits and hits[0] < window_start:
        hits.popleft()

    if len(hits) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please wait and try again.",
        )

    hits.append(now)


def _enforce_access_token(request: Request, token: str | None) -> None:
    expected = settings.app_access_token
    if not expected:
        return

    provided = token or request.headers.get("x-access-token")
    if provided != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized. Provide a valid access token.",
        )


def _enforce_request_guards(request: Request, token: str | None) -> None:
    _enforce_rate_limit(request)
    _enforce_access_token(request, token)


def run_analysis(tickers_input: str) -> list[TickerResult]:
    tickers = parse_tickers(tickers_input)
    results: list[TickerResult] = []

    spy_frame, _, _ = client.fetch("SPY")
    spy_returns = spy_frame["Close"].pct_change() if spy_frame is not None else None

    for ticker in tickers:
        frame, resolved_symbol, reason = client.fetch(ticker)
        if frame is None:
            results.append(TickerResult(ticker=ticker, reason=reason or "Unavailable"))
            continue

        analyzed = analyze_ticker(ticker, frame, spy_returns)
        if resolved_symbol and resolved_symbol.lower() != ticker.lower():
            analyzed.notes.append(f"Source symbol: {resolved_symbol}")
        results.append(analyzed)

    return results


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "raw_input": DEFAULT_TEXT,
            "results": None,
            "token_required": bool(settings.app_access_token),
            "token": "",
        },
    )


@app.post("/run", response_class=HTMLResponse)
async def run(request: Request, tickers_input: str = Form(...), token: str = Form("")) -> HTMLResponse:
    _enforce_request_guards(request, token)
    return templates.TemplateResponse(
        "results.html",
        {
            "request": request,
            "raw_input": tickers_input,
            "results": run_analysis(tickers_input),
            "token_required": bool(settings.app_access_token),
            "token": token,
        },
    )


@app.post("/api/run")
async def api_run(
    request: Request,
    tickers_input: str = Form(...),
    token: str = Form(""),
) -> dict[str, list[dict[str, object]]]:
    _enforce_request_guards(request, token)
    results = run_analysis(tickers_input)
    return {
        "results": [
            {
                "ticker": row.ticker,
                "status": row.status,
                "reason": row.reason,
                "metrics": row.metrics,
                "notes": row.notes,
                "attention": row.attention_text,
            }
            for row in results
        ]
    }
