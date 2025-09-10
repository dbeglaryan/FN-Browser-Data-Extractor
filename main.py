import argparse, json, csv, sqlite3, gzip
from pathlib import Path
from modules import history, bookmarks, cookies, downloads, searches, sessions, extensions, utils, report

def write_outputs(rows, fmt, out, compress=False, split_artifacts=False, per_browser=False):
    """Write extracted rows to disk in chosen format(s)."""
    outputs = []
    if not rows:
        return outputs

    def open_out(path):
        if compress:
            return gzip.open(path, "wt", encoding="utf-8")
        return open(path, "w", encoding="utf-8")

    # Group rows if needed
    if split_artifacts or per_browser:
        groups = {}
        for r in rows:
            key = []
            if per_browser:
                key.append(r["browser"])
            if split_artifacts:
                key.append(r["artifact"])
            groups.setdefault("_".join(key), []).append(r)
    else:
        groups = {"all": rows}

    for gname, grows in groups.items():
        outname = out
        stem, suf = Path(out).stem, Path(out).suffix
        if gname != "all":
            outname = f"{stem}_{gname}{suf}"
        outputs.append(Path(outname))

        if fmt == "csv":
            with open_out(outname) as f:
                w = csv.DictWriter(f, fieldnames=grows[0].keys())
                w.writeheader()
                for r in grows:
                    w.writerow(r)

        elif fmt == "json":
            with open_out(outname) as f:
                json.dump(grows, f, indent=2, ensure_ascii=False)

        elif fmt == "jsonl":
            with open_out(outname) as f:
                for r in grows:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")

        elif fmt == "sqlite":
            conn = sqlite3.connect(outname)
            cols = list(grows[0].keys())
            conn.execute(f"CREATE TABLE data ({','.join(cols)})")
            conn.executemany(f"INSERT INTO data VALUES ({','.join(['?']*len(cols))})",
                             [tuple(r[c] for c in cols) for r in grows])
            conn.commit()
            conn.close()

    return outputs

BANNER = r"""
 _______  ______  _____  _______ _______ _    _ _______ _____       
 |______ |_____/ |     | |______    |     \  /  |______   |   |     
 |       |    \_ |_____| ______|    |      \/   |______ __|__ |_____
                                                                     
"""

def main():
    print(BANNER)
    print("Frostveil | Browser Forensics Toolkit — unveiling traces hidden beneath the frost\n")
    ap = argparse.ArgumentParser(
        prog="frostveil",
        description="Frostveil | Browser Forensics Toolkit — fast, portable, forensic-grade extraction of browser artifacts (Chrome, Edge, Firefox)."
    )
    ap.add_argument("--format", choices=["csv", "json", "jsonl", "sqlite"], default="csv", help="Output format")
    ap.add_argument("--out", default="artifacts_export.csv", help="Output file name")
    ap.add_argument("--per-browser", action="store_true", help="separate outputs per browser")
    ap.add_argument("--split-artifacts", action="store_true", help="separate outputs per artifact")
    ap.add_argument("--compress", action="store_true", help="gzip compress output files")
    ap.add_argument("--timeline", action="store_true", help="export unified timeline JSON")
    ap.add_argument("--report", action="store_true", help="generate human-readable Markdown report")
    args = ap.parse_args()

    meta = utils.get_metadata()
    utils.log_line(f"=== Acquisition started metadata={meta} ===")

    browsers = utils.find_browsers()
    all_rows, errors = [], []

    extractors = [history, bookmarks, cookies, downloads, searches, sessions, extensions]

    for b, paths in browsers.items():
        for p in paths:
            utils.progress(f"Processing {b} {p}")
            for ex in extractors:
                try:
                    all_rows.extend(ex.extract(b, p, meta))
                except Exception as e:
                    msg = f"ERROR {b} {p}: {e}"
                    errors.append(msg)
                    utils.log_line(msg)

    outputs = write_outputs(all_rows, args.format, args.out, compress=args.compress,
                            split_artifacts=args.split_artifacts, per_browser=args.per_browser)

    if args.timeline:
        tpath = Path("timeline.json")
        with open(tpath, "w", encoding="utf-8") as f:
            json.dump(sorted([r for r in all_rows if r.get("visit_time_utc")],
                             key=lambda r: r["visit_time_utc"]),
                      f, indent=2, ensure_ascii=False)
        outputs.append(tpath)

    manifest = utils.build_manifest(meta, outputs, all_rows, errors)
    with open("manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    utils.sign_manifest("manifest.json")

    if args.report:
        report.generate(manifest)

    print("\n=== Frostveil Extraction Summary ===")
    print(f"Host: {meta['hostname']} User: {meta['username']} OS: {meta['os']}")
    print(f"Acquired at: {meta['acquired_utc']}")
    print(f"Browsers scanned: {', '.join(browsers.keys())}")
    print(f"Artifacts collected: {{ {', '.join(f'{k}: {v}' for k,v in manifest['counts'].items())} }}")
    print(f"Output files: {[str(x) for x in outputs]}")
    if errors:
        print("\n[!] Errors/Access Denied:")
        for e in errors:
            print("   -", e)
        print(f"\n[!] Total errors/access denied: {len(errors)}")


if __name__ == "__main__":
    main()
