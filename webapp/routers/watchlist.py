import csv
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config import WATCHLIST_CSV

router = APIRouter()

COLUMNS = [
    "ticker", "company_name", "market", "watch_reason",
    "ideal_entry", "trigger_condition", "invalidation",
    "risk_notes", "priority",
]


def _read_csv() -> list[dict[str, Any]]:
    if not WATCHLIST_CSV.exists():
        return []
    with WATCHLIST_CSV.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _write_csv(rows: list[dict[str, Any]]) -> None:
    WATCHLIST_CSV.parent.mkdir(parents=True, exist_ok=True)
    with WATCHLIST_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


class WatchlistItem(BaseModel):
    ticker: str
    company_name: str = ""
    market: str = ""
    watch_reason: str = ""
    ideal_entry: str = ""
    trigger_condition: str = ""
    invalidation: str = ""
    risk_notes: str = ""
    priority: str = ""


@router.get("")
async def get_watchlist():
    return _read_csv()


@router.post("", status_code=201)
async def add_watchlist(item: WatchlistItem):
    rows = _read_csv()
    if any(r["ticker"].upper() == item.ticker.upper() for r in rows):
        raise HTTPException(status_code=400, detail=f"이미 존재하는 ticker입니다: {item.ticker}")
    rows.append(item.model_dump())
    _write_csv(rows)
    return item.model_dump()


@router.put("/{ticker}")
async def update_watchlist(ticker: str, item: WatchlistItem):
    rows = _read_csv()
    idx = next((i for i, r in enumerate(rows) if r["ticker"].upper() == ticker.upper()), None)
    if idx is None:
        raise HTTPException(status_code=404, detail=f"ticker를 찾을 수 없습니다: {ticker}")
    rows[idx] = item.model_dump()
    _write_csv(rows)
    return rows[idx]


@router.delete("/{ticker}", status_code=204)
async def delete_watchlist(ticker: str):
    rows = _read_csv()
    new_rows = [r for r in rows if r["ticker"].upper() != ticker.upper()]
    if len(new_rows) == len(rows):
        raise HTTPException(status_code=404, detail=f"ticker를 찾을 수 없습니다: {ticker}")
    _write_csv(new_rows)
