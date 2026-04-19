# 투자 비서 프로젝트 (Investment Assistant)

## 프로젝트 개요

Azure Linux VM에서 실행되는 개인 투자 비서 시스템.
- **매일 KST 09:00**: yfinance로 시장 데이터 수집 → 일일 브리핑 마크다운 생성 → Telegram 요약 전송
- **매주 월요일 KST 09:10**: 주간 포트폴리오 리포트 생성 → Telegram 전송
- **웹앱(FastAPI)**: 브리핑 열람, 포트폴리오/watchlist CRUD, AI 종목 자동채움

---

## 인프라

### Azure Linux VM
- **사용자**: `hahaysh`
- **홈 디렉토리**: `/home/hahaysh`
- **Timezone**: UTC (KST = UTC+9, KST 09:00 → cron `0 0 * * *`)
- SSH로 접속하여 직접 작업

### OpenClaw
- **설치 경로**: `/home/hahaysh/.npm-global/bin/openclaw`
- **설정 파일**: `~/.openclaw/openclaw.json`
- **모델**: Microsoft Azure Foundry (gpt-4o / gpt-5-mini)
  - 웹 검색 기능 없음 → 시장 데이터는 yfinance로 직접 수집
- **Telegram 연동**: OpenClaw를 통해 Telegram으로 브리핑 전송
- **Telegram chat ID**: `7733177955` (세션 파일: `~/.openclaw/agents/main/sessions/sessions.json`)
- **스킬 위치**: `~/.openclaw/skills/`

### OpenClaw 스킬 2개
1. `daily-investment-briefing`: 일일 브리핑 생성 스킬
2. `weekly-portfolio-report`: 주간 리포트 생성 스킬
- 스킬 정의 파일: [openclaw/docs/step2-skills.md](openclaw/docs/step2-skills.md)

---

## 디렉토리 구조 (VM 기준)

```
~/investment-assistant/
├── data/
│   ├── investor_profile.md    # 투자자 프로필 (유승호)
│   ├── portfolio.csv          # 보유 종목
│   └── watchlist.csv          # 관심 종목
├── reports/
│   ├── daily/YYYY-MM-DD.md   # 일일 브리핑
│   └── weekly/YYYY-Wxx.md    # 주간 리포트
├── logs/
│   ├── daily.log
│   └── weekly.log
├── generate_briefing.py       # 일일 브리핑 스크립트
└── webapp/                    # FastAPI 웹앱 (아래 참조)
```

---

## 투자자 프로필 (유승호)

- **투자 경력**: 3년, 자산 통화: KRW + USD
- **스타일**: Value, Quality, Cash Flow 중심, Shareholder Return, 중장기 보유
- **선호 섹터**: 한국(반도체, 금융, 자동차), 미국(금융, 헬스케어, 에너지, 고품질 플랫폼)

### 포트폴리오 (주요 종목)
| 티커 | 종목 | 시장 |
|------|------|------|
| 005930 | 삼성전자 | KRX |
| 000660 | SK하이닉스 | KRX |
| 005380 | 현대차 | KRX |
| 105560 | KB금융 | KRX |
| JPM | JPMorgan Chase | NYSE |
| UNH | UnitedHealth Group | NYSE |
| XOM | ExxonMobil | NYSE |
| BRK.B | Berkshire Hathaway B | NYSE |

### Watchlist (주요 종목)
NAVER(035420), 카카오(035720), MSFT, GOOGL, 기아(000270), CVX

---

## generate_briefing.py

**위치**: `~/investment-assistant/generate_briefing.py`

**동작 순서**:
1. yfinance로 매크로 데이터 수집 (KOSPI, KOSDAQ, S&P500, NASDAQ, USDKRW, 미국10년물, DXY, WTI, 금, VIX)
2. portfolio.csv 읽어 보유 종목 주가 수집
3. 마크다운 브리핑 `reports/daily/YYYY-MM-DD.md` 저장
4. `openclaw message send --channel telegram --target 7733177955` 로 요약 전송
5. `openclaw agent` 로 시나리오/액션 섹션 자동 채우기

**KRX ticker 매핑**: yfinance는 `.KS` 접미사 필요 (`005930` → `005930.KS`), `BRK.B` → `BRK-B`

---

## cron 스케줄

```cron
# 일일 브리핑 - 매일 09:00 KST (UTC 00:00)
0 0 * * * python3 /home/hahaysh/investment-assistant/generate_briefing.py >> /home/hahaysh/investment-assistant/logs/daily.log 2>&1

# 주간 리포트 - 매주 월요일 09:10 KST (UTC 00:10)
10 0 * * 1 /home/hahaysh/.npm-global/bin/openclaw agent --to telegram:7733177955 --deliver --message "주간 포트폴리오 리포트 ..."
```

**주의**: cron에서 openclaw 전체 경로 필수 (`which openclaw` → `/home/hahaysh/.npm-global/bin/openclaw`)

