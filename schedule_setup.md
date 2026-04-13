# 스케줄 작업 설정

## cron 등록 명령어

```bash
crontab -e
```

아래 내용 추가:

```cron
# 투자 비서 — 일일 브리핑 (매일 09:00 KST = UTC 00:00)
0 0 * * * cd /path/to/investment-assistant && source config/secrets.env && claude --runbook prompts/daily_briefing_runbook.md >> logs/daily_$(date +\%Y-\%m-\%d).log 2>&1

# 투자 비서 — 주간 리포트 (매주 월요일 09:10 KST = UTC 00:10)
10 0 * * 1 cd /path/to/investment-assistant && source config/secrets.env && claude --runbook prompts/weekly_portfolio_runbook.md >> logs/weekly_$(date +\%Y-\%m-\%d).log 2>&1
```

> `/path/to/investment-assistant`를 실제 절대 경로로 교체

## 서버 타임존 확인

```bash
timedatectl status | grep "Time zone"
# Asia/Seoul이어야 함. 아니라면:
sudo timedatectl set-timezone Asia/Seoul
```

## cron 설치 여부 확인 (Ubuntu/Debian)

```bash
which cron || sudo apt-get install cron -y
sudo systemctl enable cron && sudo systemctl start cron
```

## 대체 방법 (Claude Code 스케줄러 미지원 환경)

Claude Code는 현재 내장 스케줄러를 제공하지 않습니다.  
아래 대체 방법 중 선택:

| 방법 | 환경 | 비용 |
|------|------|------|
| **cron** (위 방법) | Linux/Mac 서버 | 무료 |
| **GitHub Actions** | GitHub 저장소 필요 | 무료 (월 2000분) |
| **Render / Railway** | 클라우드 배포 | 소액 |
| **macOS launchd** | Mac 로컬 | 무료 |

### GitHub Actions 대안 (.github/workflows/daily.yml)

```yaml
name: Daily Briefing
on:
  schedule:
    - cron: '0 0 * * *'   # UTC 00:00 = KST 09:00
jobs:
  briefing:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run daily briefing
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
          GOOGLE_SHEETS_SPREADSHEET_ID: ${{ secrets.GOOGLE_SHEETS_SPREADSHEET_ID }}
        run: claude --runbook prompts/daily_briefing_runbook.md
```
