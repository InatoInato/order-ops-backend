"""Opt-in API latency budgets; run with pytest -m performance -s."""

import asyncio
import json
import math
import os
from statistics import median
from time import perf_counter

import httpx2
import pytest

pytestmark = pytest.mark.performance


def positive_setting(name, default, conversion=float):
    value = conversion(os.environ.get(name, str(default)))
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a positive finite number")
    return value


async def measure_requests(
    client,
    method,
    path,
    *,
    payload=None,
    status=200,
    count=100,
    concurrency=1,
    expected_count=None,
):
    semaphore = asyncio.Semaphore(concurrency)

    async def request():
        async with semaphore:
            start = perf_counter()
            response = await client.request(method, path, json=payload)
            duration_ms = (perf_counter() - start) * 1000
            assert response.status_code == status, response.text
            body = response.json()
            if method == "GET":
                assert isinstance(body, list)
                if expected_count is not None:
                    assert len(body) == expected_count
            else:
                assert isinstance(body["id"], int)
                for key, value in payload.items():
                    assert body[key] == value
            return duration_ms

    # Initialize routing, dependency workers, and connections outside the sample.
    for _ in range(5):
        await request()

    start = perf_counter()
    durations = await asyncio.gather(*(request() for _ in range(count)))
    elapsed = perf_counter() - start
    ordered = sorted(durations)

    def percentile(percent):
        # Nearest-rank percentiles keep tail latency visible in small samples.
        return ordered[math.ceil(percent * len(ordered)) - 1]

    return {
        "samples": count,
        "concurrency": concurrency,
        "p50_ms": median(ordered),
        "p95_ms": percentile(0.95),
        "p99_ms": percentile(0.99),
        "max_ms": max(ordered),
        "requests_per_second": count / elapsed,
    }


def check_budget(report, label, *, live=False):
    print(f"\n{label}: {json.dumps(report, sort_keys=True)}")
    prefix = "PERF_LIVE" if live else "PERF"
    p95_limit = positive_setting(f"{prefix}_P95_MS", 1000 if live else 250)
    p99_limit = positive_setting(f"{prefix}_P99_MS", 2000 if live else 500)
    assert report["p95_ms"] <= p95_limit, (
        f"{label}: p95 {report['p95_ms']:.2f} ms exceeds {p95_limit:.2f} ms"
    )
    assert report["p99_ms"] <= p99_limit, (
        f"{label}: p99 {report['p99_ms']:.2f} ms exceeds {p99_limit:.2f} ms"
    )


@pytest.mark.parametrize("concurrency", [1, 10], ids=["sequential", "concurrent"])
@pytest.mark.parametrize(
    ("method", "path", "status"),
    [
        ("GET", "/products", 200),
        ("POST", "/products", 201),
        ("PATCH", "/products/1", 200),
    ],
    ids=["list", "create", "update"],
)
async def test_endpoint_latency(
    performance_client, product_data, method, path, status, concurrency
):
    payload = None
    if method == "POST":
        payload = product_data
    elif method == "PATCH":
        payload = {"stock": 0}

    report = await measure_requests(
        performance_client,
        method,
        path,
        payload=payload,
        status=status,
        count=positive_setting("PERF_SAMPLES", 100, int),
        concurrency=concurrency,
        expected_count=100 if method == "GET" else None,
    )
    check_budget(report, f"{method} {path}")


async def test_large_product_list_latency(
    performance_client, performance_repository, product_row
):
    performance_repository.rows = [
        {**product_row, "id": index} for index in range(1, 1001)
    ]
    response = await performance_client.get("/products")
    assert len(response.json()) == 1000

    report = await measure_requests(
        performance_client,
        "GET",
        "/products",
        count=positive_setting("PERF_SAMPLES", 100, int),
        concurrency=10,
        expected_count=1000,
    )
    check_budget(report, "GET /products (1000 products)")


async def test_live_product_list_latency():
    base_url = os.environ.get("PERF_BASE_URL")
    if not base_url:
        pytest.skip("Set PERF_BASE_URL to benchmark a running API with PostgreSQL")

    # Keep the live benchmark read-only: no fixtures create or change products.
    async with httpx2.AsyncClient(
        base_url=base_url.rstrip("/") + "/", timeout=10, trust_env=False
    ) as client:
        report = await measure_requests(
            client,
            "GET",
            "products",
            count=positive_setting("PERF_SAMPLES", 100, int),
            concurrency=positive_setting("PERF_LIVE_CONCURRENCY", 10, int),
        )
    check_budget(report, "Live GET /products", live=True)
