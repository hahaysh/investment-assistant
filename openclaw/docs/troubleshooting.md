# 트러블슈팅 가이드

실제 세팅 과정에서 만났던 문제들과 해결 방법을 정리했습니다.

---

## ❌ 문제 1: `openclaw message "..."` 명령어 오류

**증상:**
```
error: too many arguments for 'message'. Expected 0 arguments but got 1.
```

**원인:** `openclaw message`는 서브커맨드가 필요합니다. 문자열을 직접 인자로 받지 않습니다.

**해결:**
```bash
# ❌ 잘못된 방법
openclaw message "안녕하세요"

# ✅ 올바른 방법 - agent로 메시지 전송
openclaw agent --to telegram:CHAT_ID --message "안녕하세요" --deliver

# ✅ 올바른 방법 - message send로 전송
openclaw message send --channel telegram --target CHAT_ID --message "안녕하세요"
```

---

## ❌ 문제 2: cron에서 openclaw를 찾지 못함

**증상:** cron은 실행되지만 브리핑이 생성되지 않고 로그에 `command not found` 에러

**원인:** cron의 PATH에는 npm global 경로가 포함되지 않습니다.

**해결:** crontab에 전체 경로(full path) 사용

```bash
# openclaw 실제 경로 확인
which openclaw
# 출력 예: /home/USERNAME/.npm-global/bin/openclaw

# ❌ 잘못된 cron 등록
0 0 * * * openclaw agent ...

# ✅ 올바른 cron 등록
0 0 * * * /home/USERNAME/.npm-global/bin/openclaw agent ...
```

---

## ❌ 문제 3: 웹 검색 실패 (403 오류)

**증상:**
```
외부 웹 검색에서 많은 페이지가 접근 제한(403 오류)으로 인해 정보를 가져올 수 없었습니다.
```

**원인:** Microsoft Foundry (gpt-4o, gpt-5-mini) 모델은 웹 검색 도구가 없습니다.
Claude API나 OpenAI API가 연결되어 있어야 웹 검색이 가능합니다.

**해결:** yfinance Python 스크립트로 직접 시장 데이터 수집
```bash
pip install yfinance --break-system-packages
python3 -c "import yfinance as yf; t=yf.Ticker('^GSPC'); print(t.fast_info.last_price)"
```

---

## ❌ 문제 4: openclaw agent가 파일을 저장하지 않음

**증상:** `openclaw agent`로 브리핑 요청 시 터미널에는 내용이 출력되지만 실제 파일이 생성되지 않음

**원인:** 에이전트가 파일 저장 명령을 이해하더라도 실제로 bash를 실행하지 않는 경우가 있습니다.

**해결 방법 1:** 명시적으로 bash 실행을 요청
```bash
openclaw agent --to telegram:CHAT_ID --message "bash 명령어로 echo 'test' > ~/test.md 실행해줘"
```

**해결 방법 2:** Python 스크립트가 직접 파일을 저장하도록 구성 (권장)
→ `generate_briefing.py`가 파일 저장을 직접 처리합니다.

---

## ❌ 문제 5: Telegram chat ID를 모를 때

**해결:**
```bash
# 방법 1: 세션 파일에서 확인
cat ~/.openclaw/agents/main/sessions/sessions.json | python3 -m json.tool | grep "telegram:direct"

# 방법 2: Telegram 전송 기록에서 확인
cat ~/.openclaw/agents/main/sessions/sessions.json.telegram-sent-messages.json
```

---

## ❌ 문제 6: 한국 종목 주가 조회 실패

**증상:** `005930` 같은 KRX 종목이 yfinance에서 조회되지 않음

**원인:** yfinance에서 한국 KRX 종목은 `.KS` 접미사가 필요합니다.

**해결:** `generate_briefing.py`의 `ticker_map`에 매핑 추가
```python
ticker_map = {
    "005930": "005930.KS",  # 삼성전자
    "000660": "000660.KS",  # SK하이닉스
    "BRK.B": "BRK-B",       # Berkshire (점 대신 하이픈)
}
```

---

## ❌ 문제 7: 시나리오/액션 섹션이 비어있음

**증상:** 브리핑 파일의 4번 시나리오와 5번 액션 아이디어가 빈칸

**원인:** `openclaw agent`로 파일 업데이트를 요청했지만 실제로 파일에 저장되지 않은 경우

**해결:** `generate_briefing.py`에 시나리오 채우기 로직을 통합
→ 스크립트 하단의 `# ── 6. 시나리오/액션 자동 채우기` 섹션 참고

---

## 💡 일반 팁

### Telegram에서 직접 브리핑 요청
OpenClaw가 연결된 Telegram 채팅에서 직접 메시지로도 실행 가능합니다:
```
오늘 투자 브리핑 생성해줘
주간 포트폴리오 리포트 만들어줘
```

### VM 재시작 후 확인
```bash
# openclaw-gateway 서비스가 자동 시작되는지 확인
systemctl status openclaw-gateway 2>/dev/null || ps aux | grep openclaw-gateway
```

### yfinance 장 마감 시간 주의
- **한국 KRX**: 장 마감 16:00 KST 이후 종가 데이터 수집 가능
- **미국 NYSE/NASDAQ**: 장 마감 04:00 KST (다음날) 이후 종가 데이터 수집 가능
- 브리핑이 09:00 KST에 실행되므로 **전일 종가 기준** 데이터가 수집됩니다.

### OpenClaw 업데이트
```bash
openclaw update
# 또는
npm update -g openclaw
```
