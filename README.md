# OrderOps backend

Small FastAPI API backed by PostgreSQL.

## Structure

```text
app/
  main.py                   # Application setup and router registration
  db.py                     # Shared PostgreSQL connection factory
  products/
    router.py               # HTTP endpoints and dependency injection
    schemas.py              # Request validation and response models
    repository.py           # Parameterized SQL and transactions
tests/
  conftest.py               # Shared fixtures and repository override
  unit/
    test_db.py              # Connection configuration
    products/
      test_router.py        # HTTP behavior with a mocked repository
      test_schemas.py       # Validation rules and boundary values
      test_repository.py    # SQL behavior with mocked connections
  performance/
    conftest.py             # In-memory repository and async ASGI client
    test_api.py             # Latency budgets and concurrent request benchmarks
sql/
  001_create_products.sql   # Initial database schema
```

Keep each feature in its own package under `app/`, following `products`.
Routes handle HTTP, schemas validate data, and repositories access the database.
Add a service layer when a feature needs business logic beyond CRUD.

## Local development

Install Python 3.14+ and uv, then run:

```sh
uv sync --locked
```

Set `DATABASE_URL` in your environment or the root `.env` file, apply
`sql/001_create_products.sql` to that PostgreSQL database, then start the API:

```sh
psql "$DATABASE_URL" -f sql/001_create_products.sql
uv run uvicorn app.main:app --reload
```

`psql` uses the shell environment; export `DATABASE_URL` before running it.
The app loads `.env` automatically. API documentation is at
<http://127.0.0.1:8000/docs>.

## Tests

```sh
uv run pytest
uv run pytest --cov=app --cov-report=term-missing
```

The tests require no running PostgreSQL instance or database credentials.
Route tests use FastAPI dependency overrides; repository and connection tests
use mocks. These tests do not verify real PostgreSQL execution or migrations.

## Performance and latency tests

Performance tests are opt-in so ordinary `uv run pytest` stays fast:

```sh
uv run pytest -m performance -s
```

The local tests measure GET, POST, and PATCH with 100 measured requests each,
both sequentially and with 10 concurrent requests. Another test lists 1,000
products under concurrency. Each scenario runs five warm-up requests first and
reports p50, p95, p99, maximum latency, and requests per second. Every response
must succeed and have the expected shape or values.

The local tests use the actual FastAPI app with an in-memory repository. They
measure request handling, validation, serialization, and dependency overhead;
they exclude network and PostgreSQL costs. Latency is measured after a request
acquires its concurrency slot, so time waiting for a slot is excluded.
Throughput includes scheduling and response checks.

The default regression budgets are **p95 <= 250 ms** and **p99 <= 500 ms**.
These are initial local guardrails, not production service targets. Run on a
quiet machine without coverage instrumentation for comparable results. Adjust
budgets and sample count to match your baseline:

```sh
PERF_SAMPLES=500 PERF_P95_MS=100 PERF_P99_MS=250 uv run pytest -m performance -s
```

To include HTTP and PostgreSQL latency, start the API against a disposable test
database and run the optional read-only live benchmark:

```sh
PERF_BASE_URL=http://127.0.0.1:8000 uv run pytest -m performance -k live -s
```

It sends GET requests only and uses whatever products are already in the
database; seed representative data for useful results. It reports the same
metrics with default budgets of p95 <= 1,000 ms and p99 <= 2,000 ms. Configure
`PERF_LIVE_P95_MS`, `PERF_LIVE_P99_MS`, `PERF_LIVE_CONCURRENCY` (default 10),
and `PERF_SAMPLES` as needed. Without `PERF_BASE_URL`, this test is skipped.

## Endpoints

| Method | Path | Behavior |
| --- | --- | --- |
| GET | `/products` | List products ordered by ID |
| POST | `/products` | Create a product; return 201 |
| PATCH | `/products/{product_id}` | Update supplied fields; return 404 if missing |

PATCH requires at least one non-null field. Prices must be positive with at
most two decimal places; stock can be zero but cannot be negative.
