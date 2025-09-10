import os, sys, shutil, tempfile, hashlib, platform, getpass, socket, subprocess
from pathlib import Path
from datetime import datetime

# ---- Time helpers ----
def utc_from_webkit(ts):
    if not ts or ts == 0:
        return None
    return datetime.utcfromtimestamp(ts/1e6 - 11644473600).isoformat()

def utc_from_unix(ts):
    if not ts or ts == 0:
        return None
    return datetime.utcfromtimestamp(ts/1e6).isoformat()

# ---- Hashing ----
def sha256_file(path: Path):
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None

# ---- Metadata ----
def get_metadata():
    return {
        "hostname": socket.gethostname(),
        "username": getpass.getuser(),
        "os": platform.platform(),
        "acquired_utc": datetime.utcnow().isoformat() + "Z"
    }

# ---- Logging ----
def log_line(msg):
    with open("history_export.log", "a", encoding="utf-8") as f:
        f.write(f"[{datetime.utcnow().isoformat()}Z] {msg}\n")

def progress(msg):
    print(f"[.] {msg}")

# ---- Manifest ----
def build_manifest(meta, outputs, all_rows, errors):
    return {
        "metadata": meta,
        "outputs": {str(f): sha256_file(f) for f in outputs},
        "counts": {r["artifact"]: sum(1 for rr in all_rows if rr["artifact"]==r["artifact"]) for r in all_rows},
        "errors": errors
    }

def sign_manifest(path):
    try:
        data = Path(path).read_bytes()
        sig = hashlib.sha256(data).hexdigest()
        Path(path + ".sig").write_text(sig, encoding="utf-8")
        log_line("Manifest signed with SHA256")
    except Exception as e:
        log_line(f"Failed to sign manifest: {e}")

# ---- File copy with VSS fallback ----
def copy_with_vss(path: Path) -> Path:
    shadow_path = Path(tempfile.gettempdir()) / f"copy_{os.getpid()}_{path.name}"
    try:
        output = subprocess.check_output(["vssadmin", "list", "shadows"], text=True, stderr=subprocess.DEVNULL)
        for line in output.splitlines():
            if "Shadow Copy Volume:" in line:
                vol = line.split(":",1)[1].strip()
                candidate = Path(vol) / str(path).lstrip("\\")
                if candidate.exists():
                    shutil.copy2(candidate, shadow_path)
                    return shadow_path
    except Exception as e:
        log_line(f"VSS fallback failed for {path}: {e}")
    return None

def safe_copy(path: Path) -> Path:
    if not path.exists():
        return None
    tmp = Path(tempfile.gettempdir()) / f"artifact_{os.getpid()}_{path.name}"
    try:
        shutil.copy2(path, tmp)
        return tmp
    except PermissionError:
        log_line(f"Permission denied copying {path}, trying VSS")
        if sys.platform.startswith("win"):
            vss = copy_with_vss(path)
            if vss: return vss
    except Exception as e:
        log_line(f"Error copying {path}: {e}")
    return None

# ---- User home discovery ----
def find_all_user_homes():
    homes = [Path.home()]
    plat = sys.platform
    if plat.startswith("win"):
        base = Path("C:/Users")
    elif plat == "darwin":
        base = Path("/Users")
    else:
        base = Path("/home")
    if base.exists():
        homes = [p for p in base.iterdir() if p.is_dir()]
    return homes

# ---- Browser profile discovery ----
def find_browsers():
    found = {}
    for home in find_all_user_homes():
        plat = sys.platform

        def add(name, path):
            try:
                if path.exists():
                    found.setdefault(name, []).append(path)
            except PermissionError:
                log_line(f"[ACCESS DENIED] Could not access {path} (user={home.name})")
            except Exception as e:
                log_line(f"[ERROR] Failed to check {path}: {e}")

        try:
            if plat.startswith("win"):
                base_local = home / "AppData/Local"
                base_roam  = home / "AppData/Roaming"

                # Chrome: all profiles
                chrome_base = base_local / "Google/Chrome/User Data"
                try:
                    if chrome_base.exists():
                        for prof in chrome_base.glob("*/History"):
                            add("chrome", prof)
                except PermissionError:
                    log_line(f"[ACCESS DENIED] Cannot list Chrome profiles for {home}")

                # Edge: all profiles
                edge_base = base_local / "Microsoft/Edge/User Data"
                try:
                    if edge_base.exists():
                        for prof in edge_base.glob("*/History"):
                            add("edge", prof)
                except PermissionError:
                    log_line(f"[ACCESS DENIED] Cannot list Edge profiles for {home}")

                # Firefox
                add("firefox", base_roam / "Mozilla/Firefox/Profiles")

            elif plat == "darwin":
                chrome_base = home / "Library/Application Support/Google/Chrome"
                try:
                    if chrome_base.exists():
                        for prof in chrome_base.glob("*/History"):
                            add("chrome", prof)
                except PermissionError:
                    log_line(f"[ACCESS DENIED] Cannot list Chrome profiles for {home}")

                edge_base = home / "Library/Application Support/Microsoft Edge"
                try:
                    if edge_base.exists():
                        for prof in edge_base.glob("*/History"):
                            add("edge", prof)
                except PermissionError:
                    log_line(f"[ACCESS DENIED] Cannot list Edge profiles for {home}")

                add("safari", home / "Library/Safari/History.db")
                add("firefox", home / "Library/Application Support/Firefox/Profiles")

            else:  # Linux
                chrome_base = home / ".config/google-chrome"
                try:
                    if chrome_base.exists():
                        for prof in chrome_base.glob("*/History"):
                            add("chrome", prof)
                except PermissionError:
                    log_line(f"[ACCESS DENIED] Cannot list Chrome profiles for {home}")

                edge_base = home / ".config/microsoft-edge"
                try:
                    if edge_base.exists():
                        for prof in edge_base.glob("*/History"):
                            add("edge", prof)
                except PermissionError:
                    log_line(f"[ACCESS DENIED] Cannot list Edge profiles for {home}")

                add("firefox", home / ".mozilla/firefox")

        except PermissionError:
            log_line(f"[ACCESS DENIED] Skipping entire home directory {home}")
        except Exception as e:
            log_line(f"[ERROR] Unexpected error scanning {home}: {e}")

    return found
