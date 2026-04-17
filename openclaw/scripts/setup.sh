#!/bin/bash
# =============================================================
# OpenClaw 투자 비서 자동 설치 스크립트
# 사용법: bash setup.sh YOUR_TELEGRAM_CHAT_ID
# 예시: bash setup.sh 7733177955
# =============================================================

set -e

CHAT_ID=${1:-"YOUR_TELEGRAM_CHAT_ID"}
HOME_DIR=$HOME
INSTALL_DIR="$HOME_DIR/investment-assistant"
OPENCLAW_BIN=$(which openclaw 2>/dev/null || echo "$HOME_DIR/.npm-global/bin/openclaw")

echo "🦞 OpenClaw 투자 비서 설치 시작"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📁 설치 경로: $INSTALL_DIR"
echo "📱 Telegram Chat ID: $CHAT_ID"
echo "🔧 OpenClaw 경로: $OPENCLAW_BIN"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── Step 1. 폴더 생성 ──
echo ""
echo "▶ Step 1. 폴더 구조 생성..."
mkdir -p "$INSTALL_DIR"/{data,reports/{daily,weekly},logs}
echo "✅ 폴더 생성 완료"

# ── Step 2. 데이터 파일 생성 ──
echo ""
echo "▶ Step 2. 데이터 파일 생성..."

cat > "$INSTALL_DIR/data/investor_profile.md" << 'EOF'
# 투자자 프로필

## Basic Info
- 이름: 투자자
- 투자 경력: -
- 자산 통화: KRW + USD
- 위험 성향: 공격적 중립

## Investment Philosophy & Style
- Value, Quality, Cash Flow 중심
- Shareholder Return, Margin of Safety 중시
- 단기 모멘텀보다 thesis 기반 중장기 보유

## Preferred Sectors / Themes
- 한국: 반도체, 금융, 자동차
- 미국: 금융, 헬스케어, 에너지, 고품질 플랫폼

## Daily Reference Metrics
- KOSPI, KOSDAQ 등락률
- S&P500, 나스닥 등락률
- USDKRW, 미국10년물금리, DXY, WTI, 금, VIX

## Risk Management Rules
- 단일 종목 최대 비중 20%
- 섹터 집중도 40% 초과 금지
- thesis 훼손 시 3거래일 내 재검토
EOF

cat > "$INSTALL_DIR/data/portfolio.csv" << 'EOF'
ticker,company_name,market,holding_status,quantity,avg_cost,currency,target_weight,thesis,risk_notes,priority
005930,삼성전자,KRX,active,100,70000,KRW,0.15,HBM/파운드리 회복+고배당,실적 가이던스 하향 리스크,1
JPM,JPMorgan Chase,NYSE,active,10,190.0,USD,0.10,글로벌 금융 프랜차이즈+자본배분,경기침체시 대손 증가,1
CASH_KRW,현금(원화),KRX,cash,0,1,KRW,0.10,유동성 확보,,5
CASH_USD,현금(달러),NYSE,cash,0,1,USD,0.10,환헤지+기회비용,,5
EOF

cat > "$INSTALL_DIR/data/watchlist.csv" << 'EOF'
ticker,company_name,market,watch_reason,ideal_entry,trigger_condition,invalidation,risk_notes,priority
MSFT,Microsoft,NASDAQ,Azure 성장 재가속,380,Azure 성장률 30%+ 복귀,AI 수익화 지연,밸류에이션 부담,1
GOOGL,Alphabet,NASDAQ,광고+클라우드 이중 성장,155,GCP 점유율 상승 확인,AI 검색 점유율 잠식,반독점 규제,1
EOF

echo "✅ 데이터 파일 생성 완료"
echo "   ⚠️  portfolio.csv와 watchlist.csv를 실제 보유 종목으로 수정하세요:"
echo "   nano $INSTALL_DIR/data/portfolio.csv"

# ── Step 3. yfinance 설치 ──
echo ""
echo "▶ Step 3. yfinance 설치..."
pip install yfinance -q --break-system-packages 2>/dev/null || pip3 install yfinance -q --break-system-packages
python3 -c "import yfinance; print('✅ yfinance 설치 완료')"

# ── Step 4. 브리핑 스크립트 생성 ──
echo ""
echo "▶ Step 4. 브리핑 스크립트 생성..."

cat > "$INSTALL_DIR/generate_briefing.py" << PYEOF
#!/usr/bin/env python3
import yfinance as yf
import csv
from datetime import datetime
import subprocess
import os

today = datetime.now().strftime("%Y-%m-%d")
output_path = os.path.expanduser(f"~/investment-assistant/reports/daily/{today}.md")
OPENCLAW_BIN = "$OPENCLAW_BIN"
TELEGRAM_CHAT_ID = "$CHAT_ID"

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

with open(output_path, "w") as f:
    f.write("\n".join(lines))
print(f"✅ 브리핑 저장 완료: {output_path}")

# ── 4. Telegram 요약 전송 ──
if portfolio:
    best = max(portfolio, key=lambda x: x["chg"])
    worst = min(portfolio, key=lambda x: x["chg"])
    portfolio_summary = f"{best['company_name']} 최고 ({best['chg']:+.2f}%) / {worst['company_name']} 최저 ({worst['chg']:+.2f}%)"
