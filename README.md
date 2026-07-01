# LiBooks

A desktop application for reading and managing a **personal library of PDF books**: import PDFs, organize them by author, genre, tags, and collections, and read them in a built-in viewer with progress tracking, bookmarks, highlights, and notes.

Built with **Python**, **PyQt5**, **PyMuPDF**, and local **SQLite** storage via **SQLAlchemy** and **Alembic**. Available in **English** and **Spanish**.

## Features

### Library

- Grid and list views with cover thumbnails (extracted from PDFs).
- Drag & drop import, import folder, and duplicate detection (file hash).
- Collections (many-to-many), tags, sort and filter options.
- **Continue reading** card for the last opened book.
- Encrypted **folder sync** (AES-GCM) and ZIP **library backup**.

### PDF reader

- Lazy page rendering, zoom, full-text search, and reading mode.
- Bookmarks, text highlights, and anchored notes.
- Sidebar with outline, bookmarks, and annotations.
- **OCR** for scanned pages (Tesseract + PyMuPDF).
- Export notes to Markdown / plain text.

### Statistics & settings

- Reading stats dashboard (books read, time, progress).
- App settings: language, library layout, sync folder, OCR path.

### Licensing & trial

- **14-day trial** on first launch; RSA license activation afterward.
- Onboarding wizard for new users.
- Optional update check against `release/version.json`.

## Licensing model (public repo + protected commercial use)

The source code may be **public on GitHub** for transparency, but **using LiBooks requires a valid license** issued by the software owner.

| Layer | What it protects |
|-------|------------------|
| **Legal (EULA)** | Prohibits use, copying, and redistribution without a license. See [LICENSE](LICENSE). |
| **Technical (RSA)** | The app verifies a digital signature on every launch. Without the private key (held only by the owner), valid licenses cannot be generated. |
| **Practical** | Bypassing verification requires modifying the code or executable — more effort than using the product legitimately. |

> **Honest note:** no desktop software is 100% tamper-proof against skilled attackers. The goal is to deter casual unauthorized use and legally support your commercial product.

## Project structure

```
LiBooks/
├── main.py                 # Entry point: logging, license, DB, UI
├── interfaz.py             # Main window and navigation
├── library_view.py         # Library grid/list, import, filters
├── pdf_viewer.py           # PDF reader shell
├── pdf_page.py / pdf_sidebar.py / pdf_annotations.py
├── stats_view.py           # Statistics panel
├── sync_engine.py          # Encrypted sync
├── trial_manager.py        # Trial period
├── onboarding_dialog.py    # First-run wizard
├── db.py / models.py / crud.py
├── alembic/                # Database migrations
├── locales/                # en.json, es.json
├── assets/icons/           # App icon (source: app_icon_512.png)
├── keys/                   # Public key (private key stays outside the repo)
├── installer/              # Inno Setup script
├── release/                # version.json for update checks
└── scripts/                # Build, signing, and owner tools
```

## Requirements

- Python 3.9–3.13 (PyQt5 5.15.9 has pre-built wheels up to 3.13; 3.14+ is not supported yet)
- Dependencies in `requirements.txt`
- **Optional:** [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) for scanned PDF text search
- **Windows packaging:** [Inno Setup 6](https://jrsoftware.org/isdl.php), [Windows SDK](https://developer.microsoft.com/windows/downloads/windows-sdk/) (for signing)
- **macOS packaging:** Xcode Command Line Tools (`iconutil`, `codesign`); build on a Mac

## Installation (developers)

```bash
git clone <repository-url>
cd LiBooks
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

### Initial key setup (owner only, once)

```bash
python scripts/generate_keypair.py
# Commit keys/license_public.pem (NOT the private key)
python scripts/generate_license.py --holder "JUNSY" --perpetual
```

Activate the generated license when running `python main.py`. See [keys/README.md](keys/README.md).

## Usage

```bash
python main.py
```

On first launch without a valid license, a **14-day trial** starts automatically. After that, the activation dialog is shown. The license key is stored in the user's data directory.

## Database migrations (Alembic)

Migrations run automatically on startup. For development:

```bash
alembic upgrade head

# After changing models.py
alembic revision --autogenerate -m "description of change"
alembic upgrade head
```

## Issuing licenses to customers (owner only)

```bash
# Perpetual license
python scripts/generate_license.py --holder "Customer" --email "customer@mail.com" --perpetual

# 365-day license
python scripts/generate_license.py --holder "Customer" --days 365

# Bound to the customer's machine (customer sends their ID from the activation dialog)
python scripts/generate_license.py --holder "Customer" --machine-id ABCD1234EF567890
```

## User data location

| OS | Path |
|----|------|
| **Windows** | `%LOCALAPPDATA%\LiBooks\` |
| **macOS** | `~/Library/Application Support/LiBooks/` |
| **Linux** | `~/.local/share/LiBooks/` |

Contains: `libooks.db`, `libros/` (imported PDFs), `license.key`, `libooks.log`, and app settings.

## Packaging

### Windows executable only

```powershell
.\scripts\build_windows.ps1
```

Uses an isolated `.build-venv`, installs dependencies + PyInstaller, regenerates icons from `assets/icons/app_icon_512.png`, and outputs `dist\LiBooks.exe`.

### Windows signed installer

```powershell
$env:LIBOOKS_SIGN_PFX = "C:\path\to\codesign.pfx"
$env:LIBOOKS_SIGN_PASSWORD = "your-password"
.\scripts\build_installer.ps1
```

Output: `dist\LiBooks-Setup-{version}.exe`.

For local testing without a commercial certificate:

```powershell
.\scripts\build_installer.ps1 -SkipSign
```

For a self-signed dev certificate:

```powershell
.\scripts\create_self_signed_cert.ps1
# set LIBOOKS_SIGN_* as printed, then:
.\scripts\build_installer.ps1
```

Full signing and CI notes: [installer/README.md](installer/README.md).

The bundle includes `keys/license_public.pem`, Alembic migrations, locales, and assets. The private signing key and license private key are **never** packaged.

### macOS app bundle

Build on a Mac (requires Python 3.9+ and Xcode Command Line Tools):

```bash
chmod +x scripts/build_macos.sh
./scripts/build_macos.sh
```

Output: `dist/LiBooks.app`. User data goes to `~/Library/Application Support/LiBooks/`.

For Tesseract OCR on macOS:

```bash
brew install tesseract tesseract-lang
```

Signing, notarization, and DMG notes: [installer/README_macos.md](installer/README_macos.md).

### Continuous integration

GitHub Actions builds on every push/PR to `main` (Windows `.exe`, macOS `.app`) and publishes release assets when you push a tag like `v1.0.1`. See [installer/README.md](installer/README.md#cicd-github-actions).

### App icon

Replace `assets/icons/app_icon_512.png` and rebuild. Icon sizes, `app_icon.ico` (Windows), and `app_icon.icns` (macOS) are generated by `scripts/generate_app_icons.py`.

## Software license

Copyright (c) 2026 **JUNSY**. See [LICENSE](LICENSE) (EULA — restricted commercial use).

Visible source code does not imply an open-source license. A valid license key (or active trial) is required to use the program.
