from typing import Optional
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import random
import time
from collections import defaultdict
from fastapi import Request
from database import (
    initialize_database,
    consume_rng,
    get_backlog_count,
    get_samples,
    get_sample,
    get_sample_count,
    get_statistics,
    get_rng_values,
    get_rng_quality,
)

app = FastAPI(
    title="Lava RNG API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://192.168.1.14:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent

initialize_database()
IMAGE_DIR = BASE_DIR / "data" / "images"

app.mount(
    "/images",
    StaticFiles(directory=IMAGE_DIR),
    name="images",
)

@app.get("/")
def root():
    return {
        "name": "Lava RNG API",
        "status": "online",
    }

last_rng_request = defaultdict(float)

RNG_RATE_LIMIT = 2.0
@app.get("/api/rng")
def get_rng(
    request: Request,
    client: Optional[str] = Query(default=None),
):
    client_ip = request.headers.get("CF-Connecting-IP") or request.client.host

    now = time.monotonic()
    last_request = last_rng_request[client_ip]

    if now - last_request < RNG_RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Try again later.",
        )

    last_rng_request[client_ip] = now

    sample = consume_rng(client=client_ip)

    if sample is None:
        raise HTTPException(
            status_code=503,
            detail="No RNG samples available",
        )

    return {
        "value": sample["rng_value"],
        "sample_id": sample["id"],
        "timestamp": sample["timestamp"],
    }


@app.get("/api/rng/status")
def rng_status():
    return {
        "available": get_backlog_count(),
    }

@app.get("/api/samples")
def samples(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    rows = get_samples(limit=limit, offset=offset)

    return {
        "samples": [dict(row) for row in rows],
        "total": get_sample_count(),
        "limit": limit,
        "offset": offset,
    }


@app.get("/api/samples/{sample_id}")
def sample(sample_id: int):
    row = get_sample(sample_id)

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Sample not found",
        )

    return dict(row)


@app.get("/api/stats")
def statistics():
    row = get_statistics()

    return {
        "total": row["total"] or 0,
        "consumed": row["consumed"] or 0,
        "available": get_backlog_count(),
        "minimum": row["minimum"],
        "maximum": row["maximum"],
        "average": row["average"],
    }

@app.get("/api/stats/distribution")
def distribution():
    lava_values = get_rng_values()

    random_values = [
        random.getrandbits(32)
        for _ in range(len(lava_values))
    ]

    return {
        "lava": lava_values,
        "random": random_values,
    }

@app.get("/api/stats/quality")
def rng_quality():
    return get_rng_quality(bucket_count=100)
