from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Form, Request
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
        {"request": request, "raw_input": DEFAULT_TEXT, "results": None},
    )


@app.post("/run", response_class=HTMLResponse)
async def run(request: Request, tickers_input: str = Form(...)) -> HTMLResponse:
    return templates.TemplateResponse(
        "results.html",
        {
            "request": request,
            "raw_input": tickers_input,
            "results": run_analysis(tickers_input),
        },
    )


@app.post("/api/run")
async def api_run(tickers_input: str = Form(...)) -> dict[str, list[dict[str, object]]]:
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
