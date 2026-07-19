# Restructuring Screener

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An **event-driven Corporate Restructuring Screener** that tracks and surfaces restructuring situations — bankruptcies, spin-offs, asset sales, debt restructurings/LMEs, strategic reviews, covenant events, distressed financings, going-concern warnings, turnaround management changes, and activist campaigns.

Every company carries three explainable **0–100 scores** — Distress, Restructuring Significance, and Turnaround Opportunity — recomputed whenever ingestion touches it.

---

## Live Demo

> GitHub Pages landing page: [https://grisheet.github.io/restructuring-screener](https://grisheet.github.io/restructuring-screener)

---

## Features

- **Explainable Scoring Engine** — Distress (leverage + liquidity + covenant stress), Restructuring Significance (event severity + breadth), and Turnaround Opportunity (stabilisation curve + management quality) scores with per-factor breakdowns
- **Event-Driven Pipeline** — idempotent ingestion, deduplication, and automated alerting
- **Layered FastAPI** — routes → Pydantic schemas → services → repositories (SQLAlchemy 2.0)
- **PostgreSQL 16** — 10-table schema, reproducible backtesting, materialized score history
- **Group-by Screening** — company-centric view nesting all catalysts under a single ticker
- **Docker Compose** — one-command local stack (Postgres 16 + API)
- **Test Suite** — 12 scenarios covering idempotency, regression, and data integrity

---

## Project Structure

```
restructuring-screener/
├── app/
│   ├── main.py                  # FastAPI application factory
│   ├── config.py                # Settings via pydantic-settings
│   ├── database/
│   │   ├── session.py           # SQLAlchemy engine + session (sync)
│   │   └── base.py              # Declarative base
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── company.py
│   │   ├── event.py
│   │   ├── score.py
│   │   ├── watchlist.py
│   │   └── screen.py
│   ├── schemas/                 # Pydantic v2 request/response schemas
│   │   ├── company.py
│   │   ├── event.py
│   │   ├── score.py
│   │   ├── watchlist.py
│   │   └── screen.py
│   ├── repositories/            # Data access layer
│   │   ├── company_repo.py
│   │   ├── event_repo.py
│   │   ├── score_repo.py
│   │   └── watchlist_repo.py
│   ├── services/                # Business logic
│   │   ├── scoring.py           # Scoring engine
│   │   ├── ingestion.py         # Pipeline + connectors
│   │   ├── screening.py         # Screen execution
│   │   └── alerting.py          # Alert dispatch
│   └── routers/                 # FastAPI route handlers
│       ├── companies.py
│       ├── events.py
│       ├── screens.py
│       ├── watchlists.py
│       └── health.py
├── scripts/
│   ├── seed.py                  # Seed database with sample data
│   └── create_tables.py         # Bootstrap schema
├── tests/
│   ├── conftest.py
│   ├── test_scoring.py
│   ├── test_ingestion.py
│   ├── test_screening.py
│   └── test_api.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

---

## Scoring Model

| Score | Range | What It Measures |
|-------|-------|------------------|
| **Distress** | 0–100 | Leverage, liquidity, covenant stress, going-concern flags |
| **Restructuring Significance** | 0–100 | Event severity, breadth of restructuring, creditor impact |
| **Turnaround Opportunity** | 0–100 | Stabilisation curve, mgmt quality, asset coverage |

Scores are designed to **separate** — a terminal Chapter 11 case scores high on Distress but low on Turnaround Opportunity, while a stressed-but-alive LME candidate scores high on both.

---

## Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 16 (or use Docker)

### 1. Clone the repository

```bash
git clone https://github.com/grisheet/restructuring-screener.git
cd restructuring-screener
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your database credentials
```

### 3. Start with Docker Compose

```bash
docker compose up -d
```

### 4. Initialize the database

```bash
pip install -r requirements.txt
python -m scripts.create_tables
python -m scripts.seed
```

### 5. Run the API

```bash
uvicorn app.main:app --reload --port 8000
```

Visit [http://localhost:8000/docs](http://localhost:8000/docs) for the interactive Swagger UI.

---

## API Endpoints

### Health
- `GET /health` — Health check with DB connectivity

### Companies
- `GET /companies` — List all companies (with optional filters)
- `GET /companies/{ticker}` — Company detail with score breakdown
- `POST /companies` — Create a company record
- `PATCH /companies/{ticker}` — Update company fundamentals

### Events
- `GET /events` — List events (filter by type, date, ticker)
- `POST /events` — Ingest a new restructuring event
- `GET /events/{id}` — Event detail

### Screens
- `POST /screens/run` — Execute a screen with filters + group_by
- `GET /screens` — List saved screens
- `POST /screens` — Save a screen configuration

### Watchlists
- `GET /watchlists` — List watchlists
- `POST /watchlists` — Create a watchlist
- `POST /watchlists/{id}/companies` — Add company to watchlist

---

## Sample Screen Request

```json
POST /screens/run
{
  "filters": {
    "distress_min": 60,
    "turnaround_min": 40,
    "event_types": ["chapter11", "lme", "debt_restructuring"]
  },
  "group_by": "company",
  "sort_by": "distress_score",
  "sort_order": "desc"
}
```

---

## Running Tests

```bash
pytest tests/ -v
```

All 12 test scenarios cover:
- Idempotent ingestion (duplicate events are deduplicated)
- Score recomputation on new events
- Group-by screening output shape
- API endpoint contract tests
- Data integrity regression tests

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| API Framework | FastAPI 0.110+ |
| ORM | SQLAlchemy 2.0 (sync) |
| Database | PostgreSQL 16 |
| Validation | Pydantic v2 |
| Testing | pytest + httpx TestClient |
| Containerization | Docker + Docker Compose |
| Migrations | Alembic (optional; `create_all` for bootstrap) |

---

## Architecture Notes

- **Sync sessions**: Chosen over async for simplicity; documented trade-offs in `session.py`
- **Connector Protocol**: `ingestion.py` uses a `Protocol` interface for data connectors, making it easy to swap `MockConnector` for real data sources (Bloomberg, Refinitiv, etc.)
- **Score Materialization**: Scores are stored and versioned — enabling reproducible backtesting and historical drift analysis
- **Enrich-only semantics**: Thin-payload sources cannot overwrite established company names or fundamentals, preventing data corruption

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Author

Built as a full-stack MVP demonstrating event-driven financial screening with explainable AI scoring.
