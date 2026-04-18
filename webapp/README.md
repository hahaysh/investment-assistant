# 투자 비서 웹앱

FastAPI 백엔드 + Vanilla JS 프론트엔드로 구성된 투자 비서 대시보드입니다.  
CSV/마크다운 파일을 직접 읽어 DB 없이 동작합니다.

---

## 핵심 기능

| 탭 | 기능 |
| -- | ---- |
| **대시보드** | 서버 상태, 최신 일일·주간 리포트 날짜 확인, 브리핑 즉시 실행 |
| **브리핑 뷰어** | 일일 브리핑 / 주간 리포트 마크다운 렌더링 (▲▼ 색상 강조 포함) |
| **포트폴리오 현황** | 보유 종목 목록 조회 · 추가 · 수정 · 삭제 |
| **관심종목** | 관심 종목 목록 조회 · 추가 · 수정 · 삭제 |

### 포트폴리오 종목 추가 시 자동채움

포트폴리오 추가 모달에서 ticker를 입력하고 포커스를 이동하면 두 가지 방식으로 빈 필드를 자동으로 채웁니다.

1. **enrich API 조회** — `GET /api/enrich/{ticker}` 를 호출해 yfinance에서 회사명·시장·통화·현재가를 가져옵니다. 조회에 성공하면 비어 있는 필드에만 값을 채우고, 사용자가 이미 입력한 값은 유지합니다.
2. **heuristic fallback** — enrich API 조회가 실패하더라도 ticker 형식(숫자 5~6자리 → KRX/KRW, 알파벳 → NASDAQ/USD)으로 시장과 통화를 최소한으로 채웁니다. 조회 실패 원인은 화면 하단 토스트 메시지로 안내합니다.

추가 모달에는 관심종목 목록에서 종목을 선택해 빈 필드를 한 번에 채우는 **"관심종목에서 불러오기"** 드롭다운도 제공됩니다. 이미 포트폴리오에 등록된 종목은 목록에서 자동으로 제외됩니다.

### 관심종목 추가 시 AI 자동채움

관심종목 추가 모달에서 ticker 또는 종목명을 입력하고 포커스를 이동하면 AI가 나머지 필드를 자동으로 채웁니다.

- `GET /api/enrich/watchlist/{query}` 를 호출합니다.
- yfinance로 종목 정보와 최근 뉴스 5건을 수집한 뒤 Azure OpenAI(gpt-4o)가 한국어로 분석합니다.
- 생성되는 필드: 관심 이유, 이상적 진입가, 트리거 조건, 무효화 조건, 리스크 노트, 우선순위
- 빈 필드만 채우므로 사용자가 직접 입력한 값은 유지됩니다.
- 조회 중에는 "AI 분석 중..." 상태 표시와 함께 저장·취소 버튼이 비활성화됩니다.
- AI 분석에 실패해도 수동 입력이 가능합니다.

> Azure OpenAI는 VM의 `~/.openclaw/openclaw.json` 설정을 그대로 읽습니다. 별도 환경변수 설정이 필요 없습니다.

### 버튼 잠금 정책

자동채움이 실행되는 동안(API 조회 중, 관심종목 선택 후 필드 채움 중) 저장·취소 버튼이 비활성화됩니다. 채움이 완료되면 즉시 복구됩니다. 이중 제출을 방지하기 위해 저장 요청 중에도 동일하게 적용됩니다.

> **권장**: 종목 데이터는 웹앱 UI를 통해 관리하세요. CSV 파일을 직접 편집할 수도 있지만, 컬럼 순서나 인코딩이 맞지 않으면 앱이 데이터를 올바르게 읽지 못할 수 있습니다.

---

## 실행 방법

### 개발 환경 (핫 리로드)

```bash
cd ~/investment-assistant/webapp
pip install -r requirements.txt --break-system-packages
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

또는 제공된 스크립트 사용:

```bash
bash ~/investment-assistant/webapp/start.sh
```

브라우저에서 `http://<VM_IP>:8000` 접속

