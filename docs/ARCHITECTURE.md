# Architecture

## Stack

| Layer | Technology | Why |
|---|---|---|
| Backend | FastAPI + uvicorn | Lightweight, typed, easy to read and maintain |
| Storage | Redis | Native key TTL — expiration is enforced by the database, not application logic |
| Frontend | Leaflet + OpenStreetMap | No API key, no Google dependency, works offline-ish |
| Reverse proxy | nginx | Rate limiting at the network layer before Python touches the request |
| Process manager | systemd | Standard on every Linux VPS, tight isolation controls |

---

## Data Flow

```
Browser
  │
  │  HTTPS (nginx)
  ▼
nginx
  │  rate limit check (limit_req)
  │  4k body size cap
  │  method allowlist
  │
  │  proxy_pass 127.0.0.1:8000
  ▼
FastAPI (uvicorn)
  │  slowapi rate limit (per IP)
  │  pydantic validation (bounds, tag allowlist, note sanitization)
  │  security headers attached to every response
  │
  │  hset + expire
  ▼
Redis (local, no persistence)
  │
  │  TTL countdown (900s)
  ▼
  [key auto-deleted]
```

When a client polls `GET /api/sightings`, the app reads from the `sightings:index` set, checks each key's remaining TTL, drops any that have already expired, and returns the live ones. Redis handles the actual deletion — the app just skips what's already gone.

---

## Redis Key Structure

Two key types, nothing else:

```
sighting:{uuid4}      Hash
  id          string   UUID4
  lat         string   float, stored as string
  lon         string   float, stored as string
  tags        string   JSON array
  note        string   sanitized plain text, max 280 chars
  posted_at   string   ISO 8601 UTC
  expires_at  string   ISO 8601 UTC
  TTL: 900 seconds

sightings:index       Set
  members: "sighting:{uuid4}", ...
  TTL: 960 seconds (TTL + 60s buffer for cleanup)
```

The index set exists so `GET /api/sightings` can retrieve all live keys without a full `SCAN`. The 60-second buffer on its TTL means the set doesn't disappear before the last sightings in it do.

No other keys are written. No counters, no session state, no logs.

---

## Why No Database

A traditional database (Postgres, SQLite, anything with durable writes) would create a subpoena target. Redis with `appendonly no` (the default) keeps everything in memory only. A server restart clears all data. There is nothing to image, nothing to hand over after the TTL window closes.

This is not a security-through-obscurity choice. It is a data minimization choice. The data is only valuable for 15 minutes. After that, retaining it serves no purpose and creates risk.

---

## Frontend

`frontend/index.html` is a single file with no build step. Leaflet and its CSS are loaded from `unpkg.com` (CDN, pinned to version 1.9.4). The map tiles come from OpenStreetMap. No other external dependencies.

The frontend polls `GET /api/sightings` every 30 seconds and reconciles the marker set — adding new ones, removing expired ones. It does not store anything locally.

On mobile (viewport < 640px), the report form lives in a bottom sheet. On desktop it is a fixed sidebar. The GPS locate button uses `navigator.geolocation.getCurrentPosition` with `enableHighAccuracy: true`. Map tap works as a fallback on both.
