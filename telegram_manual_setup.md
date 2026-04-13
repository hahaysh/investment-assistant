# Telegram 수동 설정 가이드

비개발자 기준. 5분 내 완료 가능.

---

## 1단계 — Telegram Bot 생성

1. Telegram 앱에서 `@BotFather` 검색 → 대화 시작
2. `/newbot` 입력
3. 봇 이름 입력 (예: `세인투 투자비서`)
4. 봇 유저명 입력 (영문+숫자, `_bot`으로 끝나야 함, 예: `saintu_invest_bot`)
5. 발급된 **Token** 복사 → `config/secrets.env`의 `TELEGRAM_BOT_TOKEN`에 입력

---

## 2단계 — Chat ID 확인

**개인 채팅 방식:**

1. 방금 만든 봇과 대화 시작 (검색 후 `/start` 전송)
2. 브라우저에서 아래 URL 접속 (token 교체):
   ```
   https://api.telegram.org/bot[YOUR_BOT_TOKEN]/getUpdates
   ```
3. 응답 JSON에서 `"chat":{"id":` 뒤 숫자가 Chat ID
4. `config/secrets.env`의 `TELEGRAM_CHAT_ID`에 입력

**그룹 채팅 방식 (선택):**

1. Telegram 그룹 생성 → 봇을 그룹에 초대
2. 그룹에서 아무 메시지 전송
3. 위와 동일하게 getUpdates 확인 → 그룹 Chat ID는 음수(`-100...`)

---

## 3단계 — 테스트 메시지 전송

```bash
curl -X POST "https://api.telegram.org/bot[BOT_TOKEN]/sendMessage" \
  -d chat_id=[CHAT_ID] \
  -d text="✅ 투자 비서 연결 테스트 성공"
```

또는 Python:

```python
import os, requests
requests.post(
    f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/sendMessage",
    json={"chat_id": os.environ["TELEGRAM_CHAT_ID"], "text": "✅ 연결 성공"}
)
```

---

## 4단계 — secrets.env 최종 확인

```env
TELEGRAM_BOT_TOKEN=7123456789:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TELEGRAM_CHAT_ID=123456789
```

---

## 알림 받기 팁

- 봇 알림 끄지 않도록 주의 (Telegram → 봇 대화 → 알림 설정)
- 중요 알림만 받으려면 별도 그룹/채널 생성 권장
