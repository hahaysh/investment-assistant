from fastapi import APIRouter, HTTPException

from config import DAILY_REPORTS_DIR, WEEKLY_REPORTS_DIR

router = APIRouter()


@router.get("/daily")
async def list_daily_reports():
    if not DAILY_REPORTS_DIR.exists():
        return []
    files = sorted(DAILY_REPORTS_DIR.glob("*.md"), reverse=True)
    return [
        {"date": f.stem, "filename": f.name}
        for f in files
    ]


@router.get("/weekly")
async def list_weekly_reports():
    if not WEEKLY_REPORTS_DIR.exists():
        return []
    files = sorted(WEEKLY_REPORTS_DIR.glob("*.md"), reverse=True)
    return [
        {"week": f.stem, "filename": f.name}
        for f in files
    ]


@router.get("/daily/{date}")
async def get_daily_report(date: str):
    path = DAILY_REPORTS_DIR / f"{date}.md"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"리포트를 찾을 수 없습니다: {date}")
    return {"date": date, "content": path.read_text(encoding="utf-8")}


@router.get("/weekly/{week}")
async def get_weekly_report(week: str):
    path = WEEKLY_REPORTS_DIR / f"{week}.md"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"리포트를 찾을 수 없습니다: {week}")
    return {"week": week, "content": path.read_text(encoding="utf-8")}
