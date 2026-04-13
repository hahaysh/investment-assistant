# Telegram 요약 규칙

## 전송 전제 조건
- Google Sheets 기록 **성공** 후에만 전송
- 실패 시: 로그에 기록하고 전송 중단 (재시도 1회)

---

## Daily 요약 형식 (5~8줄)

```
📊 [{TODAY}] 일일 브리핑

📈 시장: KOSPI {KOSPI_CHG}% | S&P {SPX_CHG}% | USDKRW {USDKRW}
⚡ 핵심: {TOP_DRIVER_1} / {TOP_DRIVER_2}
💼 포트폴리오: {PORTFOLIO_ACTION_SUMMARY}
🔴 리스크: {IMMEDIATE_RISK}
👀 오늘 볼 것: {WATCH_TODAY}
📁 상세: reports/daily/{TODAY}.md
```

**작성 원칙**
- 줄당 핵심 팩트 1개
- 수치는 소수점 1자리까지
- "오늘 볼 것" = 당일 가장 중요한 체크포인트 1~2개
- "즉시 확인 리스크" = thesis 훼손 or 급격한 환경 변화만
- 감상·전망 문장 금지

---

## Weekly 요약 형식 (6~10줄)

```
📋 [{WEEK_LABEL}] 주간 포트폴리오 리포트

📊 수익률: 포트 {PORT_WK}% | KOSPI {KOSPI_WK}% | S&P {SPX_WK}% | 초과 {ALPHA}%
🏆 기여: +{TOP_CONTRIB} | -{BOTTOM_CONTRIB}
🔄 Thesis: {THESIS_CHANGE_SUMMARY}
⚖️ 리밸런싱: {REBALANCE_CANDIDATES}
🎯 다음 주 촉매: {NEXT_WEEK_CATALYST}
📌 액션: {ACTION_PLAN_SUMMARY}
📁 상세: reports/weekly/{WEEK_LABEL}.md
```

**작성 원칙**
- 수익률은 반드시 벤치마크 대비 초과수익 명시
- Thesis 변화 있으면 종목명 포함
- 리밸런싱 후보는 ticker만 나열
- 다음 주 촉매는 날짜 + 이벤트명으로 짧게

---

## 전송 코드 스니펫

```python
import requests, os

def send_telegram(message: str):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    resp = requests.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"})
    resp.raise_for_status()
    return resp.json()
```
