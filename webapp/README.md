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

### 운영 환경 (systemd 서비스)

```bash
# 서비스 파일 배포
sudo cp ~/investment-assistant/webapp/investment-webapp.service /etc/systemd/system/

# 서비스 등록 및 시작
sudo systemctl daemon-reload
sudo systemctl enable investment-webapp
sudo systemctl start investment-webapp

# 상태 확인
sudo systemctl status investment-webapp

# 로그 실시간 확인
journalctl -u investment-webapp -f
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

## Azure NSG 포트 오픈 방법

포트 8000(개발) 또는 80(운영)을 외부에서 접근하려면 Azure NSG 인바운드 규칙을 추가해야 합니다.

1. Azure 포털 → 해당 VM → **네트워킹** 탭 클릭
2. **인바운드 포트 규칙 추가** 클릭
3. 아래 값으로 규칙 설정:

| 항목 | 개발용 | 운영용 |
| ---- | ------ | ------ |
| 원본 | Any | Any |
| 원본 포트 범위 | * | * |
| 대상 | Any | Any |
| 대상 포트 범위 | **8000** | **80** |
| 프로토콜 | TCP | TCP |
| 작업 | 허용 | 허용 |
| 우선순위 | 310 | 300 |
| 이름 | Allow-8000 | Allow-HTTP |

4. **추가** 클릭 후 적용까지 1~2분 대기

> 보안을 위해 운영 환경에서는 포트 8000을 닫고 Nginx를 통해 포트 80만 오픈하는 것을 권장합니다.

---

## 주요 API 엔드포인트

| 메서드 | 경로 | 설명 |
| ------ | ---- | ---- |
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

Swagger UI: `http://<VM_IP>:8000/docs`

### enrich API 상세

ticker 하나를 받아 외부 시세 데이터(yfinance)에서 종목 정보를 조회한 뒤 정제해서 반환합니다. 포트폴리오 추가 화면의 자동채움이 이 API를 사용합니다.

**KRX ticker 후보 전략** — 숫자 5~6자리는 `.KS`(KOSPI) → `.KQ`(KOSDAQ) 순으로 시도합니다. 5자리 ticker는 zero-padding(예: `5930` → `005930.KS`)을 우선 시도합니다.

#### 오류 구분

| 상태 코드 | 원인 | detail 예시 |
| --------- | ---- | ----------- |
| 400 | 빈 ticker, 금지 문자, 20자 초과 | `"ticker에 허용되지 않는 문자가 포함되어 있습니다: '삼성전자'"` |
| 502 | 모든 후보 ticker에서 yfinance 조회 실패 | `"'ZZZZZ' 종목 정보를 외부 API에서 가져오지 못했습니다. 시도한 ticker: [...]"` |

#### 응답 예시

```json
{
  "ticker": "005930",
  "resolved_ticker": "005930.KS",
  "company_name": "Samsung Electronics Co., Ltd.",
  "market": "KRX",
  "currency": "KRW",
  "current_price": 68000,
  "exchange": "KSC",
  "price_source": "fast_info"
}
```

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
