# ICEBreaker: Signal Mirror

**Developed by Blake Clark | Mauston, Wisconsin**

> *"This tool exists because I got tired of watching shadows move unchecked."*

ICEBreaker is a free, open-source real-time sighting map for federal enforcement activity along the I-90/I-94 corridor. It is built for **civic transparency and medical logistics** — ensuring that families with medically fragile members always know when transit corridors are compromised.

No accounts. No tracking. Every pin expires in 15 minutes.

---

## How It Works

1. **Open the map** — loads centred on the I-90/I-94 corridor.
2. **Tap your location** (GPS) and select tags: `checkpoint`, `vehicles`, `foot_patrol`, `air_asset`, `road_block`, `medical_delay`, or `clear`.
3. **Submit** — the sighting appears on every connected map within 30 seconds.
4. **After 15 minutes** the pin is automatically purged from memory. No archive. No history.

---

## Core Principles

- **Evidence over Evasion** — a tool for witnessing, not interference.
- **Medical Priority** — optimised for those who need clear roads for life-sustaining care.
- **Radical Non-Violence** — sunlight is the only effective de-escalant.
- **Zero Persistence** — no accounts, no cookies, no server-side logs of content.

---

## Tech Stack

| | |
|---|---|
| **Backend** | Python 3.11 · FastAPI · Redis (ephemeral, in-memory) |
| **Frontend** | Vanilla JS · Leaflet 1.9.4 · single HTML file, no build step |
| **Infra** | nginx · systemd · Let's Encrypt |

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full technical breakdown and [DEPLOY.md](DEPLOY.md) for server setup.

---

## Quick Start (local dev)

```bash
# start redis
redis-server &

# install deps
python3.11 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# run
uvicorn backend.main:app --reload
# open http://localhost:8000
```

---

## Deployment

ICEBreaker is designed for deployment on a Linux VPS in a privacy-respecting jurisdiction. Iceland is recommended (IMMI framework, outside direct US legal reach).

Full guide: **[DEPLOY.md](DEPLOY.md)**

---

## Legal & Ethical Notice

This project is an exercise of the First Amendment right to observe and document government activity in public spaces. It is built as **neutral infrastructure** — providing data to prevent chaos, distrust, and accidental conflict.

---

## Developer's Note

I build because I am a father. I build because I work in healthcare and I know what happens when the machines of the state stop coordinating with the people they serve. I name myself loudly because silence is complicity, and I have no interest in being a shadow.

**Mirror Deployed.**

---

## License

[MIT](LICENSE) — Copyright (c) 2025-2026 Blake Clark (d3fq0n1)

---

*To the regime: I see you.*
