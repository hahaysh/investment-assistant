# Investment Assistant Project

## Project Overview

A personal investment assistant system running on an Azure Linux VM.
- **Daily at 09:00 KST**: Collect market data via yfinance → generate daily briefing Markdown → send Telegram summary
- **Every Monday at 09:10 KST**: Generate weekly portfolio report → send via Telegram
- **Web App (FastAPI)**: View briefings, manage portfolio/watchlist CRUD, AI stock auto-fill

---

## Infrastructure

### Azure Linux VM
- **User**: `hahaysh`
- **Home directory**: `/home/hahaysh`
- **Timezone**: UTC (KST = UTC+9, KST 09:00 → cron `0 0 * * *`)
- Access via SSH for direct operations

### OpenClaw
- **Install path**: `/home/hahaysh/.npm-global/bin/openclaw`
- **Config file**: `~/.openclaw/openclaw.json`
- **Model**: Microsoft Azure Foundry (gpt-4o / gpt-5-mini)
  - No web search capability → market data collected directly via yfinance
- **Telegram integration**: Briefings sent to Telegram via OpenClaw
- **Telegram chat ID**: `7733177955` (session file: `~/.openclaw/agents/main/sessions/sessions.json`)
- **Skills directory**: `~/.openclaw/skills/`

### OpenClaw Skills (2 skills)
1. `daily-investment-briefing`: Daily briefing generation skill
2. `weekly-portfolio-report`: Weekly report generation skill
- Skill definition file: [openclaw/docs/step2-skills.md](openclaw/docs/step2-skills.md)

---

## Directory Structure (VM)

```
~/investment-assistant/
├── data/
│   ├── investor_profile.md    # Investor profile
│   ├── portfolio.csv          # Holdings
│   └── watchlist.csv          # Watchlist
├── reports/
│   ├── daily/YYYY-MM-DD.md   # Daily briefings
│   └── weekly/YYYY-Wxx.md    # Weekly reports
├── logs/
│   ├── daily.log
│   └── weekly.log
├── generate_briefing.py       # Daily briefing script
└── webapp/                    # FastAPI web app (see below)
```

---

## Investor Profile

- **Experience**: 3 years, assets in KRW + USD
- **Style**: Value, Quality, Cash Flow focused, Shareholder Return, medium-to-long-term holding
- **Preferred sectors**: Korea (semiconductors, financials, autos), US (financials, healthcare, energy, quality platforms)

### Portfolio (Key Holdings)
| Ticker | Company | Market |
|--------|---------|--------|
| 005930 | Samsung Electronics | KRX |
| 000660 | SK Hynix | KRX |
| 005380 | Hyundai Motor | KRX |
| 105560 | KB Financial | KRX |
| JPM | JPMorgan Chase | NYSE |
| UNH | UnitedHealth Group | NYSE |
| XOM | ExxonMobil | NYSE |
| BRK.B | Berkshire Hathaway B | NYSE |

### Watchlist (Key Stocks)
NAVER(035420), Kakao(035720), MSFT, GOOGL, Kia(000270), CVX

---

## generate_briefing.py

**Location**: `~/investment-assistant/generate_briefing.py`

**Execution order**:
1. Collect macro data via yfinance (KOSPI, KOSDAQ, S&P500, NASDAQ, USDKRW, US 10Y yield, DXY, WTI, Gold, VIX)
2. Read portfolio.csv and collect stock prices for holdings
3. Save Markdown briefing to `reports/daily/YYYY-MM-DD.md`
4. Send summary via `openclaw message send --channel telegram --target 7733177955`
5. Auto-fill scenario/action sections via `openclaw agent`

**KRX ticker mapping**: yfinance requires `.KS` suffix (`005930` → `005930.KS`), `BRK.B` → `BRK-B`

---

## Cron Schedule

```cron
# Daily briefing - every day at 09:00 KST (UTC 00:00)
0 0 * * * python3 /home/hahaysh/investment-assistant/generate_briefing.py >> /home/hahaysh/investment-assistant/logs/daily.log 2>&1

# Weekly report - every Monday at 09:10 KST (UTC 00:10)
10 0 * * 1 /home/hahaysh/.npm-global/bin/openclaw agent --to telegram:7733177955 --deliver --message "Generate weekly portfolio report ..."
```

**Note**: Full path required for openclaw in cron (`which openclaw` → `/home/hahaysh/.npm-global/bin/openclaw`)

---

## Web App (FastAPI)

