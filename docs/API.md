# API Reference

Base path: `/api`

All responses are JSON. All timestamps are ISO 8601 UTC.

---

## POST /api/sightings

Submit a new sighting. The sighting is stored in Redis and expires automatically after 15 minutes.

**Rate limit:** 30 requests per hour per IP address.

**Request body:**

```json
{
  "lat": 43.0731,
  "lon": -89.4012,
  "tags": ["checkpoint", "vehicles"],
  "note": "3 vehicles, northbound shoulder"
}
```

| Field | Type | Required | Constraints |
|---|---|---|---|
| `lat` | float | yes | 24.0 – 50.0 (continental US) |
| `lon` | float | yes | -125.0 – -66.0 (continental US) |
| `tags` | array of strings | no | values must be from the tag allowlist; duplicates removed |
| `note` | string | no | max 280 characters; HTML tags and control characters stripped |

**Valid tag values:**

| Tag | Meaning |
|---|---|
| `checkpoint` | Fixed checkpoint or inspection point |
| `vehicles` | Enforcement vehicles observed |
| `foot_patrol` | Agents on foot |
| `air_asset` | Helicopter or drone observed |
| `road_block` | Road physically blocked |
| `medical_delay` | Known impact to medical access |
| `clear` | Previously reported location confirmed clear |

**Response (201):**

```json
{
  "id": "a3f1c2d4-...",
  "lat": 43.0731,
  "lon": -89.4012,
  "tags": ["checkpoint", "vehicles"],
  "note": "3 vehicles, northbound shoulder",
  "posted_at": "2026-03-04T14:22:10.000000+00:00",
  "expires_at": "2026-03-04T14:37:10.000000+00:00",
  "ttl_remaining": 900
}
```

**Error responses:**

| Status | Cause |
|---|---|
| 422 | Validation failure (out-of-bounds coordinates, unknown tag, note too long) |
| 429 | Rate limit exceeded |

---

## GET /api/sightings

Returns all currently live sightings. Expired sightings are never returned.

**Rate limit:** 120 requests per minute per IP address.

**No request body or parameters.**

**Response (200):** Array of sighting objects, same schema as the POST response.

```json
[
  {
    "id": "a3f1c2d4-...",
    "lat": 43.0731,
    "lon": -89.4012,
    "tags": ["checkpoint"],
    "note": "",
    "posted_at": "2026-03-04T14:22:10.000000+00:00",
    "expires_at": "2026-03-04T14:37:10.000000+00:00",
    "ttl_remaining": 612
  }
]
```

Returns an empty array `[]` if no sightings are currently live.

---

## GET /api/health

Health check for the application and Redis connection.

**Response (200):**

```json
{"status": "ok", "redis": "ok"}
```

**Response (503):** Redis is unreachable.

```json
{"detail": "Redis unavailable: ..."}
```

---

## Response headers (all endpoints)

Every response includes:

| Header | Value |
|---|---|
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `Referrer-Policy` | `no-referrer` |
| `Permissions-Policy` | `geolocation=(), camera=(), microphone=()` |
| `Content-Security-Policy` | see `backend/main.py` |
| `Cache-Control` | `no-store` (on `/api/*` routes only) |
