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
    "sync_crypto",
    "pdf_meta",
    "pdf_ocr",
    "models",
    "crud",
    "book_import",
    "db",
)


def main() -> int:
    for name in MODULES:
        importlib.import_module(name)

    from db import init_db
    from version import APP_VERSION

    init_db()
    print(f"Smoke test OK - LiBooks {APP_VERSION}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())