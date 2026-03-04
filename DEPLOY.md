# Deploying ICEBreaker on a Linux VPS

Tested on Ubuntu 22.04 / Debian 12.

---

## Hosting recommendations

**Iceland is the recommended jurisdiction** for this project due to:
- The [IMMI framework](https://en.wikipedia.org/wiki/Icelandic_Modern_Media_Initiative) — designed as a safe harbor for publishers and journalists
- Outside direct US legal jurisdiction; cross-border demands require MLAT, a slow and high-bar process
- EEA/GDPR-aligned data minimization rules (this app already satisfies them by design)

Recommended Icelandic providers:
- **[1984 Hosting](https://www.1984hosting.com/)** — explicit commitment to free speech and privacy, used by journalists and activists, accepts crypto
- **[Flokinet](https://flokinet.is/)** — privacy-focused, also has Romania and Netherlands nodes

**DNS registrar:** Avoid US-based registrars (GoDaddy, Namecheap, etc.) — domains registered there can be seized via US court order regardless of where the server is. Use a registrar in Iceland, Netherlands, or another non-US jurisdiction.

**Payment:** If operational security matters, both 1984 and Flokinet accept cryptocurrency. Pay with a wallet not linked to your identity.

---

## 1. Install system dependencies

```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv redis-server nginx certbot python3-certbot-nginx
sudo systemctl enable --now redis
```

---

## 2. Create a dedicated user and app directory

```bash
sudo useradd -r -s /usr/sbin/nologin icebreaker
sudo mkdir -p /opt/icebreaker
sudo git clone https://github.com/YOUR_USER/ICEBreaker.git /opt/icebreaker
sudo chown -R icebreaker:icebreaker /opt/icebreaker
```

---

## 3. Set up Python virtual environment

```bash
cd /opt/icebreaker
sudo -u icebreaker python3.11 -m venv venv
sudo -u icebreaker venv/bin/pip install -r requirements.txt
```

---

## 4. Install the systemd service

```bash
sudo cp deploy/icebreaker.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now icebreaker
sudo systemctl status icebreaker
```

---

## 5. Configure nginx

```bash
# Edit the server_name line first:
sudo cp deploy/nginx.conf /etc/nginx/sites-available/icebreaker
sudo nano /etc/nginx/sites-available/icebreaker   # set YOUR_DOMAIN_OR_IP
sudo ln -s /etc/nginx/sites-available/icebreaker /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

---

## 6. Add TLS with Let's Encrypt (recommended)

```bash
sudo certbot --nginx -d yourdomain.example.com
# certbot will edit nginx.conf automatically
```

---

## 7. Verify

```bash
curl http://yourdomain.example.com/api/health
# {"status":"ok","redis":"ok"}
```

---

## Environment variables (optional overrides)

| Variable         | Default       | Description                                      |
|-----------------|---------------|--------------------------------------------------|
| `REDIS_HOST`     | `127.0.0.1`   | Redis hostname                                   |
| `REDIS_PORT`     | `6379`        | Redis port                                       |
| `ALLOWED_ORIGIN` | *(empty)*     | Lock CORS to your domain, e.g. `https://yourdomain.is` |

Set them in the `[Service]` block of `icebreaker.service` as `Environment=KEY=value`.

---

## Updating

```bash
cd /opt/icebreaker
sudo -u icebreaker git pull
sudo -u icebreaker venv/bin/pip install -r requirements.txt
sudo systemctl restart icebreaker
```
