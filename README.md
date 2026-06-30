# Weather ETL Pipeline

ETL pipeline that extracts real-time weather data from the **Open-Meteo API**, transforms it with **pandas**, and loads it into **PostgreSQL**. Fully containerized with Docker and tested with Pytest.

## Architecture

```
Extract → Transform → Load
   ↓           ↓         ↓
Open-Meteo   pandas   PostgreSQL
   API       + numpy   (Docker)
```

## Tech Stack

- **Python 3.13** — Core language
- **requests** — HTTP calls to Open-Meteo API
- **pandas** — Data transformation and enrichment
- **SQLAlchemy** — ORM and database abstraction
- **PostgreSQL** — Production storage (SQLite for local/testing)
- **Docker & Docker Compose** — Containerized deployment
- **Pytest + pytest-mock** — Unit and integration testing

## Project Structure

```
data-pipeline/
├── pipeline/
│   ├── extract.py      # Fetch weather data from Open-Meteo API
│   ├── transform.py    # Clean, normalize and enrich data with pandas
│   ├── load.py         # Insert into PostgreSQL with deduplication
│   └── runner.py       # ETL orchestrator with logging
├── tests/
│   ├── test_extract.py    # API mock tests (5 tests)
│   ├── test_transform.py  # Transformation tests (15 tests)
│   └── test_load.py       # DB insertion tests (5 tests)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt        # Production dependencies
└── requirements-dev.txt    # Local development dependencies
```

## What the Pipeline Does

1. **Extract** — Calls the Open-Meteo API for 4 Spanish cities (Madrid, Sevilla, Barcelona, Valencia), fetching hourly: temperature, humidity, wind speed, precipitation, weather code.

2. **Transform** — Cleans the raw data, converts types, drops rows with null temperatures, maps WMO weather codes to human-readable descriptions, and classifies temperature into categories (freezing / cold / cool / comfortable / warm / hot).

3. **Load** — Inserts transformed records into `weather_hourly` table using `INSERT OR IGNORE` to silently skip duplicate `(city, timestamp)` pairs.

## Getting Started

### Option 1 — Docker (recommended)

```bash
docker-compose up --build
```

Spins up PostgreSQL + pipeline container. The pipeline runs once and exits cleanly.

### Option 2 — Local development

**Requirements:** Python 3.13+

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux/Mac

pip install -r requirements-dev.txt
python -m pipeline.runner
```

Uses SQLite by default — no PostgreSQL needed locally.

## Running Tests

```bash
pytest tests/ -v
```

Expected output:

```
tests/test_extract.py::test_fetch_weather_valid_city          PASSED
tests/test_extract.py::test_fetch_weather_invalid_city        PASSED
tests/test_extract.py::test_fetch_weather_api_error           PASSED
tests/test_extract.py::test_fetch_all_cities_returns_all      PASSED
tests/test_extract.py::test_fetch_all_cities_skips_failed     PASSED
tests/test_load.py::test_ensure_table_creates_table           PASSED
tests/test_load.py::test_load_inserts_rows                    PASSED
tests/test_load.py::test_load_returns_correct_count           PASSED
tests/test_load.py::test_load_skips_duplicates                PASSED
tests/test_load.py::test_load_partial_new_rows                PASSED
tests/test_transform.py::test_classify_temperature[...]       PASSED (x6)
tests/test_transform.py::test_transform_returns_dataframe     PASSED
...

25 passed in 1.70s
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./weather.db` | Database connection string |

For PostgreSQL:
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/weatherdb
```

## Author

**José Ángel Ceballos Rodríguez**
- GitHub: [@Euchelu](https://github.com/Euchelu)
- LinkedIn: [José Ángel Ceballos](https://www.linkedin.com/in/josé-ángel-ceballos-rodríguez-a44996346/)
