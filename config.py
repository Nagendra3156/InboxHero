import os
from pathlib import Path
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

FOLDERPATH = Path(__file__).resolve().parent
INBOX = FOLDERPATH / "data/inbox.json"
TRACE = FOLDERPATH / "audit_log.jsonl"
PREFS = FOLDERPATH / "state/preferences.json"
DECISIONS = FOLDERPATH / "decisions.json"
OUTBOX = FOLDERPATH / "outbox"
DASHBOARD = FOLDERPATH / "dashboard/dashboard.html"
DASHJSON = FOLDERPATH / "dashboard/dashboard.json"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
