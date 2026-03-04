"""
ICEBreaker Signal Mirror — Backend
FastAPI + Redis, stateless by design.
All sightings expire after TTL_SECONDS. No user data stored.
"""

import os
import re
import uuid
import json
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
import redis as redis_lib

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

TTL_SECONDS = 900  # 15 minutes

REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Allowed origin for CORS. Set to your domain in production.
# Empty string = same-origin only (recommended when frontend is served here).
ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "")

r = redis_lib.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

# ---------------------------------------------------------------------------
# Rate limiter
# ---------------------------------------------------------------------------

limiter = Limiter(key_func=get_remote_address)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="ICEBreaker Signal Mirror", docs_url=None, redoc_url=None)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS: only allow the configured origin (or none if same-origin)
origins = [ALLOWED_ORIGIN] if ALLOWED_ORIGIN else []
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# ---------------------------------------------------------------------------
# Security headers middleware
# ---------------------------------------------------------------------------

@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://unpkg.com; "
        "style-src 'self' 'unsafe-inline' https://unpkg.com; "
        "img-src 'self' data: https://*.tile.openstreetmap.org; "
        "connect-src 'self'; "
        "frame-ancestors 'none';"
    )
    # Never cache API responses
    if request.url.path.startswith("/api"):
        response.headers["Cache-Control"] = "no-store"
    return response

# ---------------------------------------------------------------------------
# Input helpers
# ---------------------------------------------------------------------------

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

def sanitize_note(text: str) -> str:
    """Strip HTML tags and control characters from free-text note."""
    text = _HTML_TAG_RE.sub("", text)
    text = _CONTROL_RE.sub("", text)
    return text.strip()

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
    tags: list[str] = Field(default_factory=list, max_length=len(VALID_TAGS))
    note: str = Field(default="", max_length=280)

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v):
        invalid = set(v) - VALID_TAGS
        if invalid:
            raise ValueError(f"Unknown tags: {invalid}")
        return list(set(v))  # deduplicate

    @field_validator("note")
    @classmethod
    def clean_note(cls, v):
        return sanitize_note(v)

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
@limiter.limit("30/hour")
def post_sighting(request: Request, body: SightingIn):
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

    r.sadd("sightings:index", key)
    r.expire("sightings:index", TTL_SECONDS + 60)

    return SightingOut(
        **{**record, "tags": body.tags, "ttl_remaining": TTL_SECONDS}
    )


@app.get("/api/sightings", response_model=list[SightingOut])
@limiter.limit("120/minute")
def get_sightings(request: Request):
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
