import csv
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config import PORTFOLIO_CSV

router = APIRouter()

COLUMNS = [
    "ticker", "company_name", "market", "holding_status",
    "quantity", "avg_cost", "currency", "target_weight",
    "thesis", "risk_notes", "priority",
]


def _read_csv() -> list[dict[str, Any]]:
    if not PORTFOLIO_CSV.exists():
        return []
    with PORTFOLIO_CSV.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _write_csv(rows: list[dict[str, Any]]) -> None:
    PORTFOLIO_CSV.parent.mkdir(parents=True, exist_ok=True)
    with PORTFOLIO_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


class PortfolioItem(BaseModel):
    ticker: str
    company_name: str = ""
    market: str = ""
    holding_status: str = ""
    quantity: str = ""
    avg_cost: str = ""
    currency: str = ""
    target_weight: str = ""
    thesis: str = ""
    risk_notes: str = ""
    priority: str = ""


@router.get("")
async def get_portfolio():
    return _read_csv()


@router.post("", status_code=201)
async def add_portfolio(item: PortfolioItem):
    rows = _read_csv()
    if any(r["ticker"].upper() == item.ticker.upper() for r in rows):
        raise HTTPException(status_code=400, detail=f"이미 존재하는 ticker입니다: {item.ticker}")
    rows.append(item.model_dump())
    _write_csv(rows)
    return item.model_dump()


@router.put("/{ticker}")
async def update_portfolio(ticker: str, item: PortfolioItem):
    rows = _read_csv()
    idx = next((i for i, r in enumerate(rows) if r["ticker"].upper() == ticker.upper()), None)
    if idx is None:
        raise HTTPException(status_code=404, detail=f"ticker를 찾을 수 없습니다: {ticker}")
    rows[idx] = item.model_dump()
    _write_csv(rows)
    return rows[idx]


@router.delete("/{ticker}", status_code=204)
async def delete_portfolio(ticker: str):
    rows = _read_csv()
    new_rows = [r for r in rows if r["ticker"].upper() != ticker.upper()]
    if len(new_rows) == len(rows):
        raise HTTPException(status_code=404, detail=f"ticker를 찾을 수 없습니다: {ticker}")
    _write_csv(new_rows)
