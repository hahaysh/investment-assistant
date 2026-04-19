"""
GET /api/enrich/{ticker}
GET /api/enrich/watchlist/{query}

ticker 또는 종목명을 받아 yfinance + Claude AI로 종목 정보를 조회하고
프론트엔드 자동채움에 필요한 필드를 반환한다.

오류 구분
  400  입력값이 잘못됨 (빈 값, 너무 긴 문자열 등)
  502  외부 API(yfinance / Claude) 조회 실패
"""

import json
import os
import re
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter()

# ──────────────────────────────────────────────────────────
# Ticker 후보 전략
# ──────────────────────────────────────────────────────────

def _is_krx(ticker: str) -> bool:
    """숫자 5~6자리 → KRX 종목으로 판단"""
    return bool(re.match(r"^\d{5,6}$", ticker))


def _krx_candidates(ticker: str) -> list[str]:
    """
    KRX ticker 후보 목록 (우선순위순)
    ① 6자리 zero-padding + .KS  (KOSPI 대부분)
    ② 원본 그대로 + .KS
    ③ 6자리 zero-padding + .KQ  (KOSDAQ)
    ④ 원본 그대로 + .KQ
    """
    padded = ticker.zfill(6)
    return [
        f"{padded}.KS",
        f"{ticker}.KS",
        f"{padded}.KQ",
        f"{ticker}.KQ",
    ]


def _us_candidates(ticker: str) -> list[str]:
    """
    미국 ticker 후보 목록 (우선순위순)
    ① 대문자 그대로         (NASDAQ / NYSE 대부분)
    ② 대문자 + -USD        (암호화폐 혼입 방지용 ETF류)
    """
    upper = ticker.upper()
    return [upper, f"{upper}-USD"]


# ──────────────────────────────────────────────────────────
# yfinance 래퍼 (import 지연 → 서버 기동 속도 유지)
# ──────────────────────────────────────────────────────────

def _fetch_yf_info(resolved: str, timeout: int = 10) -> Optional[dict]:
    """
    yfinance Ticker.info 조회.
    가격 필드가 하나라도 있어야 유효한 응답으로 간주.
    반환값: info dict  |  None(조회 실패)
    """
    try:
        import yfinance as yf  # 지연 임포트
        ticker_obj = yf.Ticker(resolved)

        # fast_info 우선 (네트워크 비용 낮음)
        try:
            fi = ticker_obj.fast_info
            price = getattr(fi, "last_price", None)
            if price:
                return {
                    "_source": "fast_info",
                    "regularMarketPrice": price,
                    "currency":  getattr(fi, "currency",  None),
                    "exchange":  getattr(fi, "exchange",  None),
                    "shortName": None,
                    "longName":  None,
                }
        except Exception:
            pass

        # fast_info 실패 시 full info fallback
        info = ticker_obj.info
        price = (
            info.get("regularMarketPrice")
            or info.get("currentPrice")
            or info.get("previousClose")
        )
        if price is None:
            return None
        return info

    except Exception as exc:
        logger.debug("yfinance 조회 오류 (%s): %s", resolved, exc)
        return None


# ──────────────────────────────────────────────────────────
# 보조 정제 함수
# ──────────────────────────────────────────────────────────

_EXCHANGE_TO_MARKET = {
    # KRX
    "KSC": "KRX", "KOE": "KRX", "XKRX": "KRX", "KSE": "KRX",
    # NASDAQ
    "NMS": "NASDAQ", "NGM": "NASDAQ", "NCM": "NASDAQ", "XNAS": "NASDAQ",
    # NYSE
    "NYQ": "NYSE", "XNYS": "NYSE",
    # AMEX
    "ASE": "AMEX", "XASE": "AMEX",
}


def _derive_market(exchange: str, is_krx: bool) -> str:
    if exchange in _EXCHANGE_TO_MARKET:
        return _EXCHANGE_TO_MARKET[exchange]
    if is_krx:
        return "KRX"
    return "NASDAQ"  # 미국 종목 기본값


def _derive_currency(info_currency: Optional[str], market: str) -> str:
    """
    yfinance currency 필드가 있으면 그대로 사용.
    없거나 빈 문자열이면 시장으로 유추.
    """
    if info_currency and info_currency.upper() in ("KRW", "USD", "EUR", "JPY", "HKD", "GBP"):
        return info_currency.upper()
    return "KRW" if market == "KRX" else "USD"


# ──────────────────────────────────────────────────────────
# 관심종목 자동채움 — yfinance + Claude AI
# ──────────────────────────────────────────────────────────