else:
    portfolio_summary = "데이터 없음"

summary = f"""📊 {today} 일일 투자 브리핑
• 시장: KOSPI {macro['KOSPI']['price']:,.0f} ({macro['KOSPI']['chg']:+.2f}%) / S&P500 {macro['S&P500']['price']:,.0f} ({macro['S&P500']['chg']:+.2f}%)
• 매크로: USDKRW {macro['USDKRW']['price']:,.0f} / 미국10년물 {macro['미국10년물']['price']:.2f}% / VIX {macro['VIX']['price']:.1f}
• WTI: {macro['WTI']['price']:.2f} ({macro['WTI']['chg']:+.2f}%) / 금: {macro['금']['price']:,.0f}
• 포트폴리오: {portfolio_summary}
• 리포트: {output_path}"""

print("\n" + summary)

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

# ── 5. 시나리오/액션 자동 채우기 ──
import time
time.sleep(3)

if portfolio:
    scenario_prompt = f"""아래 브리핑 파일의 4번 시나리오와 5번 액션 아이디어를 실제 시장 데이터 기반으로 구체적으로 채워서 {output_path} 파일을 업데이트해줘.
현재 데이터:
- KOSPI: {macro['KOSPI']['price']:,.0f} ({macro['KOSPI']['chg']:+.2f}%)
- S&P500: {macro['S&P500']['price']:,.0f} ({macro['S&P500']['chg']:+.2f}%)
- VIX: {macro['VIX']['price']:.1f} / WTI: {macro['WTI']['price']:.2f} ({macro['WTI']['chg']:+.2f}%)
- USDKRW: {macro['USDKRW']['price']:,.0f}
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

chmod +x "$INSTALL_DIR/generate_briefing.py"
echo "✅ 브리핑 스크립트 생성 완료"

# ── Step 5. OpenClaw 스킬 등록 ──
echo ""
echo "▶ Step 5. OpenClaw 스킬 등록..."

mkdir -p "$HOME_DIR/.openclaw/skills/daily-investment-briefing"
cat > "$HOME_DIR/.openclaw/skills/daily-investment-briefing/SKILL.md" << 'EOF'
---
name: daily-investment-briefing
description: 매일 09:00 KST 투자 일일 브리핑 생성. 시장 요약, 보유 종목 영향, watchlist 점검, 액션 아이디어를 ~/investment-assistant/reports/daily/YYYY-MM-DD.md 로 저장 후 Telegram 5~8줄 요약 전송.
metadata: {"openclaw":{"emoji":"📈","os":["linux","darwin"]}}
---
## 트리거
"오늘 투자 브리핑", "일일 브리핑 실행"
## 참조 파일
- ~/investment-assistant/data/investor_profile.md
- ~/investment-assistant/data/portfolio.csv
- ~/investment-assistant/data/watchlist.csv
EOF

mkdir -p "$HOME_DIR/.openclaw/skills/weekly-portfolio-report"
cat > "$HOME_DIR/.openclaw/skills/weekly-portfolio-report/SKILL.md" << 'EOF'
---
name: weekly-portfolio-report
description: 매주 월요일 09:10 KST 주간 포트폴리오 리포트 생성. 수익률 vs 벤치마크, thesis 점검, 리밸런싱 후보를 ~/investment-assistant/reports/weekly/YYYY-Wxx.md 로 저장 후 Telegram 6~10줄 요약 전송.
metadata: {"openclaw":{"emoji":"📋","os":["linux","darwin"]}}
---
## 트리거
"주간 리포트", "이번 주 포트폴리오 점검"
## 참조 파일
- ~/investment-assistant/data/investor_profile.md
- ~/investment-assistant/data/portfolio.csv
- ~/investment-assistant/data/watchlist.csv
EOF

echo "✅ 스킬 등록 완료"

# ── Step 6. cron 등록 ──
echo ""
echo "▶ Step 6. cron 등록..."

(crontab -l 2>/dev/null; cat << CRON
# 투자 일일 브리핑 - 매일 09:00 KST (UTC 00:00)
0 0 * * * python3 $INSTALL_DIR/generate_briefing.py >> $INSTALL_DIR/logs/daily.log 2>&1
# 주간 포트폴리오 리포트 - 매주 월요일 09:10 KST (UTC 00:10)
10 0 * * 1 $OPENCLAW_BIN agent --to telegram:$CHAT_ID --deliver --message "주간 포트폴리오 리포트 생성해줘. ~/investment-assistant/data 참조해서 weekly-portfolio-report 스킬 실행하고 ~/investment-assistant/reports/weekly/\$(date +%Y-W%V).md 로 저장해줘." >> $INSTALL_DIR/logs/weekly.log 2>&1
CRON
) | crontab -

echo "✅ cron 등록 완료"

# ── 완료 ──
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 설치 완료!"
echo ""
echo "📋 다음 단계:"
echo "  1. 포트폴리오 수정: nano $INSTALL_DIR/data/portfolio.csv"
echo "  2. 수동 테스트:     python3 $INSTALL_DIR/generate_briefing.py"
echo "  3. cron 확인:       crontab -l"
echo ""
echo "📱 Telegram Chat ID: $CHAT_ID"
echo "⏰ 자동 실행: 매일 09:00 KST / 매주 월 09:10 KST"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
