# Daily Briefing Runbook

**실행 시각**: 매일 09:00 KST  
**출력 경로**: `reports/daily/YYYY-MM-DD.md`  
**참조 파일**: `data/investor_profile.md` · `data/portfolio.csv` · `data/watchlist.csv`

---

## Step 1 — 데이터 수집 (자동)

수집 항목:
- KOSPI / KOSDAQ 전일 종가 및 등락률
- S&P500 / NASDAQ 전일 종가 및 등락률
- USDKRW 환율 / 미국 10년물 금리 / DXY / VIX / WTI / 금

도구: Yahoo Finance API or yfinance 라이브러리

---

## Step 2 — Claude 프롬프트 실행

```
당신은 세인투의 개인 투자 비서입니다.

투자 스타일: value, quality, cash flow, shareholder return, margin of safety
섹터 그룹: [A]반도체 [B]한국금융 [C]자동차 [D]미국금융 [E]헬스케어 [F]에너지 [G]고품질플랫폼
포트폴리오 상세: data/portfolio.csv 참조
관찰 종목 상세: data/watchlist.csv 참조

오늘 날짜: {TODAY}
시장 데이터:
- KOSPI: {KOSPI_CLOSE} ({KOSPI_CHG}%)
- KOSDAQ: {KOSDAQ_CLOSE} ({KOSDAQ_CHG}%)
- S&P500: {SPX_CLOSE} ({SPX_CHG}%)
- NASDAQ: {NDX_CLOSE} ({NDX_CHG}%)
- USDKRW: {USDKRW}
- 미국10년물: {US10Y}%
- DXY: {DXY}
- VIX: {VIX}
- WTI: ${WTI}
- 금: ${GOLD}

아래 구조로 일일 브리핑을 작성하세요. reports/daily/{TODAY}.md로 저장합니다.
```

---

## Step 3 — 보고서 구조 (출력 템플릿)

```markdown
# 일일 투자 브리핑 — {TODAY}

## 1. 시장 요약
- 한국/미국 전일 시황 1~2줄 요약
- 주요 원인: (뉴스·이벤트 기반)

## 2. 미국-한국 시장 연결 해석
- 미국 선물/야간 흐름 → 한국 개장 영향
- 환율·금리 채널 분석

## 3. 거시 지표 체크
| 지표 | 값 | 전일비 | 투자 함의 |
|------|-----|--------|----------|
| USDKRW | | | |
| 미국10년물 | | | |
| DXY | | | |
| VIX | | | |
| WTI | | | |
| 금 | | | |

## 4. 섹터 로테이션
- 강세 섹터: 
- 약세 섹터: 
- 로테이션 신호:

## 5. 보유 종목 영향 분석
> portfolio.csv 섹터 그룹별로 간략히 서술 (종목명 + 1줄)

## 6. Watchlist 영향
> watchlist.csv 트리거 조건 충족 여부 확인

## 7. 오늘 주요 일정
- 경제지표 발표:
- 기업 실적:
- 연준/한은 발언:

## 8. 시나리오
| 구분 | 조건 | 포트폴리오 영향 |
|------|------|----------------|
| Bullish | | |
| Base | | |
| Bear | | |

## 9. 액션 아이디어
- [ ] 즉시 검토:
- [ ] 모니터링 유지:
- [ ] 보류:

## 10. Thesis 변화 여부
- 변화 없음 / 훼손 종목: / 강화 종목:
```

---

## Step 4 — Google Sheets 기록

시트: `일일브리핑` (schema → `docs/google_sheets_schema.md`)  
저장 항목: 날짜, 실행시각, 시장국면, 주요 수치, 강세/약세 섹터, 핵심동인Top3, 리포트파일 경로  
**본문 저장 금지** — 긴 텍스트는 markdown 파일 경로로 대체

---

## Step 5 — Telegram 전송

Google Sheets 기록 성공 확인 후 전송  
형식: `prompts/telegram_summary_rules.md` → Daily 요약 참조
