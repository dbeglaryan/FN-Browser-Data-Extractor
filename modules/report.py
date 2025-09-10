from pathlib import Path
import json

def generate(manifest, rows):
    out = Path("report.md")
    counts = manifest["counts"]
    md = []
    md.append(f"# Browser Artifact Report")
    md.append("")
    md.append(f"**Host**: {manifest['metadata']['hostname']}  ")
    md.append(f"**User**: {manifest['metadata']['username']}  ")
    md.append(f"**OS**: {manifest['metadata']['os']}  ")
    md.append(f"**Acquired at**: {manifest['metadata']['acquired_utc']}  ")
    md.append("")
    md.append("## Artifact Counts")
    for k,v in counts.items():
        md.append(f"- {k}: {v}")
    md.append("")
    md.append("## Outputs")
    for f,h in manifest["outputs"].items():
        md.append(f"- {f} (SHA256={h})")
    md.append("")
    out.write_text("\n".join(md), encoding="utf-8")
    return out
