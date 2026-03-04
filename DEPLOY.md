# Deploying ICEBreaker on a Linux VPS

Tested on Ubuntu 22.04 / Debian 12.

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

| Variable     | Default     | Description              |
|-------------|-------------|--------------------------|
| `REDIS_HOST` | `127.0.0.1` | Redis hostname           |
| `REDIS_PORT` | `6379`      | Redis port               |

Set them in the `[Service]` block of `icebreaker.service` as `Environment=KEY=value`.

---

## Updating

```bash
cd /opt/icebreaker
sudo -u icebreaker git pull
sudo -u icebreaker venv/bin/pip install -r requirements.txt
sudo systemctl restart icebreaker
```
