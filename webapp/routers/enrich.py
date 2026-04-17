"""
GET /api/enrich/{ticker}

ticker 하나를 받아 yfinance로 종목 정보를 조회하고,
프론트엔드 자동채움에 필요한 필드를 정제해서 반환한다.

오류 구분
  400  입력값이 잘못됨 (빈 ticker, 너무 긴 문자열 등)
  502  외부 API(yfinance) 조회 실패 또는 종목 미존재
"""

import re
import time
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
