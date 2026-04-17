from pathlib import Path

DATA_DIR = Path("~/investment-assistant/data").expanduser()
PORTFOLIO_CSV = DATA_DIR / "portfolio.csv"
WATCHLIST_CSV = DATA_DIR / "watchlist.csv"

DAILY_REPORTS_DIR = Path("~/investment-assistant/reports/daily").expanduser()
WEEKLY_REPORTS_DIR = Path("~/investment-assistant/reports/weekly").expanduser()

BRIEFING_SCRIPT = Path("~/investment-assistant/generate_briefing.py").expanduser()
