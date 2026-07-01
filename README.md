# LiBooks

A desktop application for reading and managing a **personal library of PDF books** in a comfortable, intuitive way: import your PDFs, organize them by author, genre, and collections, and read them in a built-in viewer with automatic progress tracking, bookmarks, and notes.

Built with **Python**, a **PyQt5** graphical interface, a **PyMuPDF**-based viewer, and local **SQLite** storage via **SQLAlchemy** and **Alembic**.

## Features

- Import PDF books into the library (copied to the user's data directory).
- Register and edit title, author, and genre for each book.
- Organize books into **collections** (many-to-many relationship).
- Built-in **PDF viewer** with lazy rendering, zoom, bookmarks, and notes.
- Automatic **reading progress** saving.
- **License activation** with cryptographically signed keys (RSA).

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
├── main.py              # Entry point: logging, license, DB, UI
├── license_core.py      # Cryptographic license verification
├── license_manager.py   # License storage and lifecycle
├── license_dialog.py    # Activation dialog (PyQt5)
├── interfaz.py          # Main window
├── pdf_viewer.py        # PDF viewer
├── db.py / models.py / crud.py
├── paths.py
├── alembic/             # Database migrations
├── keys/                # Public key (private key stays outside the repo)
└── scripts/             # Owner tools (key generation)
```

## Requirements

- Python 3.9 or later
- Dependencies listed in `requirements.txt`

## Installation (developers / owner)

```bash
git clone <repository-url>
cd LiBooks
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

### Initial key setup (owner only, once)

```bash
python scripts/generate_keypair.py
# Commit keys/license_public.pem (NOT the private key)
python scripts/generate_license.py --holder "JUNSY" --perpetual
```

Activate the generated license when running `python main.py`.

## Usage

```bash
python main.py
```

On first launch without a valid license, the activation dialog is shown. The key is saved in the user's data directory.

## Database migrations (Alembic)

```bash
# Apply pending migrations (also runs automatically on startup)
alembic upgrade head

# Create a new migration after changing models.py
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

- **Windows:** `%LOCALAPPDATA%\LiBooks\`
- **macOS:** `~/Library/Application Support/LiBooks/`
- **Linux:** `~/.local/share/LiBooks/`

Contains: `libooks.db`, `libros/`, `license.key`, `libooks.log`.

## Packaging

```bash
pip install pyinstaller
pyinstaller libooks.spec
```

Includes `keys/license_public.pem` in the executable. The private key is **never** packaged.

## Software license

Copyright (c) 2026 **JUNSY**. See [LICENSE](LICENSE) (EULA — restricted commercial use).

Visible source code does not imply an open-source license. A valid license key is required to use the program.
