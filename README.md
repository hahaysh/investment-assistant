# 🦞 OpenClaw Personal Investment Assistant

> 🇰🇷 [한국어 README](README.ko.md)

An automated personal investment management system running on an Azure Linux VM. OpenClaw AI Agent generates daily investment briefings, and a FastAPI web app manages portfolio and watchlist.

> **🌐 Live App:** [http://hahayshopenclaw.koreacentral.cloudapp.azure.com:8002/](http://hahayshopenclaw.koreacentral.cloudapp.azure.com:8002/)

---

## System Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                          Azure Linux VM                          │
│                                                                  │
│   ┌───────────────────┐     ┌──────────────────────────────────┐ │
│   │     OpenClaw      │     │        webapp2  (port 8002)      │ │
│   │    (AI Agent)     │     │                                  │ │
│   │                   │     │  ┌─────────────┐ ┌────────────┐  │ │
│   │  daily-briefing   │     │  │   FastAPI   │ │ Vanilla JS │  │ │
│   │  weekly-report    │     │  │   Backend   │ │  Frontend  │  │ │
│   └────────┬──────────┘     │  └──────┬──────┘ └─────┬──────┘  │ │
│            │ writes         │         │               │          │ │
│            ▼                │         ▼       static/index.html  │ │
│   ~/investment-assistant/   │  ┌────────────────────────────┐   │ │
│   ├─ data/                  │  │  ~/investment-assistant/   │   │ │
│   │  ├─ portfolio.csv  ◄────┼──│  ├─ data/*.csv             │   │ │
│   │  └─ watchlist.csv       │  │  ├─ reports/daily/*.md     │   │ │
│   ├─ reports/               │  │  └─ reports/weekly/*.md    │   │ │
│   │  ├─ daily/*.md          │  └────────────────────────────┘   │ │
│   │  └─ weekly/*.md         │                                    │ │
│   └─ generate_briefing.py   │  ┌────────────────────────────┐   │ │
│                             │  │  External APIs             │   │ │
│                             │  │  ├─ yfinance  (quotes)     │   │ │
│                             │  │  └─ Azure OpenAI (gpt-4o)  │   │ │
│                             │  └────────────────────────────┘   │ │
│                             └──────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘

GitHub ──(push)──► GitHub Actions ──(rsync)──► webapp2  (auto deploy)
```

### Data Flow

| Flow | Description |
| ---- | ----------- |
| **OpenClaw → Files** | AI Agent saves daily/weekly briefings as Markdown under `reports/` |
| **Files → FastAPI** | FastAPI reads CSV and Markdown files directly via API (no database) |
| **FastAPI → Frontend** | REST API + static file serving handled by a single FastAPI server |
| **yfinance → enrich** | Fetches real-time quotes and news when a ticker is entered |
| **Azure OpenAI → enrich** | Generates watchlist analysis text from yfinance news using gpt-4o |

---

## Repository Structure

```text
investment-assistant/
├── .github/
│   └── workflows/
│       └── deploy-webapp2.yml       # GitHub Actions auto-deploy
│
├── openclaw/                        # OpenClaw AI Agent configuration
│   ├── skills/
│   │   ├── daily-investment-briefing/   # Daily briefing skill
│   │   └── weekly-portfolio-report/     # Weekly report skill
│   ├── scripts/
│   │   └── setup.sh
│   └── docs/                        # Step-by-step setup guides
│       ├── step1-project-setup.md
│       ├── step2-skills.md
│       ├── step3-briefing-script.md
│       ├── step4-cron.md
│       ├── step5-test.md
│       └── troubleshooting.md
│
└── webapp/                          # Web app source code
    ├── main.py                      # FastAPI entry point, router registration
    ├── config.py                    # Central file path constants
    ├── requirements.txt
    ├── start.sh                     # Development server start script
    ├── investment-webapp.service    # systemd service template
    ├── nginx-investment.conf        # Nginx reverse proxy config
    ├── routers/
    │   ├── reports.py               # Daily/weekly report API
    │   ├── portfolio.py             # Portfolio CRUD API
    │   ├── watchlist.py             # Watchlist CRUD API
    │   └── enrich.py                # Stock info lookup + AI auto-fill API
    └── static/
        ├── index.html               # SPA frontend (full UI)
        └── translations/            # i18n translation files
            ├── ko.js                # Korean
            ├── en.js                # English
            ├── ja.js                # Japanese
            ├── zh.js                # Chinese
            └── fr.js                # French
```

---

## Prerequisites

- Ubuntu 24.04 LTS (Azure VM)
- Python 3.x + pip
- OpenClaw installed and running (`openclaw-gateway` process)
- Telegram bot connected
- Azure OpenAI resource (shared with OpenClaw config)

---

## Part 1 — OpenClaw Automation

### VM Working Directory

```text
~/investment-assistant/
├── data/
│   ├── investor_profile.md     # Investor profile
│   ├── portfolio.csv           # Holdings
│   └── watchlist.csv           # Watchlist
├── reports/
│   ├── daily/                  # Daily briefings (YYYY-MM-DD.md)
│   └── weekly/                 # Weekly reports (YYYY-Wxx.md)
├── logs/
│   ├── daily.log
│   └── weekly.log
└── generate_briefing.py        # Briefing generation script
```

### Automation Schedule

| Task | Schedule |
| ---- | -------- |
| Daily investment briefing + Telegram delivery | Every day at 09:00 KST |
| Weekly portfolio report generation | Every Monday at 09:10 KST |

### Setup Steps

| Step | Content |
| ---- | ------- |
| [Step 1](./openclaw/docs/step1-project-setup.md) | Create project folders and data files |
| [Step 2](./openclaw/docs/step2-skills.md) | Register OpenClaw skills |
| [Step 3](./openclaw/docs/step3-briefing-script.md) | Create briefing Python script |
| [Step 4](./openclaw/docs/step4-cron.md) | Set up cron schedule |
| [Step 5](./openclaw/docs/step5-test.md) | Test and verify |

For issues → [troubleshooting.md](./openclaw/docs/troubleshooting.md)

### Manual Execution

```bash
# Run daily briefing immediately
python3 ~/investment-assistant/generate_briefing.py

# Run weekly report immediately
~/.npm-global/bin/openclaw agent \
  --to telegram:YOUR_CHAT_ID --deliver \
  --message "Generate weekly portfolio report. Refer to ~/investment-assistant/data, run weekly-portfolio-report skill, save to ~/investment-assistant/reports/weekly/$(date +%Y-W%V).md"
```

---

## Part 2 — Web App (webapp2)

### Features

| Tab | Functionality |
| --- | ------------- |
| **Dashboard** | Server status, latest report dates, trigger briefing manually |
| **Briefing Viewer** | Render daily/weekly Markdown (▲▼ color highlights) |
| **Portfolio** | View, add, edit, delete holdings |
| **Watchlist** | View, add, edit, delete watchlist stocks |

### Backend Structure

| File | Role |
| ---- | ---- |
| `main.py` | FastAPI app creation, CORS, router registration, static files, `/health` · `/api/status` · `/api/run-briefing` |
| `config.py` | All paths under `~/investment-assistant/` managed with `Path.expanduser()`. Change paths here only. |
| `routers/reports.py` | Glob `reports/daily/*.md` · `reports/weekly/*.md` — returns list and file contents |
| `routers/portfolio.py` | `portfolio.csv` CRUD. Case-insensitive ticker matching, UTF-8 encoding |
| `routers/watchlist.py` | `watchlist.csv` CRUD. Same structure |
| `routers/enrich.py` | yfinance quote lookup + Azure OpenAI watchlist analysis |

#### CSV Column Structure

`portfolio.csv`:

```text
ticker, company_name, market, holding_status, quantity, avg_cost,
currency, target_weight, thesis, risk_notes, priority
```

`watchlist.csv`:

```text
ticker, company_name, market, watch_reason, ideal_entry,
trigger_condition, invalidation, risk_notes, priority
```

### Frontend (`static/index.html`)

Single-file SPA with no build tools. Loads Tailwind CSS and marked.js from CDN.

| Component | Description |
| --------- | ----------- |
| **State management** | Single `const S = { tab, portfolioData, watchlistData, ... }` object |
| **Tab switching** | `switchTab(name)` renders only the active view |
| **API calls** | `async function api(method, path, body)` wrapper — errors normalized via `parseApiError()` |
| **Auto-fill** | `autoFillPortfolio()` (yfinance), `autoFillWatchlist()` (Azure OpenAI) — fills empty fields only |
| **Button lock** | `setModalBtns(formId, disabled)` — prevents double submission during API calls |
| **Markdown rendering** | `renderMarkdown()` + `colorizeTree()` — highlights ▲▼ symbols in green/red |
| **Lookup map** | `_pfMap`, `_wlMap` — references row data from `onclick` without JSON serialization |
| **i18n** | `t(key)` helper + `data-i18n` attribute-based translation. Supports Korean, English, Japanese, Chinese, French. Selection persisted in `localStorage` |

### Auto-fill Policy

#### Adding to Portfolio

1. When ticker loses focus, calls `GET /api/enrich/{ticker}` → auto-fills company name, market, currency
2. On API failure, heuristic fallback (5–6 digit number → KRX/KRW, letters → NASDAQ/USD)
3. Selecting from watchlist dropdown fills empty fields from watchlist data (stocks already in portfolio are excluded)

#### Adding to Watchlist

- When ticker or stock name loses focus, calls `GET /api/enrich/watchlist/{query}?lang={lang}`
- yfinance news (5 items) + Azure OpenAI (gpt-4o) → generates analysis text in selected language (ko/en/ja/zh/fr)
- Generated fields: watch reason, ideal entry price, trigger condition, invalidation condition, risk notes, priority
- Azure OpenAI reads `~/.openclaw/openclaw.json` on the VM directly (no extra env vars needed)

All auto-fill only populates empty fields — values already entered by the user are preserved.

### API Endpoints

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET | `/health` | Health check (used by deployment automation) |
| GET | `/api/status` | Server status and latest report dates |
| GET | `/api/reports/daily` | List daily briefings |
| GET | `/api/reports/daily/{date}` | Get specific date briefing |
| GET | `/api/reports/weekly` | List weekly reports |
| GET | `/api/reports/weekly/{week}` | Get specific week report |
| POST | `/api/run-briefing` | Trigger briefing script immediately |
| GET | `/api/portfolio` | Get all portfolio holdings |
| POST | `/api/portfolio` | Add holding |
| PUT | `/api/portfolio/{ticker}` | Update holding |
| DELETE | `/api/portfolio/{ticker}` | Delete holding |
| GET | `/api/watchlist` | Get all watchlist stocks |
| POST | `/api/watchlist` | Add watchlist stock |
| PUT | `/api/watchlist/{ticker}` | Update watchlist stock |
| DELETE | `/api/watchlist/{ticker}` | Delete watchlist stock |
| GET | `/api/enrich/{ticker}` | Get stock info via yfinance |
| GET | `/api/enrich/watchlist/{query}?lang=en` | ticker/name → AI watchlist fields (lang: ko/en/ja/zh/fr) |

Swagger UI: `http://<VM_IP>:8002/docs`

### Running the App

#### Development (hot reload)

```bash
cd ~/investment-assistant/webapp
pip install -r requirements.txt --break-system-packages
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Open `http://<VM_IP>:8000` in your browser.

#### Production (port 8002, systemd)

Production deployment is handled automatically by GitHub Actions. Pushing changes to `webapp/**` on the `main` branch triggers auto-deployment.

```bash
# Check service status
sudo systemctl status webapp2

# Tail logs
journalctl -u webapp2 -f

# Manual restart
sudo systemctl restart webapp2
```

#### Initial Server Setup (one-time)

```bash
# 1) Create deployment directory
mkdir -p ~/webapp2

# 2) Register systemd service
sudo bash -c 'cat > /etc/systemd/system/webapp2.service << EOF
[Unit]
Description=Investment Assistant Web App v2
After=network.target

[Service]
Type=simple
User=hahaysh
WorkingDirectory=/home/hahaysh/webapp2
ExecStart=/home/hahaysh/myenv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8002
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF'

# 3) Grant GitHub Actions permission to restart the service
echo "hahaysh ALL=(ALL) NOPASSWD: /bin/systemctl restart webapp2, /bin/systemctl is-active webapp2" \
  | sudo tee /etc/sudoers.d/webapp2-deploy
sudo chmod 440 /etc/sudoers.d/webapp2-deploy

# 4) Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable webapp2
```

#### Nginx Reverse Proxy

```bash
sudo apt install -y nginx
sudo cp ~/investment-assistant/webapp/nginx-investment.conf /etc/nginx/sites-available/investment
sudo ln -s /etc/nginx/sites-available/investment /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

### GitHub Actions Auto-Deploy

`.github/workflows/deploy-webapp2.yml` — automatically deploys to the VM on every push to `main`.

#### Required GitHub Secrets

| Secret | Description |
| ------ | ----------- |
| `HAHAYSHOPENCLAWSSH` | VM SSH private key |
| `DEPLOY_SSH_HOST` | VM public IP or FQDN |
| `DEPLOY_SSH_USER` | VM login username |

#### Deployment Flow

```text
push / manual trigger
  → Verify SSH connection
  → Back up current webapp2 (timestamped)
  → rsync ./webapp/ → ~/webapp2/
  → pip install -r requirements.txt
  → systemctl restart webapp2
  → Health check /health + /api/status (up to 30 retries)
  → Auto-rollback from backup on failure
  → Always print last 80 lines of service logs
  → Auto-delete backups older than 7 days
```

#### Manual Trigger Options

GitHub → Actions → `Deploy webapp2 to Azure Linux VM` → `Run workflow`

| Option | Description |
| ------ | ----------- |
| `dry_run=true` | Show rsync diff only, no actual deployment |
| `rollback_on_failure=false` | Skip rollback on failure |

### Azure NSG Port Rules

| | Development | Production |
| - | ----------- | ---------- |
| Destination port | **8000** | **8002** |
| Protocol | TCP | TCP |
| Priority | 310 | 320 |
| Name | Allow-8000 | Allow-8002 |

> In production, it is recommended to expose only port 80 via Nginx and close port 8002.

**Note:** Manage stock data through the web app UI. If editing CSV files directly, always save as UTF-8 and do not modify the column headers in the first row.
