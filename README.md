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
REQUESTS_PER_MINUTE=12 APP_ACCESS_TOKEN=change-me uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

Open:

- http://localhost:8080

### Option B: Docker

Build:

```bash
docker build -t watchlist-heatmap .
```

Run:

```bash
docker run --rm -p 8080:8080 -e REQUESTS_PER_MINUTE=12 -e APP_ACCESS_TOKEN=change-me watchlist-heatmap
```

Open:

- http://localhost:8080

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

Rate limiting and optional access token protection apply to both `/run` and `/api/run`.

Example:

```bash
curl -X POST http://localhost:8080/api/run \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "X-Access-Token: change-me" \
  --data-urlencode $'tickers_input=Ticker\nGLD\nVAW\nIBIT'
```

---

## 5) Data + caching behavior

- Source: `https://stooq.com/q/d/l/?s=<symbol>&i=d`
- The app tries normalized symbol variants (`ticker`, `ticker.us`)
- Daily CSV responses are cached in local SQLite (`data/cache.sqlite3`)
- If a fetch fails, the app can fall back to latest cached data

---

## 6) Google Cloud Run deployment

This repo includes:

- `Dockerfile` (Cloud Run-compatible by honoring the `$PORT` environment variable)
- `cloudrun.yaml` (optional service manifest)

### Quick path

1. Authenticate and set your project:

```bash
gcloud auth login
gcloud config set project YOUR_GCP_PROJECT_ID
```

2. Enable required APIs:

```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
```

3. Deploy directly from source:

```bash
gcloud run deploy watchlist-heatmap \
  --source . \
  --region us-central1 \
  --no-allow-unauthenticated \
  --set-env-vars REQUESTS_PER_MINUTE=12,APP_ACCESS_TOKEN=change-me
```

Cloud Run sets `PORT` automatically (typically `8080`), and the container startup command already uses it.

Use IAM + `APP_ACCESS_TOKEN` to avoid exposing unthrottled public endpoints.

### Optional: deploy with manifest

If you prefer a declarative service definition:

```bash
gcloud run services replace cloudrun.yaml --region us-central1
```

---

## 7) Security defaults

- Requests are rate-limited in-app per client IP (default: `12` per minute).
- Set `REQUESTS_PER_MINUTE` to tune throttling for your use case.
- Set `APP_ACCESS_TOKEN` to require a secret token for `/run` and `/api/run`.
- For Cloud Run, keep `--no-allow-unauthenticated` unless you intentionally need public access.

---

## 8) Project structure

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
cloudrun.yaml
```

---

## 9) Known limitations (V1)

With Stooq-only coverage:

- ETFs/stocks/ADRs: generally good
- mutual funds and bespoke/private symbols: may be unavailable

Unavailable symbols are reported in-row so the whole analysis still completes.