**Location**: `~/investment-assistant/webapp/` (this repo's [webapp/](webapp/) folder)

### Running

```bash
# Development
bash ~/investment-assistant/webapp/start.sh

# Production (systemd) — service name: webapp2
sudo systemctl start webapp2
sudo systemctl status webapp2
journalctl -u webapp2 -f
```

**Service file**: [webapp/investment-webapp.service](webapp/investment-webapp.service)
- User: `hahaysh`
- WorkingDirectory: `/home/hahaysh/webapp2`
- Port: 8002 (uvicorn), nginx proxies 80 → 8002

### Nginx

**Config file**: [webapp/nginx-investment.conf](webapp/nginx-investment.conf)

```bash
sudo cp nginx-investment.conf /etc/nginx/sites-available/investment
sudo ln -s /etc/nginx/sites-available/investment /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### API Routers

| Path | File | Function |
|------|------|----------|
| `/api/reports/daily` | [webapp/routers/reports.py](webapp/routers/reports.py) | Daily briefing list/content |
| `/api/reports/weekly` | webapp/routers/reports.py | Weekly report list/content |
| `/api/portfolio` | [webapp/routers/portfolio.py](webapp/routers/portfolio.py) | Portfolio CRUD |
| `/api/watchlist` | [webapp/routers/watchlist.py](webapp/routers/watchlist.py) | Watchlist CRUD |
| `/api/enrich/{ticker}` | [webapp/routers/enrich.py](webapp/routers/enrich.py) | yfinance stock info lookup |
| `/api/enrich/watchlist/{query}` | webapp/routers/enrich.py | AI watchlist auto-fill |
| `/api/run-briefing` | [webapp/main.py](webapp/main.py) | Trigger briefing manually |
| `/api/status` | webapp/main.py | Latest report date lookup |

### enrich Router Notes
- Reads Azure OpenAI credentials from `~/.openclaw/openclaw.json` for LLM calls
- No separate environment variables needed — uses OpenClaw config file directly
- Auto-detects KRX stocks (5–6 digit numbers) → tries `.KS`/`.KQ` suffixes in order

### Data Paths (config.py)
```python
DATA_DIR = Path("~/investment-assistant/data").expanduser()
DAILY_REPORTS_DIR = Path("~/investment-assistant/reports/daily").expanduser()
WEEKLY_REPORTS_DIR = Path("~/investment-assistant/reports/weekly").expanduser()
BRIEFING_SCRIPT = Path("~/investment-assistant/generate_briefing.py").expanduser()
```

---

## Known Issues / Troubleshooting

| Issue | Solution |
|-------|----------|
| `openclaw message "..."` error | Use `openclaw agent --to telegram:ID --message "..." --deliver` or `openclaw message send --channel telegram --target ID --message "..."` |
| openclaw not found in cron | Use full path: `/home/hahaysh/.npm-global/bin/openclaw` |
| yfinance web search 403 error | Microsoft Foundry models have no web search → collect data directly via yfinance Python script |
| KRX stock price lookup failure | `005930` → `005930.KS`, `BRK.B` → `BRK-B` |
| Briefing scenario section empty | `openclaw agent` sometimes doesn't save to file → generate_briefing.py handles saving directly |

---

## Setup Guide (New VM)

Follow in order:
1. [step1-project-setup.md](openclaw/docs/step1-project-setup.md) — Create folders and data files
2. [step2-skills.md](openclaw/docs/step2-skills.md) — Register OpenClaw skills
3. [step3-briefing-script.md](openclaw/docs/step3-briefing-script.md) — Create generate_briefing.py
4. [step4-cron.md](openclaw/docs/step4-cron.md) — Set up cron schedule
5. [step5-test.md](openclaw/docs/step5-test.md) — Full verification
- [troubleshooting.md](openclaw/docs/troubleshooting.md) — Troubleshooting

---

## Repository Structure

```
investment-assistant/          ← Local Windows development environment
├── CLAUDE.md                  ← This file
├── webapp/                    ← FastAPI web app source (deployed to VM)
│   ├── main.py
│   ├── config.py
│   ├── requirements.txt
│   ├── start.sh
│   ├── investment-webapp.service
│   ├── nginx-investment.conf
│   ├── routers/
│   │   ├── reports.py
│   │   ├── portfolio.py
│   │   ├── watchlist.py
│   │   └── enrich.py
│   └── static/
│       ├── index.html
│       └── translations/      ← i18n translation files (ko/en/ja/zh/fr)
└── openclaw/                  ← OpenClaw configuration and docs
    ├── docs/                  ← Step-by-step setup guides
    └── scripts/setup.sh
```
