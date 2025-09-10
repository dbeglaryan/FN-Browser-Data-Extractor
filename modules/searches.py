import sqlite3
from pathlib import Path
from . import utils

def extract(browser, path: Path, meta):
    rows = []
    if browser in ["chrome","edge"]:
        tmp = utils.safe_copy(path)
        if not tmp: return rows
        try:
            con = sqlite3.connect(str(tmp))
            cur = con.cursor()
            cur.execute("SELECT term, url_id FROM keyword_search_terms")
            for term, url_id in cur.fetchall():
                rows.append({
                    **meta, "browser": browser, "artifact": "search",
                    "profile": str(path.parent), "url": f"url_id={url_id}", "title": term,
                    "visit_count": None, "visit_time_utc": None, "extra": ""
                })
            con.close()
        except Exception as e:
            utils.log_line(f"Error searches {browser}: {e}")
    elif browser=="firefox":
        profs = path.glob("*.default*") if path.is_dir() else []
        for prof in profs:
            fh = prof / "formhistory.sqlite"
            tmp = utils.safe_copy(fh)
            if not tmp: continue
            try:
                con = sqlite3.connect(str(tmp))
                cur = con.cursor()
                cur.execute("SELECT fieldname, value, timesUsed FROM moz_formhistory")
                for fn, val, times in cur.fetchall():
                    rows.append({
                        **meta, "browser": "firefox", "artifact": "search",
                        "profile": str(prof), "url": "", "title": val,
                        "visit_count": times, "visit_time_utc": None, "extra": f"field={fn}"
                    })
                con.close()
            except Exception as e:
                utils.log_line(f"Error searches firefox {prof}: {e}")
    return rows
