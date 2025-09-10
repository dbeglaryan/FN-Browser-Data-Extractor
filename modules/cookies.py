import sqlite3
from pathlib import Path
from . import utils

def extract(browser, path: Path, meta):
    rows = []
    if browser in ["chrome","edge"]:
        ck = path.parent / "Cookies"
        tmp = utils.safe_copy(ck)
        if not tmp: return rows
        try:
            con = sqlite3.connect(str(tmp))
            cur = con.cursor()
            cur.execute("SELECT host_key, name, value, last_access_utc FROM cookies")
            for host, name, val, ts in cur.fetchall():
                # Chromium often encrypts values, here we just mark them
                if val and val.startswith("v10"): 
                    val = "<encrypted>"
                rows.append({
                    **meta, "browser": browser, "artifact": "cookie",
                    "profile": str(path.parent), "url": host, "title": name,
                    "visit_count": None, "visit_time_utc": utils.utc_from_webkit(ts), "extra": f"value={val}"
                })
            con.close()
        except Exception as e:
            utils.log_line(f"Error cookies {browser}: {e}")
    elif browser=="firefox":
        profs = path.glob("*.default*") if path.is_dir() else []
        for prof in profs:
            ck = prof / "cookies.sqlite"
            tmp = utils.safe_copy(ck)
            if not tmp: continue
            try:
                con = sqlite3.connect(str(tmp))
                cur = con.cursor()
                cur.execute("SELECT host, name, value, lastAccessed FROM moz_cookies")
                for host, name, val, ts in cur.fetchall():
                    rows.append({
                        **meta, "browser": "firefox", "artifact": "cookie",
                        "profile": str(prof), "url": host, "title": name,
                        "visit_count": None, "visit_time_utc": utils.utc_from_unix(ts), "extra": f"value={val}"
                    })
                con.close()
            except Exception as e:
                utils.log_line(f"Error cookies firefox {prof}: {e}")
    return rows
