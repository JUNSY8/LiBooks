<p align="center">
  <strong>LiBooks</strong><br>
  <em>Your personal PDF library — local, private, and built to read.</em>
</p>

<p align="center">
  Desktop app for importing, organizing, and reading PDF books.<br>
  Built with <strong>Python</strong>, <strong>PyQt5</strong>, <strong>PyMuPDF</strong>, and <strong>SQLite</strong> (SQLAlchemy + Alembic).<br>
  Available in <strong>English</strong> and <strong>Spanish</strong>.
</p>

<p align="center">
  <a href="https://github.com/JUNSY8/LiBooks/releases/latest">Download</a> ·
  <a href="#features">Features</a> ·
  <a href="#installation-developers">Install</a> ·
  <a href="#licensing-model-public-repo--protected-commercial-use">License</a>
</p>

---

## Highlights

| Area | What you get |
|------|----------------|
| **Library** | Grid/list views, covers, drag & drop, collections, tags, filters |
| **Brillo** | 5-level personal importance scale — assign from the library, no edit dialog needed |
| **Reader** | Zoom, search, bookmarks, highlights, notes, OCR |
| **Sync & backup** | Encrypted folder sync (AES-GCM) and ZIP library backup |
| **Privacy** | Everything stays on your machine — no cloud account required |

---

## Features

### Library & organization

- **Grid and list views** with cover thumbnails extracted from PDFs.
- **Drag & drop** import, folder import, and duplicate detection (file hash).
- **Collections** (many-to-many groups) with sidebar navigation.
- **Free tags** with inline editing on book cards and a tag picker popup.
- **Reading status** — unread, in progress, completed, paused, abandoned (manual or automatic from progress).
- **Brillo bibliográfico** — a fixed 5-level scale (Bruma → Chispa → Llama → Resplandor → Farol) to mark how important each book is *to you*. Luminous dots on every card; click to rate, hover for level descriptions.
- Sort and filter by title, author, date, progress, status, tag, or brillo.
- **Continue reading** card for the last opened book.

### PDF reader

- Lazy page rendering, zoom, full-text search, and reading mode.
- Bookmarks, text highlights, and anchored notes.
- Sidebar with outline, bookmarks, and annotations.
- **OCR** for scanned pages (Tesseract + PyMuPDF).
- Export notes to Markdown / plain text.

### Statistics & settings

- Reading stats dashboard.
- App settings: language, library layout, sync folder, OCR path.

### Sync, backup & licensing

- Encrypted **folder sync** between devices (progress + annotations).
- ZIP **library backup** with merge support.
- **14-day trial** on first launch; RSA license activation afterward.
- Onboarding wizard and optional update check via `release/version.json`.

---

## Brillo bibliográfico

LiBooks uses **Brillo** instead of free-form categories or star ratings: a proprietary scale that answers *“how much does this book shine in my library?”*

| Level | Name | Meaning |
|:-----:|------|---------|
| 1 | Bruma | Faint presence |
| 2 | Chispa | Catches your eye now and then |
| 3 | Llama | Solid staple on your shelf |
| 4 | Resplandor | Standout work you recommend |
| 5 | Farol | Essential — a beacon of your library |

Each book has **one brillo level** (or none). Set it directly from the library view; tooltips explain every level.

---

## Licensing model

The source code may be **public on GitHub** for transparency, but **using LiBooks requires a valid license** issued by the software owner.

| Layer | What it protects |
|-------|------------------|
| **Legal (EULA)** | Prohibits use, copying, and redistribution without a license. See [LICENSE](LICENSE). |
| **Technical (RSA)** | The app verifies a digital signature on every launch. |
| **Practical** | Bypassing verification requires modifying the binary — more effort than using the product legitimately. |

> No desktop app is 100% tamper-proof. The goal is to deter casual unauthorized use and support a commercial product legally.

---

## Project structure

```
LiBooks/
├── main.py                 # Entry point
├── interfaz.py             # Main window
├── library_view.py         # Grid/list, import, filters, brillo
├── brillo.py / brillo_picker.py
├── pdf_viewer.py           # PDF reader
├── reading_status.py       # Reading status logic
├── tag_picker.py           # Inline tag/status picker
├── sync_engine.py          # Encrypted sync
├── db.py / models.py / crud.py
├── alembic/                # Migrations (001–007)
├── locales/                # en.json, es.json
├── assets/icons/
├── installer/              # Inno Setup (Windows)
├── release/                # version.json
└── scripts/                # Build & owner tools
```

---

## Requirements

- **Python** 3.9–3.13 (PyQt5 wheels up to 3.13)
- Dependencies in `requirements.txt`
- **Optional:** [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) for scanned PDF search
- **Windows packaging:** [Inno Setup 6](https://jrsoftware.org/isdl.php), [Windows SDK](https://developer.microsoft.com/windows/downloads/windows-sdk/) (signing)

---

## Installation (developers)

```bash
git clone https://github.com/JUNSY8/LiBooks.git
cd LiBooks
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux
pip install -r requirements.txt
python main.py
```

Migrations run automatically on startup. For manual control:

```bash
alembic upgrade head
```

### Initial key setup (owner only)

```bash
python scripts/generate_keypair.py
python scripts/generate_license.py --holder "JUNSY" --perpetual
```

See [keys/README.md](keys/README.md).

---

## User data location

| OS | Path |
|----|------|
| **Windows** | `%LOCALAPPDATA%\LiBooks\` |
| **Linux** | `~/.local/share/LiBooks/` |

Contains: `libooks.db`, `libros/` (PDFs), `license.key`, settings, and logs.

---

## Packaging

### Windows executable

```powershell
.\scripts\build_windows.ps1
```

Output: `dist\LiBooks.exe`.

### Windows signed installer

```powershell
$env:LIBOOKS_SIGN_PFX = "C:\path\to\codesign.pfx"
$env:LIBOOKS_SIGN_PASSWORD = "your-password"
.\scripts\build_installer.ps1
```

Output: `dist\LiBooks-Setup-{version}.exe`. Details: [installer/README.md](installer/README.md).

### Linux executable

```bash
bash scripts/build_linux.sh
```

Output: `dist/LiBooks` and release tarball `LiBooks-{version}-Linux-x86_64.tar.gz`.

### CI & releases

GitHub Actions runs smoke tests and builds on push/PR. **Tagged releases** (`v*`) publish Windows installer and Linux archive. See [.github/workflows/release.yml](.github/workflows/release.yml).

---

## Issuing licenses (owner only)

```bash
python scripts/generate_license.py --holder "Customer" --perpetual
python scripts/generate_license.py --holder "Customer" --days 365
python scripts/generate_license.py --holder "Customer" --machine-id ABCD1234EF567890
```

---

## Software license

Copyright © 2026 **JUNSY**. See [LICENSE](LICENSE) (EULA — restricted commercial use).

Visible source does not imply open source. A valid license key or active trial is required to run the app.
