# Watchlist Heatmap / Attention Numbers

A small FastAPI app that lets you paste a column of tickers and get a daily-close “attention” dashboard:

- returns (1D / 5D / 21D)
- distance to 200DMA
- 20D realized vol + percentile
- 1D range + percentile
- 30D correlation to SPY + correlation change
- attention notes and severity labels (`NORMAL`, `WATCH`, `ATTENTION`, `STRESS`)

The app uses **Stooq** daily OHLC data and handles unavailable symbols without breaking the whole run.

---

## 1) Prerequisites

- Python 3.11+ recommended
- internet access for fetching Stooq data

> If your environment uses a proxy, ensure `pip` and runtime HTTPS requests can reach package indexes / Stooq.

---

## 2) Local setup

### Option A: Python virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the app:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 10000 --reload
```

Open:

- http://localhost:10000

### Option B: Docker

Build:

```bash
docker build -t watchlist-heatmap .
```

Run:

```bash
docker run --rm -p 10000:10000 watchlist-heatmap
```

Open:

- http://localhost:10000

---

## 3) How to use

Paste a list like:

```text
Ticker
GLD
QACDS
VAW
IBIT
```

Click **Run**.

You’ll get:

- a metrics table
- a status badge per ticker
- an “Attention” explanation for what changed and why it matters
- clear “Unavailable” handling for symbols that cannot be resolved from Stooq

---

## 4) API usage

`POST /api/run` accepts form data (`tickers_input`) and returns JSON.

Example:

```bash
curl -X POST http://localhost:10000/api/run \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode $'tickers_input=Ticker\nGLD\nVAW\nIBIT'
```

---

## 5) Data + caching behavior

- Source: `https://stooq.com/q/d/l/?s=<symbol>&i=d`
- The app tries normalized symbol variants (`ticker`, `ticker.us`)
- Daily CSV responses are cached in local SQLite (`data/cache.sqlite3`)
- If a fetch fails, the app can fall back to latest cached data

---

## 6) Render deployment

This repo includes:

- `Dockerfile`
- `render.yaml`

### Quick path

1. Push repo to GitHub.
2. In Render, create a new **Web Service** from this repo.
3. Use Docker environment (or let `render.yaml` configure it).
4. Start command is already handled by Docker CMD:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 10000
```

---

## 7) Project structure

```text
app/
  main.py
  core/
    analytics.py
    cache.py
    config.py
    data.py
    models.py
    tickers.py
  templates/
    index.html
    results.html
  static/
    styles.css
requirements.txt
Dockerfile
render.yaml
```

---

## 8) Known limitations (V1)

With Stooq-only coverage:

- ETFs/stocks/ADRs: generally good
- mutual funds and bespoke/private symbols: may be unavailable

Unavailable symbols are reported in-row so the whole analysis still completes.
