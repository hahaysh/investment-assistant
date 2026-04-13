# 개인 투자 비서 — Claude Code 프로젝트

## 프로젝트 목적
세인투의 개인 투자 포트폴리오를 위한 자동화 브리핑 시스템.

## 핵심 원칙
- 브리핑 프롬프트는 **투자 스타일 + 섹터 그룹 + data 파일 참조** 중심으로 짧게 유지
- 종목별 수량/평단/비중을 프롬프트에 반복 삽입 금지 → data/portfolio.csv 직접 참조
- Google Sheets에는 숫자와 짧은 메모만 저장 (본문 금지)
- Telegram은 Google Sheets 기록 성공 후에만 전송

## 데이터 파일
| 파일 | 용도 |
|------|------|
| `data/investor_profile.md` | 투자 철학, 스타일, 섹터 선호 |
| `data/portfolio.csv` | 보유 종목 전체 (수량·평단·thesis·risk) |
| `data/watchlist.csv` | 관찰 종목 (진입조건·무효화) |

## 실행 방법

### 일일 브리핑 (수동)
```bash
claude --runbook prompts/daily_briefing_runbook.md
```

### 주간 리포트 (수동)
```bash
claude --runbook prompts/weekly_portfolio_runbook.md
```

### 환경 변수 설정
```bash
cp config/secrets.env.example config/secrets.env
# secrets.env 편집 후:
source config/secrets.env
```

## 스케줄 (cron)
```
00 00 * * *   cd /path/to/investment-assistant && claude --runbook prompts/daily_briefing_runbook.md
10 00 * * 1   cd /path/to/investment-assistant && claude --runbook prompts/weekly_portfolio_runbook.md
```
> KST 09:00 = UTC 00:00 / KST 09:10 = UTC 00:10

## 출력 경로
- 일일 상세 보고서: `reports/daily/YYYY-MM-DD.md`
- 주간 상세 보고서: `reports/weekly/YYYY-Wxx.md`
- Google Sheets: 구조화 수치만 (schema → `docs/google_sheets_schema.md`)
- Telegram: 요약 메시지

## 의존성
```
pip install anthropic google-auth google-auth-oauthlib google-api-python-client python-telegram-bot python-dotenv
```