### 운영 환경 — webapp2 (포트 8002, systemd)

운영 배포는 GitHub Actions(`deploy-webapp2.yml`)를 통해 자동화되어 있습니다.  
`main` 브랜치에 `webapp/**` 경로 변경이 push되면 자동 배포됩니다.

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
# 1) 저장소 배포 디렉토리 생성
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

# 3) sudo 권한 설정 (GitHub Actions 서비스 재시작용)
echo "hahaysh ALL=(ALL) NOPASSWD: /bin/systemctl restart webapp2, /bin/systemctl is-active webapp2" \
  | sudo tee /etc/sudoers.d/webapp2-deploy
sudo chmod 440 /etc/sudoers.d/webapp2-deploy

# 4) 서비스 등록
sudo systemctl daemon-reload
sudo systemctl enable webapp2
```

### Nginx 리버스 프록시 (포트 80으로 서비스)

```bash
# Nginx 설치 (미설치 시)
sudo apt install -y nginx

# 설정 파일 배포
sudo cp ~/investment-assistant/webapp/nginx-investment.conf /etc/nginx/sites-available/investment
sudo ln -s /etc/nginx/sites-available/investment /etc/nginx/sites-enabled/

# 기존 default 사이트 비활성화 (필요 시)
sudo rm /etc/nginx/sites-enabled/default

# 설정 테스트 및 적용
sudo nginx -t && sudo systemctl reload nginx
```

---

## GitHub Actions 자동 배포

`.github/workflows/deploy-webapp2.yml` 워크플로우가 `main` 브랜치 push 시 VM에 자동 배포합니다.

### 필요한 GitHub Secrets

| Secret | 설명 |
| ------ | ---- |
| `HAHAYSHOPENCLAWSSH` | VM SSH 개인키 |
| `DEPLOY_SSH_HOST` | VM 공인 IP 또는 FQDN |
| `DEPLOY_SSH_USER` | VM 로그인 사용자명 |

### 배포 흐름

```text
push / 수동 트리거
  → SSH 연결 확인
  → 현재 webapp2 백업 (타임스탬프)
  → rsync ./webapp/ → ~/webapp2/   ← git clone 중간 폴더 없음
  → pip install -r requirements.txt
  → systemctl restart webapp2
  → /health + /api/status 헬스체크 (최대 30회 재시도)
  → 실패 시 백업에서 자동 롤백
  → 항상 서비스 로그 80줄 출력
  → 7일 지난 백업 자동 삭제
```

### 수동 트리거 옵션

GitHub → Actions → `Deploy webapp2` → `Run workflow`

| 옵션 | 설명 |
| ---- | ---- |
| `dry_run=true` | rsync 변경 목록만 출력, 실제 배포 없음 |
| `rollback_on_failure=false` | 실패 시 롤백 건너뜀 |

---

## Azure NSG 포트 오픈 방법

| 항목 | 개발용 | webapp2 운영용 |
| ---- | ------ | -------------- |
| 대상 포트 범위 | **8000** | **8002** |
| 프로토콜 | TCP | TCP |
| 우선순위 | 310 | 320 |
| 이름 | Allow-8000 | Allow-8002 |

> 보안을 위해 운영 환경에서는 Nginx를 통해 포트 80만 오픈하고 8002는 닫는 것을 권장합니다.

---

## 주요 API 엔드포인트

| 메서드 | 경로 | 설명 |
| ------ | ---- | ---- |
| GET | `/health` | 서비스 헬스체크 (배포 자동화용) |
| GET | `/api/status` | 서버 상태 및 최신 리포트 날짜 |
| GET | `/api/reports/daily` | 일일 브리핑 목록 |
| GET | `/api/reports/daily/{date}` | 특정 날짜 브리핑 내용 |
| GET | `/api/reports/weekly` | 주간 리포트 목록 |
| GET | `/api/reports/weekly/{week}` | 특정 주차 리포트 내용 |
| POST | `/api/run-briefing` | 브리핑 스크립트 즉시 실행 |
| GET | `/api/portfolio` | 포트폴리오 현황 전체 조회 |
| POST | `/api/portfolio` | 포트폴리오 종목 추가 |
| PUT | `/api/portfolio/{ticker}` | 포트폴리오 종목 수정 |
| DELETE | `/api/portfolio/{ticker}` | 포트폴리오 종목 삭제 |
| GET | `/api/watchlist` | 관심종목 전체 조회 |
| POST | `/api/watchlist` | 관심종목 추가 |
| PUT | `/api/watchlist/{ticker}` | 관심종목 수정 |
| DELETE | `/api/watchlist/{ticker}` | 관심종목 삭제 |
| GET | `/api/enrich/{ticker}` | ticker 종목 정보 조회 (yfinance) |
| GET | `/api/enrich/watchlist/{query}` | ticker·종목명 → AI 관심종목 필드 생성 |

Swagger UI: `http://<VM_IP>:8002/docs`

