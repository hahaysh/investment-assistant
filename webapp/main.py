import subprocess
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from config import DAILY_REPORTS_DIR, WEEKLY_REPORTS_DIR, BRIEFING_SCRIPT
from routers import reports, portfolio, watchlist, enrich

app = FastAPI(title="투자 비서 API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reports.router,   prefix="/api/reports",   tags=["reports"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["portfolio"])
app.include_router(watchlist.router, prefix="/api/watchlist", tags=["watchlist"])
app.include_router(enrich.router,    prefix="/api/enrich",    tags=["enrich"])

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", response_class=FileResponse)
async def serve_index():
    return static_dir / "index.html"


@app.post("/api/run-briefing")
async def run_briefing():
    if not BRIEFING_SCRIPT.exists():
        raise HTTPException(status_code=404, detail=f"브리핑 스크립트를 찾을 수 없습니다: {BRIEFING_SCRIPT}")
    subprocess.Popen(["python3", str(BRIEFING_SCRIPT)])
    return {"status": "started", "message": "브리핑 생성을 시작했습니다."}


@app.get("/api/status")
async def get_status():
    last_daily = None
    if DAILY_REPORTS_DIR.exists():
        files = sorted(DAILY_REPORTS_DIR.glob("*.md"), reverse=True)
        if files:
            last_daily = files[0].stem

    last_weekly = None
    if WEEKLY_REPORTS_DIR.exists():
        files = sorted(WEEKLY_REPORTS_DIR.glob("*.md"), reverse=True)
        if files:
            last_weekly = files[0].stem

    return {
        "status": "ok",
        "last_daily": last_daily,
        "last_weekly": last_weekly,
    }
