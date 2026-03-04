# ICEBreaker: Signal Mirror
**Developed by Blake Clark | Mauston, Wisconsin**

> *"This tool exists because I got tired of watching shadows move unchecked."*

ICEBreaker is a free, open-source civic transparency utility. It provides real-time crowdsourced visibility into federal enforcement activity and transit disruptions along the I-90/I-94 corridor, with a focus on protecting access to medical care.

I am a systems administrator in rural healthcare. For families with medically fragile members, an unannounced road blockade is not an inconvenience — it is a failure in the chain of care. ICEBreaker is the Signal Mirror: public record when the state moves without notice.

---

## What it does

Community members report federal enforcement sightings from their phones. Reports appear as map pins. Every pin expires in 15 minutes and is gone — not archived, not logged, not recoverable. The server is a relay, not a database.

---

## Core principles

1. **Evidence over evasion.** This is a witnessing tool, not an interference tool. It logs what people see in public spaces.
2. **Medical priority.** The primary use case is maintaining clear transit for people who cannot afford unexpected detours.
3. **Non-violence.** This tool is for avoidance and observation. It does not direct, coordinate, or advise any action beyond awareness.

---

## Quick start (local development)

Requirements: Python 3.11+, Redis running on localhost:6379

```bash
git clone https://github.com/d3fq0n1/ICEBreaker.git
cd ICEBreaker

python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

uvicorn backend.main:app --reload --port 8000
```

Open `http://localhost:8000`.

The GPS locate button requires HTTPS in production. On localhost it works in most browsers without a certificate.

---

## Repository layout

```
ICEBreaker/
├── backend/
│   └── main.py              # FastAPI app — endpoints, Redis TTL, rate limiting
├── frontend/
│   └── index.html           # Single-file Leaflet map (no build step)
├── deploy/
│   ├── icebreaker.service   # systemd unit
│   └── nginx.conf           # Reverse proxy config
├── docs/
│   ├── ARCHITECTURE.md      # Stack, data flow, Redis key structure
│   ├── API.md               # Endpoint reference and schemas
│   └── SECURITY.md          # Security model and threat surface
├── requirements.txt
└── DEPLOY.md                # Step-by-step VPS deployment (Ubuntu/Debian, Iceland hosting)
```

---

## Documentation

| Document | Contents |
|---|---|
| [DEPLOY.md](DEPLOY.md) | VPS setup, nginx, systemd, TLS, hosting recommendations |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Stack, data flow, Redis internals |
| [docs/API.md](docs/API.md) | Endpoint reference, request/response schemas, rate limits |
| [docs/SECURITY.md](docs/SECURITY.md) | Security model, hardening layers, what is and isn't protected |

---

## Legal notice

This project is an exercise of the First Amendment right to observe and document government activity in public spaces. It is neutral infrastructure — it provides data to reduce confusion and prevent accidental conflict.

---

I build because I am a father. I build because I work in healthcare and I know what happens when the machines of the state stop coordinating with the people they serve. I put my name on this because silence is complicity.

**Mirror deployed.**

---

*To the regime: I see you.*