def _resolve_query_to_ticker(query: str) -> tuple[str, Optional[dict]]:
    """
    query가 ticker 형식이면 그대로 사용,
    종목명처럼 보이면 yf.Search로 ticker 검색.
    반환: (resolved_ticker, yf_info_or_None)
    """
    import yfinance as yf

    # ticker처럼 보이면 바로 시도
    if re.match(r"^[A-Z0-9.\-]{1,10}$", query.upper()) or re.match(r"^\d{5,6}$", query):
        ticker = query.upper()
        is_krx = _is_krx(ticker)
        candidates = _krx_candidates(ticker) if is_krx else _us_candidates(ticker)
        for c in candidates:
            info = _fetch_yf_info(c)
            if info:
                return ticker, info
        return ticker, None

    # 종목명 → yf.Search
    try:
        results = yf.Search(query, max_results=3).quotes
        if results:
            ticker = results[0].get("symbol", "")
            if ticker:
                info = _fetch_yf_info(ticker)
                return ticker.split(".")[0], info  # .KS 등 suffix 제거
    except Exception as exc:
        logger.debug("yf.Search 실패 (%s): %s", query, exc)

    return query.upper(), None


def _fetch_news_text(resolved_ticker: str, max_items: int = 5) -> str:
    """yfinance 뉴스 → 프롬프트용 텍스트. 실패 시 빈 문자열."""
    try:
        import yfinance as yf
        news = yf.Ticker(resolved_ticker).news or []
        lines = []
        for i, n in enumerate(news[:max_items], 1):
            title   = n.get("title", "")
            summary = n.get("summary") or n.get("description") or ""
            if title:
                lines.append(f"{i}. {title}" + (f"\n   {summary}" if summary else ""))
        return "\n".join(lines)
    except Exception:
        return ""


def _load_azure_config() -> dict:
    """
    ~/.openclaw/openclaw.json 에서 Azure OpenAI 접속 정보 읽기.
    반환: {"api_key": ..., "endpoint": ..., "model": ...}
    """
    from pathlib import Path

    config_path = Path.home() / ".openclaw" / "openclaw.json"
    if not config_path.exists():
        raise RuntimeError("OpenClaw 설정 파일을 찾을 수 없습니다: ~/.openclaw/openclaw.json")

    with open(config_path, encoding="utf-8") as f:
        cfg = json.load(f)

    try:
        provider = cfg["models"]["providers"]["microsoft-foundry"]
        api_key  = provider["apiKey"]
        # baseUrl 예: https://xxx.openai.azure.com/openai/v1  → endpoint만 추출
        base_url = provider["baseUrl"]
        endpoint = base_url.split("/openai")[0]
        # 배포된 모델 중 첫 번째 사용 (보통 gpt-4o)
        model = provider["models"][0]["id"] if provider.get("models") else "gpt-4o"
    except (KeyError, IndexError) as exc:
        raise RuntimeError(f"OpenClaw 설정에서 Azure OpenAI 정보를 읽지 못했습니다: {exc}")

    return {"api_key": api_key, "endpoint": endpoint, "model": model}


def _call_llm(prompt: str) -> dict:
    """
    Azure OpenAI (OpenClaw 설정) 호출 → JSON dict 반환.
    별도 환경변수 불필요 — ~/.openclaw/openclaw.json을 그대로 사용.
    """
    from openai import AzureOpenAI

    cfg = _load_azure_config()
    client = AzureOpenAI(
        api_key=cfg["api_key"],
        azure_endpoint=cfg["endpoint"],
        api_version="2024-12-01-preview",
    )

    response = client.chat.completions.create(
        model=cfg["model"],
        messages=[{"role": "user", "content": prompt}],
        max_tokens=512,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content.strip()
    # 혹시 마크다운 코드 블록이 붙어 있으면 제거
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)

    return json.loads(raw)


_LANG_INSTRUCTION = {
    "ko": "한국어, 60자 이내",
    "en": "English, within 60 characters",
    "ja": "日本語、60文字以内",
    "zh": "中文（简体），60字以内",
    "fr": "Français, en moins de 60 caractères",
}


