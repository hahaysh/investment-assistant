# Step 3. 브리핑 생성 Python 스크립트

## 개요
yfinance로 실시간 시장 데이터를 수집하고, 마크다운 브리핑 파일 저장 후 Telegram으로 요약을 전송하는 스크립트입니다.

> ⚠️ **중요**: OpenClaw의 기본 모델(Microsoft Foundry gpt-4o/gpt-5-mini)은 웹 검색 기능이 없습니다.
> 때문에 `openclaw agent`로 "웹 검색해서 시장 데이터 가져와줘" 방식은 403 오류가 발생합니다.
> **yfinance Python 스크립트**로 직접 데이터를 수집하는 방식을 사용합니다.

---

## 3-1. yfinance 설치

```bash
pip install yfinance -q --break-system-packages
python3 -c "import yfinance as yf; print('yfinance OK')"
```

---

## 3-2. 브리핑 스크립트 생성

```bash
cat > ~/investment-assistant/generate_briefing.py << 'PYEOF'
#!/usr/bin/env python3
import yfinance as yf
import csv
from datetime import datetime
import subprocess
import os

today = datetime.now().strftime("%Y-%m-%d")
output_path = os.path.expanduser(f"~/investment-assistant/reports/daily/{today}.md")

# ── 1. 매크로 데이터 수집 ──
macro_tickers = {
    "KOSPI": "^KS11", "KOSDAQ": "^KQ11",
    "S&P500": "^GSPC", "NASDAQ": "^IXIC",
    "USDKRW": "USDKRW=X", "미국10년물": "^TNX",
    "DXY": "DX-Y.NYB", "WTI": "CL=F",
    "금": "GC=F", "VIX": "^VIX"
}

macro = {}
for name, ticker in macro_tickers.items():
    try:
        t = yf.Ticker(ticker)
        i = t.fast_info
        prev = i.previous_close
        last = i.last_price
        chg = ((last - prev) / prev * 100) if prev else 0
        macro[name] = {"price": last, "chg": chg}
    except:
        macro[name] = {"price": 0, "chg": 0}

# ── 2. 포트폴리오 데이터 수집 ──
portfolio = []
csv_path = os.path.expanduser("~/investment-assistant/data/portfolio.csv")
with open(csv_path) as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row["holding_status"] == "cash":
            continue
        # 한국 종목 ticker 변환 (yfinance는 .KS 접미사 필요)
        ticker_map = {
            "005930": "005930.KS", "000660": "000660.KS",
            "005380": "005380.KS", "105560": "105560.KS",
            "000270": "000270.KS", "035420": "035420.KS",
            "035720": "035720.KS", "BRK.B": "BRK-B"
        }
        yf_ticker = ticker_map.get(row["ticker"], row["ticker"])
        try:
            t = yf.Ticker(yf_ticker)
            i = t.fast_info
            prev = i.previous_close
            last = i.last_price
            chg = ((last - prev) / prev * 100) if prev else 0
            row["current_price"] = last
            row["chg"] = chg
        except:
            row["current_price"] = 0
            row["chg"] = 0
        portfolio.append(row)

# ── 3. 마크다운 브리핑 생성 ──
def fmt(name):
    m = macro[name]
    arrow = "▲" if m["chg"] >= 0 else "▼"
    return f"{m['price']:,.2f} ({arrow}{abs(m['chg']):.2f}%)"

lines = []
lines.append(f"# 📊 일일 투자 브리핑 — {today}\n")

lines.append("## 1. 시장 요약\n")
lines.append("| 지표 | 수치 |")
lines.append("|------|------|")
for name in macro_tickers:
    lines.append(f"| {name} | {fmt(name)} |")
lines.append("")

lines.append("## 2. 보유 종목 현황\n")
lines.append("| 종목 | 현재가 | 등락 | Thesis | 리스크 |")
lines.append("|------|--------|------|--------|--------|")
for p in portfolio:
    arrow = "▲" if p["chg"] >= 0 else "▼"
    lines.append(f"| {p['company_name']}({p['ticker']}) | {p['current_price']:,.0f} | {arrow}{abs(p['chg']):.2f}% | {p['thesis']} | {p['risk_notes']} |")
lines.append("")

lines.append("## 3. Watchlist 점검\n")
watch_path = os.path.expanduser("~/investment-assistant/data/watchlist.csv")
with open(watch_path) as f:
    reader = csv.DictReader(f)
    lines.append("| 종목 | 감시 이유 | 진입 조건 | 무효화 |")
    lines.append("|------|-----------|-----------|--------|")
    for row in reader:
        lines.append(f"| {row['company_name']}({row['ticker']}) | {row['watch_reason']} | {row['trigger_condition']} | {row['invalidation']} |")
lines.append("")

lines.append("## 4. 시나리오\n")
lines.append("- **Bullish**: \n- **Base**: \n- **Bear**: \n")

lines.append("## 5. 액션 아이디어\n")
lines.append("- [ ] \n")

lines.append("## 6. Thesis 변화\n")
lines.append("- 없음\n")

lines.append(f"\n---\n*생성: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} KST*")

# ── 4. 파일 저장 ──
with open(output_path, "w") as f:
    f.write("\n".join(lines))

print(f"✅ 브리핑 저장 완료: {output_path}")

# ── 5. Telegram 요약 전송 ──
kospi = macro["KOSPI"]
sp500 = macro["S&P500"]
usdkrw = macro["USDKRW"]
vix = macro["VIX"]
wti = macro["WTI"]

best = max(portfolio, key=lambda x: x["chg"])
worst = min(portfolio, key=lambda x: x["chg"])

summary = f"""📊 {today} 일일 투자 브리핑
• 시장: KOSPI {kospi['price']:,.0f} ({kospi['chg']:+.2f}%) / S&P500 {sp500['price']:,.0f} ({sp500['chg']:+.2f}%)
• 매크로: USDKRW {usdkrw['price']:,.0f} / 미국10년물 {macro['미국10년물']['price']:.2f}% / VIX {vix['price']:.1f}
• WTI: {wti['price']:.2f} ({wti['chg']:+.2f}%) / 금: {macro['금']['price']:,.0f}
• 포트폴리오: {best['company_name']} 최고 ({best['chg']:+.2f}%) / {worst['company_name']} 최저 ({worst['chg']:+.2f}%)
• 리포트: {output_path}"""

print("\n" + summary)

# Telegram 전송
OPENCLAW_BIN = os.path.expanduser("~/.npm-global/bin/openclaw")
TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"  # ← 본인 chat ID로 변경

result = subprocess.run([
    OPENCLAW_BIN, "message", "send",
    "--channel", "telegram",
    "--target", TELEGRAM_CHAT_ID,
    "--message", summary
], capture_output=True, text=True)

if result.returncode == 0:
    print("✅ Telegram 전송 완료")
else:
    print(f"⚠️ Telegram 전송 실패: {result.stderr}")

# ── 6. 시나리오/액션 자동 채우기 (OpenClaw agent) ──
import time
time.sleep(3)

scenario_prompt = f"""아래 브리핑 파일의 4번 시나리오와 5번 액션 아이디어를 실제 시장 데이터 기반으로 구체적으로 채워서 {output_path} 파일을 업데이트해줘.
현재 데이터:
- KOSPI: {macro['KOSPI']['price']:,.0f} ({macro['KOSPI']['chg']:+.2f}%)
- S&P500: {macro['S&P500']['price']:,.0f} ({macro['S&P500']['chg']:+.2f}%)
- VIX: {macro['VIX']['price']:.1f}
- WTI: {macro['WTI']['price']:.2f} ({macro['WTI']['chg']:+.2f}%)
- USDKRW: {macro['USDKRW']['price']:,.0f}
- 최고 종목: {best['company_name']} ({best['chg']:+.2f}%)
- 최저 종목: {worst['company_name']} ({worst['chg']:+.2f}%)
Bullish/Base/Bear 각 1~2줄, 액션 아이디어 3개 이상 작성해줘."""

result2 = subprocess.run([
    OPENCLAW_BIN, "agent",
    "--to", f"telegram:{TELEGRAM_CHAT_ID}",
    "--message", scenario_prompt
], capture_output=True, text=True)

if result2.returncode == 0:
    print("✅ 시나리오/액션 채우기 완료")
else:
    print(f"⚠️ 시나리오 채우기 실패: {result2.stderr}")
PYEOF

chmod +x ~/investment-assistant/generate_briefing.py
echo "✅ 스크립트 생성 완료"
```

