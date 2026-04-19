# 🦞 OpenClaw 개인 투자 비서

> 🇺🇸 [English README](README.md)

Azure Linux VM에서 OpenClaw AI Agent가 매일 투자 브리핑을 자동 생성하고, FastAPI 웹앱으로 포트폴리오·관심종목을 관리하는 개인 투자 관리 시스템입니다.

> **🌐 서비스 접속:** [http://hahayshopenclaw.koreacentral.cloudapp.azure.com:8002/](http://hahayshopenclaw.koreacentral.cloudapp.azure.com:8002/)

---

## 시스템 아키텍처

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
│                             │  │  ├─ yfinance  (시세/뉴스)  │   │ │
│                             │  │  └─ Azure OpenAI (gpt-4o)  │   │ │
│                             │  └────────────────────────────┘   │ │
│                             └──────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘

GitHub ──(push)──► GitHub Actions ──(rsync)──► webapp2  (자동 배포)
```

### 데이터 흐름

| 흐름 | 설명 |
| ---- | ---- |
| **OpenClaw → 파일** | AI Agent가 매일/매주 브리핑을 `reports/` 폴더에 마크다운으로 저장 |
| **파일 → FastAPI** | FastAPI가 CSV·마크다운을 직접 읽어 API로 제공 (DB 없음) |
| **FastAPI → 프론트** | REST API + 정적 파일 서빙을 FastAPI 단일 서버에서 처리 |
| **yfinance → enrich** | 종목 ticker 입력 시 실시간 시세·뉴스 조회 |
| **Azure OpenAI → enrich** | yfinance 뉴스 기반 관심종목 분석 텍스트 자동 생성 (gpt-4o) |

---

## 레포 구조

```text
investment-assistant/
├── .github/
│   └── workflows/
│       └── deploy-webapp2.yml       # GitHub Actions 자동 배포
│
├── openclaw/                        # OpenClaw AI Agent 설정
│   ├── skills/
│   │   ├── daily-investment-briefing/   # 일일 브리핑 생성 스킬
│   │   └── weekly-portfolio-report/     # 주간 리포트 생성 스킬
│   ├── scripts/
│   │   └── setup.sh
│   └── docs/                        # 단계별 설정 가이드
│       ├── step1-project-setup.md
│       ├── step2-skills.md
│       ├── step3-briefing-script.md
│       ├── step4-cron.md
│       ├── step5-test.md
│       └── troubleshooting.md
│
└── webapp/                          # 웹앱 소스코드
    ├── main.py                      # FastAPI 앱 진입점, 라우터 등록
    ├── config.py                    # 전체 파일 경로 상수 관리
    ├── requirements.txt
    ├── start.sh                     # 개발 서버 시작 스크립트
    ├── investment-webapp.service    # systemd 서비스 템플릿
    ├── nginx-investment.conf        # Nginx 리버스 프록시 설정
    ├── routers/
    │   ├── reports.py               # 일일·주간 리포트 API
    │   ├── portfolio.py             # 포트폴리오 CRUD API
    │   ├── watchlist.py             # 관심종목 CRUD API
    │   └── enrich.py                # 종목 정보 조회 + AI 자동채움 API
    └── static/
        ├── index.html               # SPA 프론트엔드 (전체 UI)
        └── translations/            # 다국어 번역 파일
            ├── ko.js                # 한국어
            ├── en.js                # English
            ├── ja.js                # 日本語
            ├── zh.js                # 中文
            └── fr.js                # Français
```

---

## 사전 요구사항

- Ubuntu 24.04 LTS (Azure VM 기준)
- Python 3.x + pip
- OpenClaw 설치 및 실행 중 (`openclaw-gateway` 프로세스)
- Telegram 봇 연결 완료
- Azure OpenAI 리소스 (OpenClaw에 연결된 것을 그대로 사용)

---

## Part 1 — OpenClaw 자동화

### VM 운영 디렉토리

```text
~/investment-assistant/
├── data/
│   ├── investor_profile.md     # 투자자 프로필
│   ├── portfolio.csv           # 보유 종목
│   └── watchlist.csv           # 관심 종목
├── reports/
│   ├── daily/                  # 일일 브리핑 (YYYY-MM-DD.md)
│   └── weekly/                 # 주간 리포트 (YYYY-Wxx.md)
├── logs/
│   ├── daily.log
│   └── weekly.log
└── generate_briefing.py        # 브리핑 생성 스크립트
```

### 자동화 기능

| 기능 | 일정 |
| ---- | ---- |
| 일일 투자 브리핑 생성 + Telegram 전송 | 매일 09:00 KST |
| 주간 포트폴리오 리포트 생성 | 매주 월요일 09:10 KST |

### 설치 순서

| 단계 | 내용 |
| ---- | ---- |
| [Step 1](./openclaw/docs/step1-project-setup.md) | 프로젝트 폴더 및 데이터 파일 생성 |
| [Step 2](./openclaw/docs/step2-skills.md) | OpenClaw 스킬 등록 |
| [Step 3](./openclaw/docs/step3-briefing-script.md) | 브리핑 생성 Python 스크립트 |
| [Step 4](./openclaw/docs/step4-cron.md) | cron 자동 스케줄 등록 |
| [Step 5](./openclaw/docs/step5-test.md) | 테스트 및 검증 |

문제 발생 시 → [troubleshooting.md](./openclaw/docs/troubleshooting.md)

### 수동 실행

```bash
# 일일 브리핑 즉시 실행
python3 ~/investment-assistant/generate_briefing.py

# 주간 리포트 즉시 실행
~/.npm-global/bin/openclaw agent \
  --to telegram:YOUR_CHAT_ID --deliver \
  --message "주간 포트폴리오 리포트 생성해줘. ~/investment-assistant/data 참조해서 weekly-portfolio-report 스킬 실행하고 ~/investment-assistant/reports/weekly/$(date +%Y-W%V).md 로 저장해줘."
```

---

## Part 2 — 웹앱 (webapp2)

### 기능 요약

| 탭 | 기능 |
| -- | ---- |
| **대시보드** | 서버 상태, 최신 리포트 날짜 확인, 브리핑 즉시 실행 |
| **브리핑 뷰어** | 일일·주간 마크다운 렌더링 (▲▼ 색상 강조) |
| **포트폴리오 현황** | 보유 종목 조회·추가·수정·삭제 |
| **관심종목** | 관심 종목 조회·추가·수정·삭제 |

### 백엔드 구조

| 파일 | 역할 |
| ---- | ---- |
| `main.py` | FastAPI 앱 생성, CORS 설정, 라우터 등록, 정적 파일 서빙, `/health` · `/api/status` · `/api/run-briefing` |
| `config.py` | `~/investment-assistant/` 하위 모든 경로를 `Path.expanduser()`로 관리. 경로 변경 시 이 파일만 수정 |
| `routers/reports.py` | `reports/daily/*.md` · `reports/weekly/*.md` glob으로 목록 반환 및 파일 내용 읽기 |
| `routers/portfolio.py` | `portfolio.csv` CRUD. ticker 대소문자 무관 매칭, UTF-8 인코딩 |
| `routers/watchlist.py` | `watchlist.csv` CRUD. 동일 구조 |
| `routers/enrich.py` | yfinance 시세 조회 + Azure OpenAI 관심종목 분석 |

#### CSV 컬럼 구조

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

### 프론트엔드 (`static/index.html`)

빌드 도구 없는 단일 파일 SPA입니다. CDN으로 Tailwind CSS와 marked.js를 로드합니다.

| 구성 요소 | 설명 |
| --------- | ---- |
| **상태 관리** | `const S = { tab, portfolioData, watchlistData, ... }` 단일 객체로 전체 상태 관리 |
| **탭 전환** | `switchTab(name)` 호출 시 해당 뷰만 렌더링 |
| **API 통신** | `async function api(method, path, body)` 래퍼 — 에러를 `parseApiError()`로 정제 |
| **자동채움** | `autoFillPortfolio()` (yfinance), `autoFillWatchlist()` (Azure OpenAI) — 빈 필드만 채우는 정책 |
| **버튼 잠금** | `setModalBtns(formId, disabled)` — API 호출 중 이중 제출 방지 |
| **마크다운 렌더링** | `renderMarkdown()` + `colorizeTree()` — ▲▼ 기호를 색상(초록/빨강)으로 강조 |
| **lookup map** | `_pfMap`, `_wlMap` — `onclick` 속성에서 JSON 직렬화 없이 행 데이터를 참조 |
| **다국어 지원** | `t(key)` 헬퍼 + `data-i18n` 속성 기반 번역. 한국어·영어·일본어·중국어·프랑스어 지원. 선택 언어는 `localStorage`에 저장 |

### 자동채움 정책

#### 포트폴리오 추가

1. ticker 입력 후 포커스 이동 시 `GET /api/enrich/{ticker}` 호출 → 회사명·시장·통화 자동채움
2. API 실패 시 heuristic fallback (숫자 5~6자리 → KRX/KRW, 알파벳 → NASDAQ/USD)
3. 관심종목 드롭다운에서 선택하면 watchlist 데이터로 빈 필드 채움 (이미 포트폴리오에 있는 종목은 목록에서 제외)

#### 관심종목 추가

- ticker 또는 종목명 입력 후 포커스 이동 시 `GET /api/enrich/watchlist/{query}?lang={lang}` 호출
- yfinance 뉴스 5건 + Azure OpenAI(gpt-4o) → 선택 언어로 분석 텍스트 생성 (한국어·영어·일본어·중국어·프랑스어)
- 생성 필드: 관심 이유, 이상적 진입가, 트리거 조건, 무효화 조건, 리스크 노트, 우선순위
- Azure OpenAI는 VM의 `~/.openclaw/openclaw.json` 설정을 그대로 읽어 사용 (별도 환경변수 불필요)

모든 자동채움은 빈 필드만 채우며, 사용자가 이미 입력한 값은 유지합니다.

### 주요 API 엔드포인트

| 메서드 | 경로 | 설명 |
| ------ | ---- | ---- |
| GET | `/health` | 헬스체크 (배포 자동화용) |
| GET | `/api/status` | 서버 상태 및 최신 리포트 날짜 |
| GET | `/api/reports/daily` | 일일 브리핑 목록 |
| GET | `/api/reports/daily/{date}` | 특정 날짜 브리핑 내용 |
| GET | `/api/reports/weekly` | 주간 리포트 목록 |
| GET | `/api/reports/weekly/{week}` | 특정 주차 리포트 내용 |
| POST | `/api/run-briefing` | 브리핑 스크립트 즉시 실행 |
| GET | `/api/portfolio` | 포트폴리오 전체 조회 |
| POST | `/api/portfolio` | 종목 추가 |
| PUT | `/api/portfolio/{ticker}` | 종목 수정 |
| DELETE | `/api/portfolio/{ticker}` | 종목 삭제 |
| GET | `/api/watchlist` | 관심종목 전체 조회 |
| POST | `/api/watchlist` | 관심종목 추가 |
| PUT | `/api/watchlist/{ticker}` | 관심종목 수정 |
| DELETE | `/api/watchlist/{ticker}` | 관심종목 삭제 |
| GET | `/api/enrich/{ticker}` | ticker 종목 정보 조회 (yfinance) |
| GET | `/api/enrich/watchlist/{query}?lang=ko` | ticker·종목명 → AI 관심종목 필드 생성 (lang: ko/en/ja/zh/fr) |

Swagger UI: `http://<VM_IP>:8002/docs`

### 실행 방법

#### 개발 환경 (핫 리로드)

```bash
cd ~/investment-assistant/webapp
pip install -r requirements.txt --break-system-packages
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

브라우저에서 `http://<VM_IP>:8000` 접속

#### 운영 환경 (포트 8002, systemd)

운영 배포는 GitHub Actions가 자동으로 처리합니다. `main` 브랜치에 `webapp/**` 변경이 push되면 자동 배포됩니다.

```bash
# 서비스 상태 확인
sudo systemctl status webapp2

# 로그 실시간 확인
journalctl -u webapp2 -f

# 수동 재시작
sudo systemctl restart webapp2
```

#### 초기 서버 설정 (최초 1회)

```bash
# 1) 배포 디렉토리 생성
mkdir -p ~/webapp2

# 2) systemd 서비스 등록
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

# 3) GitHub Actions 서비스 재시작 권한 설정
echo "hahaysh ALL=(ALL) NOPASSWD: /bin/systemctl restart webapp2, /bin/systemctl is-active webapp2" \
  | sudo tee /etc/sudoers.d/webapp2-deploy
sudo chmod 440 /etc/sudoers.d/webapp2-deploy

# 4) 서비스 등록
sudo systemctl daemon-reload
sudo systemctl enable webapp2
```

#### Nginx 리버스 프록시

```bash
sudo apt install -y nginx
sudo cp ~/investment-assistant/webapp/nginx-investment.conf /etc/nginx/sites-available/investment
sudo ln -s /etc/nginx/sites-available/investment /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

### GitHub Actions 자동 배포

`.github/workflows/deploy-webapp2.yml` — `main` 브랜치 push 시 VM에 자동 배포합니다.

#### 필요한 GitHub Secrets

| Secret | 설명 |
| ------ | ---- |
| `HAHAYSHOPENCLAWSSH` | VM SSH 개인키 |
| `DEPLOY_SSH_HOST` | VM 공인 IP 또는 FQDN |
| `DEPLOY_SSH_USER` | VM 로그인 사용자명 |

#### 배포 흐름

```text
push / 수동 트리거
  → SSH 연결 확인
  → 현재 webapp2 백업 (타임스탬프)
  → rsync ./webapp/ → ~/webapp2/
  → pip install -r requirements.txt
  → systemctl restart webapp2
  → /health + /api/status 헬스체크 (최대 30회 재시도)
  → 실패 시 백업에서 자동 롤백
  → 항상 서비스 로그 80줄 출력
  → 7일 지난 백업 자동 삭제
```

#### 수동 트리거 옵션

GitHub → Actions → `Deploy webapp2 to Azure Linux VM` → `Run workflow`

| 옵션 | 설명 |
| ---- | ---- |
| `dry_run=true` | rsync 변경 목록만 출력, 실제 배포 없음 |
| `rollback_on_failure=false` | 실패 시 롤백 건너뜀 |

### Azure NSG 포트 오픈

| 항목 | 개발용 | 운영용 |
| ---- | ------ | ------ |
| 대상 포트 | **8000** | **8002** |
| 프로토콜 | TCP | TCP |
| 우선순위 | 310 | 320 |
| 이름 | Allow-8000 | Allow-8002 |

> 운영 환경에서는 Nginx를 통해 포트 80만 오픈하고 8002는 닫는 것을 권장합니다.

**참고**: 종목 데이터는 웹앱 UI를 통해 관리하세요. CSV를 직접 편집할 경우 반드시 UTF-8 인코딩으로 저장하고 첫 행의 컬럼 헤더를 변경하지 마세요.
