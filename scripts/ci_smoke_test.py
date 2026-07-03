"""Comprobaciones rapidas en CI (sin lanzar la interfaz grafica)."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MODULES = (
    "version",
    "paths",
    "app_settings",
    "license_core",
    "trial_manager",
    "message_boxes",
    "reading_status",
    "sync_crypto",
    "pdf_meta",
    "pdf_ocr",
    "models",
    "crud",
    "book_import",
    "db",
)

TEXT_FILES = (
    "libooks.spec",
)


def check_text_file_encodings() -> None:
    for rel in TEXT_FILES:
        path = ROOT / rel
        if not path.is_file():
            continue
        data = path.read_bytes()
        if b"\x00" in data:
            raise SystemExit(
                f"Invalid encoding in {rel}: null bytes found (save as UTF-8, not UTF-16)"
            )
        if data.startswith(b"\xff\xfe") or data.startswith(b"\xfe\xff"):
            raise SystemExit(f"Invalid encoding in {rel}: UTF-16 BOM detected")


def main() -> int:
    check_text_file_encodings()

    for name in MODULES:
        importlib.import_module(name)

    from db import init_db
    from version import APP_VERSION

    init_db()
    print(f"Smoke test OK - LiBooks {APP_VERSION}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())