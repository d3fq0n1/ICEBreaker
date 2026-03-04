"""
ICEBreaker Signal Mirror — Backend
FastAPI + Redis, stateless by design.
All sightings expire after TTL_SECONDS. No user data stored.
"""

import uuid
import json
import time
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator
import redis

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

TTL_SECONDS = 900  # 15 minutes

# Redis default: localhost:6379, db 0. Override via env if needed.
import os
REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="ICEBreaker Signal Mirror", docs_url=None, redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

VALID_TAGS = {
    "checkpoint",
    "vehicles",
    "foot_patrol",
    "air_asset",
    "road_block",
    "medical_delay",
    "clear",
}

class SightingIn(BaseModel):
    lat: float = Field(..., ge=24.0, le=50.0)   # continental US rough bounds
    lon: float = Field(..., ge=-125.0, le=-66.0)
    tags: list[str] = Field(default_factory=list)
    note: str = Field(default="", max_length=280)

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v):
        invalid = set(v) - VALID_TAGS
        if invalid:
            raise ValueError(f"Unknown tags: {invalid}. Allowed: {VALID_TAGS}")
        return list(set(v))  # deduplicate

class SightingOut(BaseModel):
    id: str
    lat: float
    lon: float
    tags: list[str]
    note: str
    posted_at: str
    expires_at: str
    ttl_remaining: int  # seconds

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/sightings", response_model=SightingOut, status_code=201)
def post_sighting(body: SightingIn):
    sid = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    expires = now.timestamp() + TTL_SECONDS

    record = {
        "id": sid,
        "lat": body.lat,
        "lon": body.lon,
        "tags": json.dumps(body.tags),
        "note": body.note,
        "posted_at": now.isoformat(),
        "expires_at": datetime.fromtimestamp(expires, tz=timezone.utc).isoformat(),
    }

    key = f"sighting:{sid}"
    r.hset(key, mapping=record)
    r.expire(key, TTL_SECONDS)

    # Keep a set index so we can scan efficiently
    r.sadd("sightings:index", key)
    r.expire("sightings:index", TTL_SECONDS + 60)

    return SightingOut(
        **{**record, "tags": body.tags, "ttl_remaining": TTL_SECONDS}
    )


@app.get("/api/sightings", response_model=list[SightingOut])
def get_sightings():
    keys = r.smembers("sightings:index")
    results = []
    for key in keys:
        ttl = r.ttl(key)
        if ttl <= 0:
            r.srem("sightings:index", key)
            continue
        data = r.hgetall(key)
        if not data:
            r.srem("sightings:index", key)
            continue
        results.append(SightingOut(
            id=data["id"],
            lat=float(data["lat"]),
            lon=float(data["lon"]),
            tags=json.loads(data["tags"]),
            note=data.get("note", ""),
            posted_at=data["posted_at"],
            expires_at=data["expires_at"],
            ttl_remaining=ttl,
        ))
    return results


@app.get("/api/health")
def health():
    try:
        r.ping()
        return {"status": "ok", "redis": "ok"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Redis unavailable: {e}")


# ---------------------------------------------------------------------------
# Serve frontend
# ---------------------------------------------------------------------------

app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

@app.get("/")
def index():
    return FileResponse("frontend/index.html")