### enrich API 상세

#### `GET /api/enrich/{ticker}` — 포트폴리오 자동채움

ticker 하나를 받아 yfinance에서 종목 정보를 조회한 뒤 반환합니다.

**KRX ticker 후보 전략** — 숫자 5~6자리는 `.KS`(KOSPI) → `.KQ`(KOSDAQ) 순으로 시도합니다. 5자리 ticker는 zero-padding(예: `5930` → `005930.KS`)을 우선 시도합니다.

| 상태 코드 | 원인 |
| --------- | ---- |
| 400 | 빈 ticker, 금지 문자, 20자 초과 |
| 502 | 모든 후보 ticker에서 yfinance 조회 실패 |

#### `GET /api/enrich/watchlist/{query}` — 관심종목 AI 자동채움

ticker 또는 종목명을 받아 yfinance 뉴스 + Azure OpenAI(gpt-4o)로 관심종목 전체 필드를 생성합니다.

```json
{
  "ticker": "MSFT",
  "company_name": "Microsoft Corporation",
  "market": "NASDAQ",
  "currency": "USD",
  "current_price": 415.3,
  "watch_reason": "Azure AI 성장 재가속 + Copilot 수익화 본격화",
  "ideal_entry": "370",
  "trigger_condition": "Azure 성장률 30%+ 복귀 + 분기 EPS 컨센서스 상회",
  "invalidation": "AI 투자 대비 수익화 지연 2분기 연속",
  "risk_notes": "밸류에이션 부담, 규제 리스크",
  "priority": "1"
}
```

| 상태 코드 | 원인 |
| --------- | ---- |
| 400 | 빈 입력값, 50자 초과 |
| 502 | yfinance 조회 실패 또는 Azure OpenAI 호출 실패 |

---

## 데이터 파일 경로

모든 경로는 `config.py`에서 관리됩니다.

| 상수 | 실제 경로 | 설명 |
| ---- | --------- | ---- |
| `DATA_DIR` | `~/investment-assistant/data/` | 데이터 파일 루트 |
| `PORTFOLIO_CSV` | `~/investment-assistant/data/portfolio.csv` | 포트폴리오 현황 |
| `WATCHLIST_CSV` | `~/investment-assistant/data/watchlist.csv` | 관심종목 |
| `DAILY_REPORTS_DIR` | `~/investment-assistant/reports/daily/` | 일일 브리핑 저장 위치 |
| `WEEKLY_REPORTS_DIR` | `~/investment-assistant/reports/weekly/` | 주간 리포트 저장 위치 |
| `BRIEFING_SCRIPT` | `~/investment-assistant/generate_briefing.py` | 브리핑 생성 스크립트 |

CSV 파일을 직접 편집해야 하는 경우 반드시 UTF-8 인코딩으로 저장하고, 첫 행의 컬럼 헤더를 변경하지 마세요.