---

## 웹앱 (FastAPI)

**위치**: `~/investment-assistant/webapp/` (이 저장소의 [webapp/](webapp/) 폴더)

### 실행

```bash
# 개발
bash ~/investment-assistant/webapp/start.sh

# 운영 (systemd) — 서비스명: webapp2
sudo systemctl start webapp2
sudo systemctl status webapp2
journalctl -u webapp2 -f
```

**서비스 파일**: [webapp/investment-webapp.service](webapp/investment-webapp.service)
- User: `hahaysh`
- WorkingDirectory: `/home/hahaysh/webapp2`
- 포트: 8002 (uvicorn), nginx가 80 → 8002 프록시

### Nginx

**설정 파일**: [webapp/nginx-investment.conf](webapp/nginx-investment.conf)

```bash
sudo cp nginx-investment.conf /etc/nginx/sites-available/investment
sudo ln -s /etc/nginx/sites-available/investment /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### API 라우터

| 경로 | 파일 | 기능 |
|------|------|------|
| `/api/reports/daily` | [webapp/routers/reports.py](webapp/routers/reports.py) | 일일 브리핑 목록/조회 |
| `/api/reports/weekly` | webapp/routers/reports.py | 주간 리포트 목록/조회 |
| `/api/portfolio` | [webapp/routers/portfolio.py](webapp/routers/portfolio.py) | 포트폴리오 CRUD |
| `/api/watchlist` | [webapp/routers/watchlist.py](webapp/routers/watchlist.py) | 관심종목 CRUD |
| `/api/enrich/{ticker}` | [webapp/routers/enrich.py](webapp/routers/enrich.py) | yfinance 종목 정보 조회 |
| `/api/enrich/watchlist/{query}` | webapp/routers/enrich.py | AI 관심종목 자동채움 |
| `/api/run-briefing` | [webapp/main.py](webapp/main.py) | 브리핑 수동 실행 |
| `/api/status` | webapp/main.py | 최신 리포트 날짜 조회 |

### enrich 라우터 특이사항
- `~/.openclaw/openclaw.json`에서 Azure OpenAI 접속 정보를 읽어 LLM 호출
- 별도 환경변수 불필요, OpenClaw 설정 파일 그대로 사용
- KRX 종목 자동 판별 (5~6자리 숫자) → `.KS`/`.KQ` 후보 순서대로 시도

### 데이터 경로 (config.py)
```python
DATA_DIR = Path("~/investment-assistant/data").expanduser()
DAILY_REPORTS_DIR = Path("~/investment-assistant/reports/daily").expanduser()
WEEKLY_REPORTS_DIR = Path("~/investment-assistant/reports/weekly").expanduser()
BRIEFING_SCRIPT = Path("~/investment-assistant/generate_briefing.py").expanduser()
```

---

## 알려진 문제 / 트러블슈팅

| 문제 | 해결 |
|------|------|
| `openclaw message "..."` 오류 | `openclaw agent --to telegram:ID --message "..." --deliver` 또는 `openclaw message send --channel telegram --target ID --message "..."` 사용 |
| cron에서 openclaw not found | 전체 경로 사용: `/home/hahaysh/.npm-global/bin/openclaw` |
| yfinance 웹 검색 403 오류 | Microsoft Foundry 모델은 웹 검색 불가 → yfinance Python 스크립트로 직접 수집 |
| KRX 종목 주가 조회 실패 | `005930` → `005930.KS`, `BRK.B` → `BRK-B` |
| 브리핑 시나리오 섹션 비어있음 | `openclaw agent`가 파일에 실제로 저장 안 하는 경우 있음 → generate_briefing.py가 직접 저장 처리 |

---

## 설치 가이드 (새 VM 세팅 시)

순서대로 진행:
1. [step1-project-setup.md](openclaw/docs/step1-project-setup.md) — 폴더/데이터 파일 생성
2. [step2-skills.md](openclaw/docs/step2-skills.md) — OpenClaw 스킬 등록
3. [step3-briefing-script.md](openclaw/docs/step3-briefing-script.md) — generate_briefing.py 생성
4. [step4-cron.md](openclaw/docs/step4-cron.md) — cron 스케줄 등록
5. [step5-test.md](openclaw/docs/step5-test.md) — 전체 검증
- [troubleshooting.md](openclaw/docs/troubleshooting.md) — 트러블슈팅

---

## 이 저장소 구조

```
investment-assistant/          ← 로컬 Windows 개발 환경
├── CLAUDE.md                  ← 이 파일
├── webapp/                    ← FastAPI 웹앱 소스 (VM에 배포)
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
│       └── translations/      ← 다국어 번역 (ko/en/ja/zh/fr)
└── openclaw/                  ← OpenClaw 설정/문서
    ├── docs/                  ← 단계별 세팅 가이드
    └── scripts/setup.sh
```