@router.get("/watchlist/{query}")
async def enrich_watchlist(query: str, lang: str = "ko"):
    """
    ticker 또는 종목명 → 관심종목 전체 필드 자동채움.
    yfinance로 종목 정보·뉴스를 수집하고 Claude AI로 필드를 생성한다.
    """
    query = query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="ticker 또는 종목명을 입력해주세요.")
    if len(query) > 50:
        raise HTTPException(status_code=400, detail="입력값이 너무 깁니다.")
    lang_instr = _LANG_INSTRUCTION.get(lang, _LANG_INSTRUCTION["ko"])

    # ── 1) ticker 해석 + 기본 정보 ───────────────────────
    ticker, info = _resolve_query_to_ticker(query)

    if info is None:
        raise HTTPException(
            status_code=502,
            detail=f"'{query}' 종목 정보를 외부 API에서 가져오지 못했습니다. "
                   "ticker 또는 종목명을 확인하고 다시 시도해주세요.",
        )

    is_krx      = _is_krx(ticker)
    exchange    = (info.get("exchange") or "").upper()
    market      = _derive_market(exchange, is_krx)
    currency    = _derive_currency(info.get("currency"), market)
    price       = (
        info.get("regularMarketPrice")
        or info.get("currentPrice")
        or info.get("previousClose")
    )
    company_name = (info.get("shortName") or info.get("longName") or ticker).strip()

    # resolved_ticker: fast_info 경로면 query를 그대로, full info면 exchange suffix 포함
    resolved_ticker = ticker

    # ── 2) 뉴스 수집 ────────────────────────────────────
    # KRX는 .KS/.KQ suffix 필요
    news_ticker = (
        f"{ticker.zfill(6)}.KS" if is_krx else ticker
    )
    news_text = _fetch_news_text(news_ticker)

    # ── 3) Claude AI로 관심종목 필드 생성 ───────────────
    price_str = f"{price:,.0f} {currency}" if price else "정보 없음"
    news_section = f"최근 뉴스:\n{news_text}" if news_text else "최근 뉴스: 없음"

    prompt = f"""다음 종목의 정보와 뉴스를 바탕으로 투자 관심종목 등록 정보를 작성해줘.

종목: {ticker} ({company_name})
시장: {market}
현재가: {price_str}

{news_section}

아래 JSON 형식으로만 응답해줘. 다른 설명 없이 JSON만:
{{
  "watch_reason": "관심 이유 — 핵심 투자 아이디어 중심, {lang_instr}",
  "ideal_entry": "이상적 진입가 — 현재가 기준 숫자만 (단위 없음)",
  "trigger_condition": "매수 트리거 — 구체적 지표나 이벤트, {lang_instr}",
  "invalidation": "무효화 조건 — 이 조건 발생 시 관심 철회, {lang_instr}",
  "risk_notes": "주요 리스크 — {lang_instr}",
  "priority": 우선순위_정수 (1=최고관심, 5=낮음)
}}"""

    try:
        ai = _call_llm(prompt)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as exc:
        logger.warning("Claude 호출 실패: %s", exc)
        raise HTTPException(
            status_code=502,
            detail="AI 분석 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
        )

    return {
        "ticker":            ticker,
        "company_name":      company_name,
        "market":            market,
        "currency":          currency,
        "current_price":     price,
        "watch_reason":      ai.get("watch_reason", ""),
        "ideal_entry":       str(ai.get("ideal_entry", "")),
        "trigger_condition": ai.get("trigger_condition", ""),
        "invalidation":      ai.get("invalidation", ""),
        "risk_notes":        ai.get("risk_notes", ""),
        "priority":          str(ai.get("priority", "3")),
    }


# ──────────────────────────────────────────────────────────
# Endpoint
# ──────────────────────────────────────────────────────────

@router.get("/{ticker}")
async def enrich_ticker(ticker: str):
    ticker = ticker.strip().upper()

    # ── 입력 검증 (400) ─────────────────────────────────
    if not ticker:
        raise HTTPException(status_code=400, detail="ticker를 입력해주세요.")
    if len(ticker) > 20:
        raise HTTPException(status_code=400, detail=f"ticker가 너무 깁니다: '{ticker}'")
    if not re.match(r"^[A-Z0-9.\-]+$", ticker):
        raise HTTPException(
            status_code=400,
            detail=f"ticker에 허용되지 않는 문자가 포함되어 있습니다: '{ticker}'"
        )

    is_krx = _is_krx(ticker)
    candidates = _krx_candidates(ticker) if is_krx else _us_candidates(ticker)

    # ── 후보를 순서대로 시도 ────────────────────────────
    info: Optional[dict] = None
    resolved: Optional[str] = None
    tried: list[str] = []

    for candidate in candidates:
        tried.append(candidate)
        info = _fetch_yf_info(candidate)
        if info is not None:
            resolved = candidate
            break

    # ── 외부 API 실패 (502) ─────────────────────────────
    if info is None:
        tried_str = ", ".join(tried)
        raise HTTPException(
            status_code=502,
            detail=(
                f"'{ticker}' 종목 정보를 외부 API에서 가져오지 못했습니다. "
                f"시도한 ticker: [{tried_str}]. "
                "ticker를 확인하거나 잠시 후 다시 시도해주세요."
            ),
        )

    # ── 정제 ────────────────────────────────────────────
    exchange    = (info.get("exchange") or "").upper()
    market      = _derive_market(exchange, is_krx)
    currency    = _derive_currency(info.get("currency"), market)
    price       = (
        info.get("regularMarketPrice")
        or info.get("currentPrice")
        or info.get("previousClose")
    )
    company_name = (info.get("shortName") or info.get("longName") or "").strip()

    return {
        "ticker":          ticker,
        "resolved_ticker": resolved,
        "company_name":    company_name,
        "market":          market,
        "currency":        currency,
        "current_price":   price,
        "exchange":        exchange or None,
        "price_source":    info.get("_source", "yfinance_full"),
    }
