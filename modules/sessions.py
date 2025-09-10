import json, lzma
from pathlib import Path
from . import utils

def extract(browser, path: Path, meta):
    rows = []
    if browser in ["chrome","edge"]:
        # Chromium session files vary; best-effort parse
        sess_file = path.parent / "Sessions"
        if sess_file.exists():
            rows.append({
                **meta, "browser": browser, "artifact": "session",
                "profile": str(path.parent), "url": "<session data>", "title": "",
                "visit_count": None, "visit_time_utc": None, "extra": "binary session not parsed"
            })
    elif browser=="firefox":
        profs = path.glob("*.default*") if path.is_dir() else []
        for prof in profs:
            ss = prof / "sessionstore.jsonlz4"
            if ss.exists():
                try:
                    raw = ss.read_bytes()
                    # Firefox sessionstore uses LZ4; fallback: mark as raw
                    rows.append({
                        **meta, "browser": "firefox", "artifact": "session",
                        "profile": str(prof), "url": "<sessionstore>", "title": "",
                        "visit_count": None, "visit_time_utc": None, "extra": f"size={len(raw)}"
                    })
                except Exception as e:
                    utils.log_line(f"Error sessions firefox {prof}: {e}")
    return rows
