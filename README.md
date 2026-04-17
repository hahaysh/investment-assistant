# 🦞 OpenClaw 개인 투자 비서 세팅 가이드

Azure Linux VM에서 OpenClaw를 활용해 매일 자동으로 투자 브리핑을 생성하고 Telegram으로 받는 시스템입니다.

## 📋 완성된 기능

- 📊 **매일 09:00 KST** — 일일 투자 브리핑 자동 생성 + Telegram 전송
- 📋 **매주 월요일 09:10 KST** — 주간 포트폴리오 리포트 자동 생성
- 💹 **실시간 시장 데이터** — yfinance 기반 (KOSPI, S&P500, USDKRW, VIX 등)
- 📁 **마크다운 리포트** — 파일로 누적 저장
- 🤖 **AI 시나리오 분석** — OpenClaw agent가 Bullish/Base/Bear 자동 작성

## 🏗️ 레포 구조

```text
investment-assistant/
├── openclaw/                   # OpenClaw 설정 및 가이드
│   ├── docs/                   # 단계별 설치 가이드
│   ├── scripts/                # 설치 스크립트
│   ├── skills/                 # OpenClaw 스킬 정의
│   └── data-templates/         # 데이터 파일 템플릿
├── webapp/                     # 웹앱 소스코드
│   ├── src/
│   └── public/
└── README.md
```

### OpenClaw VM 구조 (Azure Linux VM 기준)

```text
~/investment-assistant/         # VM 상의 실제 운영 폴더
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

## ✅ 사전 요구사항

- Ubuntu 24.04 LTS (Azure VM 기준)
- OpenClaw 설치 및 실행 중 (`openclaw-gateway` 프로세스)
- Telegram 봇 연결 완료
- Python 3.x

## 🚀 설치 순서

| 단계 | 내용 |
| ---- | ---- |
| [Step 1](./docs/step1-project-setup.md) | 프로젝트 폴더 및 데이터 파일 생성 |
| [Step 2](./docs/step2-skills.md) | OpenClaw 스킬 등록 |
| [Step 3](./docs/step3-briefing-script.md) | 브리핑 생성 Python 스크립트 |
| [Step 4](./docs/step4-cron.md) | cron 자동 스케줄 등록 |
| [Step 5](./docs/step5-test.md) | 테스트 및 검증 |

## ⚠️ 알려진 문제 및 팁

[troubleshooting.md](./docs/troubleshooting.md) 참고

## 📱 수동 실행

```bash
# 일일 브리핑 즉시 실행
python3 ~/investment-assistant/generate_briefing.py

# 주간 리포트 즉시 실행
~/.npm-global/bin/openclaw agent \
  --to telegram:YOUR_CHAT_ID --deliver \
  --message "주간 포트폴리오 리포트 생성해줘. ~/investment-assistant/data 참조해서 weekly-portfolio-report 스킬 실행하고 ~/investment-assistant/reports/weekly/$(date +%Y-W%V).md 로 저장해줘."
```

## 📂 파일 업데이트

```bash
# 포트폴리오 수정 (매수/매도 후)
nano ~/investment-assistant/data/portfolio.csv

# 관심 종목 수정
nano ~/investment-assistant/data/watchlist.csv
```
