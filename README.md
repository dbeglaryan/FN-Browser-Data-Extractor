# 🧊 FrostNode | Browser Data Extractor ⚡

A professional **browser artifact extractor** that stays **portable** and **forensic-grade**.  
Built with 🐍 **Python**, no external dependencies required.

Collects **history, cookies, bookmarks, downloads, searches, sessions, and extensions**  
from Chrome, Edge, and Firefox — with full logging and manifest signing. 🔍

---

## ✨ Features
- 🌐 Cross-browser support → Chrome, Edge, Firefox  
- 📖 Artifacts: history, bookmarks, cookies, downloads, searches, sessions, extensions  
- 🧭 Timeline export for investigations  
- 📑 Markdown reports with metadata and counts  
- 🔒 Forensic integrity with SHA256 manifest + signature  
- 📦 Portable → pure Python, no dependencies  
- 🚫 Access-safe → logs “Access Denied” instead of crashing  

---

## 🚀 Run locally
```bash
python main.py --format csv --out artifacts_export.csv
```

---

## 📊 Example Run
```text
--- SUMMARY ---
Browsers scanned: chrome, edge, firefox
Artifacts collected: { history: 16261, search: 1351, session: 3, extension: 21, bookmark: 106, download: 2602, cookie: 40 }
Output files: ['artifacts_export.csv']
```

---

## 📦 Packaging (optional)
```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile main.py
```
Builds appear in `dist/`.

---

## 📜 License
MIT — see [LICENSE](LICENSE).
