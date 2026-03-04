# ICEBreaker Architecture

> Stateless by design. Ephemeral by conviction.

---

## System Overview

```
┌─────────────────────────────────────┐
│         Browser (Leaflet SPA)       │
│  GPS locate · tag · note · submit   │
│  polls GET /api/sightings every 30s │
└────────────┬────────────────────────┘
             │ HTTPS :443
┌────────────▼────────────────────────┐
│         nginx reverse proxy         │
│  TLS termination · rate limiting    │
│  security headers · 4 KB body cap   │
└────────────┬────────────────────────┘
             │ HTTP :8000 (loopback)
┌────────────▼────────────────────────┐
│     Uvicorn + FastAPI (2 workers)   │
│  input validation · sanitization    │
│  CORS · slowapi rate limiting       │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│        Redis (in-memory only)       │
│  sighting:{uuid} hashes, TTL 900s   │
│  sightings:index set, TTL 960s      │
└─────────────────────────────────────┘
```

---

## Data Flow

### Submitting a sighting

```
User taps GPS → selects tags → optional note → POST /api/sightings
  → Pydantic validates lat/lon bounds, tag enum, note length
  → backend strips HTML tags & control chars
  → UUID generated, timestamps computed (UTC)
  → Redis HSET sighting:{uuid} with TTL=900s
  → sightings:index SADD with TTL=960s
  → 201 → SightingOut JSON returned
```

### Reading the map

```
Every 30s: GET /api/sightings
  → backend scans sightings:index
  → dead keys pruned, live hashes fetched
  → ttl_remaining computed per entry
  → 200 → list[SightingOut]
  → frontend reconciles markers (add/remove/update)
```

---

## API Surface

| Method | Path | Rate limit | Purpose |
|--------|------|------------|---------|
| `GET` | `/` | — | Serve the SPA |
| `GET` | `/api/health` | — | Health check (`{"status":"ok","redis":"ok"}`) |
| `GET` | `/api/sightings` | 120/min | Fetch all live sightings |
| `POST` | `/api/sightings` | 30/hr | Submit a new sighting |

---

## Sighting Schema

### Input (`SightingIn`)

| Field | Type | Constraints |
|-------|------|-------------|
| `lat` | float | 24.0 – 50.0 (continental US) |
| `lon` | float | -125.0 – -66.0 |
| `tags` | list[str] | 1–7 from: `checkpoint`, `vehicles`, `foot_patrol`, `air_asset`, `road_block`, `medical_delay`, `clear` |
| `note` | str | max 280 chars, sanitized |

### Output (`SightingOut`)

All input fields plus `id` (UUID), `posted_at`, `expires_at` (ISO 8601), and `ttl_remaining` (seconds).

---

## Redis Layout

```
sighting:{uuid}          → Hash   (TTL 900s / 15 min)
  id, lat, lon, tags (JSON), note, posted_at, expires_at

sightings:index          → Set    (TTL 960s / 16 min buffer)
  members: sighting:{uuid}, ...
```

No persistence configured. All data lives in memory and vanishes on restart or expiry.

---

## Frontend

Single HTML file (`frontend/index.html`) — no build step, no framework.

| Layer | Tech |
|-------|------|
| Map | Leaflet 1.9.4 (OSM tiles) |
| Styling | Embedded CSS, dark theme, responsive |
| JS | Vanilla — fetch, geolocation API, vibration API |
| Layout | Bottom sheet (mobile) / sidebar (desktop) |

### Marker colours

| Tag | Colour |
|-----|--------|
| `checkpoint` | gold `#e3b341` |
| `vehicles` / `foot_patrol` | orange `#f0883e` |
| `air_asset` | light blue `#a5d6ff` |
| `road_block` | red `#f85149` |
| `medical_delay` | light red `#ff7b72` |
| `clear` | green `#3fb950` |

---

## Security Model

### Defence in depth

| Layer | Mechanism |
|-------|-----------|
| nginx | TLS, rate limiting (2/min POST, 30/min GET), 4 KB body cap, security headers (HSTS, CSP, X-Frame-Options DENY) |
| FastAPI | CORS middleware, slowapi per-endpoint limits, Pydantic validation, HTML/control-char stripping |
| systemd | Unprivileged user, `NoNewPrivileges`, `ProtectSystem=strict`, `CapabilityBoundingSet=` (empty), syscall whitelist |
| Design | No accounts, no cookies, no telemetry, no persistent storage |

### Zero-Persistence Protocol

- **15-minute TTL** on every sighting — no archive, no history.
- **No user identifiers** — no accounts, sessions, emails, or tracking pixels.
- **No server-side logs of sighting content** — Redis evicts automatically.

---

## Deployment Target

| | |
|---|---|
| **OS** | Ubuntu 22.04 / Debian 12 |
| **Process manager** | systemd |
| **Recommended jurisdiction** | Iceland (IMMI framework) |
| **Recommended hosts** | 1984 Hosting, Flokinet |

See [DEPLOY.md](DEPLOY.md) for step-by-step setup.

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `REDIS_HOST` | `127.0.0.1` | Redis hostname |
| `REDIS_PORT` | `6379` | Redis port |
| `ALLOWED_ORIGIN` | *(empty)* | Lock CORS to a specific domain |

Set in the `[Service]` block of `icebreaker.service`.
