# Weekly Portfolio Runbook

**실행 시각**: 매주 월요일 09:10 KST  
**출력 경로**: `reports/weekly/YYYY-Wxx.md`  
**참조 파일**: `data/investor_profile.md` · `data/portfolio.csv` · `data/watchlist.csv`

---

## Step 1 — 데이터 수집 (자동)

수집 항목:
- 지난 주 KOSPI / S&P500 / NASDAQ 주간 수익률
- 포트폴리오 각 종목 주간 수익률 (yfinance)
- 시장 주요 이벤트 요약 (뉴스 API or 수동 입력)

---

## Step 2 — Claude 프롬프트 실행

```
당신은 세인투의 개인 투자 비서입니다.

투자 스타일: value, quality, cash flow, shareholder return, margin of safety
섹터 그룹: [A]반도체 [B]한국금융 [C]자동차 [D]미국금융 [E]헬스케어 [F]에너지 [G]고품질플랫폼
포트폴리오 상세: data/portfolio.csv 참조
관찰 종목 상세: data/watchlist.csv 참조

분석 기간: {WEEK_START} ~ {WEEK_END} ({WEEK_LABEL})
벤치마크 수익률:
- KOSPI: {KOSPI_WK}%
- S&P500: {SPX_WK}%
종목별 주간 수익률: {RETURNS_JSON}

아래 구조로 주간 포트폴리오 리포트를 작성하세요. reports/weekly/{WEEK_LABEL}.md로 저장합니다.
```

---

## Step 3 — 보고서 구조 (출력 템플릿)

```markdown
# 주간 포트폴리오 리포트 — {WEEK_LABEL}
기간: {WEEK_START} ~ {WEEK_END}

## 1. 주간 수익률 요약
| 구분 | 수익률 |
|------|--------|
| 포트폴리오 | |
| KOSPI | |
| S&P500 | |
| 초과수익 | |

## 2. 수익/손실 기여 종목
- 최고 기여: 
- 최저 기여: 
- 기여 분석 (섹터별):

## 3. 비중 변화
> 이번 주 매매 내역 및 비중 변동 요약

## 4. Thesis 점검
| 종목 | Thesis 상태 | 변화 내용 |
|------|------------|----------|
| | 유지/변경/훼손 | |

## 5. 밸류에이션 변화
- PER/PBR 주요 변동 종목:
- 안전마진 축소/확대 종목:

## 6. 리스크 맵
- 상승 리스크:
- 하락 리스크:
- 환율 노출:

## 7. 리밸런싱 후보
- 비중 과다:
- 비중 부족:
- 매도 검토:

## 8. 다음 주 주요 촉매
- 경제지표:
- 기업 실적:
- 정책 이벤트:

## 9. Watchlist 승격 후보
> 트리거 조건 근접 종목 목록 + 이유

## 10. 다음 주 액션 플랜
- [ ] 우선순위 1:
- [ ] 우선순위 2:
- [ ] 모니터링:
```

---

## Step 4 — Google Sheets 기록

시트: `주간포트폴리오리포트` (schema → `docs/google_sheets_schema.md`)  
저장 항목: 주간시작일, 종료일, 수익률, 초과수익, 기여 종목, 리밸런싱 후보, 리포트 파일 경로  
**본문 저장 금지**

---

## Step 5 — Telegram 전송

Google Sheets 기록 성공 확인 후 전송  
형식: `prompts/telegram_summary_rules.md` → Weekly 요약 참조
