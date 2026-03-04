# Security Model

## What this document covers

The threat model for ICEBreaker is different from a typical web app. The primary concern is not protecting user accounts or financial data — there are none. The concerns are:

1. The server being flooded or abused to serve false data
2. A legal demand for user data producing anything meaningful
3. The server process being compromised and used for something else

Each layer below addresses one or more of those.

---

## Data minimization (the main defense)

No IP addresses are logged. No session identifiers are issued. No user accounts exist. The only thing stored is the sighting payload itself (coordinates, tags, optional note), and it lives for 15 minutes.

Redis is run without append-only file persistence (`appendonly no` is the default). All data is in-memory. A server restart is a clean slate.

After the TTL expires, a legal demand for "all data on user X" produces nothing, because there is no user X and there is no data.

---

## Rate limiting

Two layers:

**nginx** (network layer, before Python runs):
- POST to `/api/sightings`: 2 requests/minute per IP, burst of 5
- All other routes: 30 requests/minute per IP, burst of 20
- Request body capped at 4KB — oversized requests are rejected before parsing

**slowapi** (application layer, per endpoint):
- POST `/api/sightings`: 30 requests/hour per IP
- GET `/api/sightings`: 120 requests/minute per IP

The nginx limits are tighter and hit first. The slowapi limits are a backstop for anything that gets through (e.g., if nginx is misconfigured).

---

## Input validation

All input is validated by pydantic before it touches the database:

- `lat`/`lon`: must be within continental US bounding box (24–50°N, 66–125°W). Coordinates outside this range are rejected with 422.
- `tags`: validated against a hard-coded allowlist. Any unknown tag causes a 422.
- `note`: HTML tags and C0/C1 control characters are stripped server-side before storage. Max 280 characters.

The frontend also does client-side validation, but server-side validation is the authoritative check.

---

## HTTP security headers

Every response carries:

- `X-Content-Type-Options: nosniff` — prevents MIME-type sniffing
- `X-Frame-Options: DENY` — blocks the page from being embedded in an iframe
- `Referrer-Policy: no-referrer` — no referrer header sent on outgoing requests
- `Content-Security-Policy` — restricts script/style sources to `self` and pinned unpkg.com CDN; blocks inline eval; `frame-ancestors 'none'`
- `Cache-Control: no-store` on all `/api/*` responses — sightings are not cached by proxies or CDNs
- `Permissions-Policy` — explicitly revokes geolocation, camera, and microphone permission grants at the browser level (the frontend requests geolocation only when the user taps the locate button)

---

## CORS

CORS is locked to the `ALLOWED_ORIGIN` environment variable. In production this should be set to `https://yourdomain.com`. When the variable is empty (the default), no cross-origin requests are allowed — which is correct when the frontend is served by the same FastAPI process.

---

## nginx hardening

- `server_tokens off` — nginx version not sent in error responses or headers
- `client_max_body_size 4k` — no large body attacks
- Method allowlist: only GET, POST, HEAD, OPTIONS are accepted; everything else returns 405
- HSTS with `max-age=63072000; includeSubDomains; preload` — forces HTTPS for two years after first visit
- HTTP permanently redirected to HTTPS (301)

---

## systemd process isolation

The `icebreaker` system user has no login shell and no home directory. The service unit adds:

- `NoNewPrivileges=true` — process cannot gain additional privileges via setuid/setgid
- `PrivateTmp=true` — isolated `/tmp`
- `PrivateDevices=true` — no access to hardware devices
- `ProtectSystem=strict` — filesystem is read-only except for explicitly listed paths
- `ProtectHome=true` — no access to `/home`, `/root`, `/run/user`
- `ProtectKernelTunables`, `ProtectKernelModules`, `ProtectKernelLogs` — cannot touch kernel interfaces
- `ProtectControlGroups=true` — cannot modify cgroup hierarchy
- `CapabilityBoundingSet=` (empty) — no Linux capabilities at all; the process binds to port 8000 (unprivileged) via nginx proxy, so none are needed
- `MemoryDenyWriteExecute=true` — blocks write+execute memory mappings (shellcode injection)
- `LockPersonality=true` — cannot change execution domain
- `RestrictNamespaces=true` — cannot create new namespaces
- `SystemCallFilter=@system-service` — only syscalls a normal service needs are allowed; anything else returns EPERM

---

## What this doesn't protect

- **Your identity.** Your name is on the repo by choice. If you receive legal process as an individual, hosting jurisdiction and data minimization help, but they don't make you unreachable.
- **DNS seizure.** If your domain is registered with a US registrar, the domain can be seized independently of the server. See DEPLOY.md for registrar guidance.
- **The server IP.** Anyone can see the server's IP address. Iceland's jurisdiction makes legal action slower and harder, not impossible.
- **Coordinated false reports.** Rate limiting reduces abuse but doesn't eliminate it. There is no authentication layer because authentication would require storing user identifiers, which contradicts the zero-persistence model.