---

## 3-3. Chat ID 설정

스크립트 내 `YOUR_TELEGRAM_CHAT_ID`를 본인 Telegram chat ID로 변경합니다.

```bash
# Telegram chat ID 확인
cat ~/.openclaw/agents/main/sessions/sessions.json | python3 -m json.tool | grep -i "telegram:direct"
```

출력 예시: `"agent:main:telegram:direct:7733177955"` → chat ID는 `7733177955`

```bash
# 스크립트에서 chat ID 교체
sed -i 's/YOUR_TELEGRAM_CHAT_ID/7733177955/' ~/investment-assistant/generate_briefing.py
```

---

## 3-4. 테스트 실행

```bash
python3 ~/investment-assistant/generate_briefing.py
```

**정상 출력 예시:**
```
✅ 브리핑 저장 완료: /home/USERNAME/investment-assistant/reports/daily/2026-04-17.md
📊 2026-04-17 일일 투자 브리핑
• 시장: KOSPI 6,192 (-0.55%) / S&P500 7,041 (+0.26%)
...
✅ Telegram 전송 완료
✅ 시나리오/액션 채우기 완료
```

```bash
# 파일 생성 확인
ls ~/investment-assistant/reports/daily/
cat ~/investment-assistant/reports/daily/$(date +%Y-%m-%d).md
```

> 💡 **팁**: 한국 장 마감 후(16:00 KST 이후) 실행해야 당일 종가 데이터가 수집됩니다.
> 
> 💡 **팁**: `BRK.B`는 yfinance에서 `BRK-B`로 조회해야 합니다. ticker_map에 이미 반영되어 있습니다.

✅ Step 3 완료 → [Step 4로 이동](./step4-cron.md)
