# Step 4. cron 자동 스케줄 등록

## 개요
매일 09:00 KST와 매주 월요일 09:10 KST에 자동으로 브리핑이 실행되도록 cron을 등록합니다.

> ⚠️ **중요**: Azure VM의 기본 Timezone은 **UTC**입니다.
> KST(UTC+9) 기준으로 변환해야 합니다.
> - KST 09:00 → **UTC 00:00**
> - KST 09:10 → **UTC 00:10**

---

## 4-1. Timezone 확인

```bash
timedatectl | grep "Time zone"
```

UTC가 아닌 경우:
```bash
# UTC로 변경
sudo timedatectl set-timezone UTC
```

---

## 4-2. openclaw 실행 경로 확인

```bash
which openclaw
```

> ⚠️ **중요**: cron은 PATH 환경변수가 일반 셸과 다릅니다.
> 반드시 **전체 경로(full path)** 를 사용해야 합니다.
> 
> 일반적으로 npm global 설치 시: `/home/USERNAME/.npm-global/bin/openclaw`
> `/usr/bin/openclaw`가 아닐 수 있으니 반드시 `which openclaw`로 확인하세요.

---

## 4-3. cron 등록

```bash
# USERNAME과 CHAT_ID를 본인 값으로 변경 후 실행
(crontab -l 2>/dev/null; cat << 'CRON'
# 투자 일일 브리핑 - 매일 09:00 KST (UTC 00:00)
0 0 * * * python3 /home/hahaysh/investment-assistant/generate_briefing.py >> /home/hahaysh/investment-assistant/logs/daily.log 2>&1

# 주간 포트폴리오 리포트 - 매주 월요일 09:10 KST (UTC 00:10)
10 0 * * 1 /home/hahaysh/.npm-global/bin/openclaw agent --to telegram:7733177955 --deliver --message "주간 포트폴리오 리포트 생성해줘. ~/investment-assistant/data 참조해서 weekly-portfolio-report 스킬 실행하고 ~/investment-assistant/reports/weekly/$(date +%Y-W%V).md 로 저장해줘." >> /home/hahaysh/investment-assistant/logs/weekly.log 2>&1
CRON
) | crontab -
```

> 💡 **팁**: `/home/hahaysh/` 부분을 본인 홈 디렉토리로 변경하세요.
> `echo $HOME` 명령으로 확인 가능합니다.

---

## 4-4. cron 등록 확인

```bash
crontab -l
```

**정상 출력 예시:**
```
# 투자 일일 브리핑 - 매일 09:00 KST (UTC 00:00)
0 0 * * * python3 /home/hahaysh/investment-assistant/generate_briefing.py >> ...

# 주간 포트폴리오 리포트 - 매주 월요일 09:10 KST (UTC 00:10)
10 0 * * 1 /home/hahaysh/.npm-global/bin/openclaw agent ...
```

---

## 4-5. cron 로그 확인

```bash
# 실행 후 로그 확인
tail -f ~/investment-assistant/logs/daily.log
tail -f ~/investment-assistant/logs/weekly.log
```

---

## 4-6. cron 수정/삭제

```bash
# cron 편집
crontab -e

# cron 전체 삭제
crontab -r
```

✅ Step 4 완료 → [Step 5로 이동](./step5-test.md)
