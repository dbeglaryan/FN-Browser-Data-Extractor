from pathlib import Path
from . import utils
import json

def extract(browser, path: Path, meta):
    rows = []
    if browser in ["chrome","edge"]:
        extdir = path.parent / "Extensions"
        if extdir.exists():
            for ext in extdir.glob("*/*/manifest.json"):
                try:
                    data = json.loads(ext.read_text(encoding="utf-8"))
                    rows.append({
                        **meta, "browser": browser, "artifact": "extension",
                        "profile": str(path.parent), "url": data.get("homepage_url",""),
                        "title": data.get("name",""), "visit_count": None,
                        "visit_time_utc": None, "extra": f"version={data.get('version','')}"
                    })
                except Exception as e:
                    utils.log_line(f"Error extension {ext}: {e}")
    elif browser=="firefox":
        profs = path.glob("*.default*") if path.is_dir() else []
        for prof in profs:
            extdir = prof / "extensions"
            if extdir.exists():
                for xpi in extdir.glob("*.xpi"):
                    rows.append({
                        **meta, "browser": "firefox", "artifact": "extension",
                        "profile": str(prof), "url": "", "title": xpi.name,
                        "visit_count": None, "visit_time_utc": None, "extra": "xpi package"
                    })
    return rows
