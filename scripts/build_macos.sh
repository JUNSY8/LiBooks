#!/usr/bin/env bash
# Empaqueta LiBooks para macOS (.app) con PyInstaller.
# Uso: bash scripts/build_macos.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Este script debe ejecutarse en macOS." >&2
  exit 1
fi

resolve_python() {
  if [[ -n "${LIBOOKS_PYTHON:-}" ]]; then
    echo "$LIBOOKS_PYTHON"
    return 0
  fi
  local candidate
  for candidate in python3.11 python3.12 python3.13 python3.10 python3.9 python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
      if "$candidate" -c 'import sys; sys.exit(0 if (3, 9) <= sys.version_info[:2] <= (3, 13) else 1)'; then
        echo "$candidate"
        return 0
      fi
    fi
  done
  echo "No se encontro Python 3.9-3.13 (PyQt5 5.15.9 no soporta 3.14+)." >&2
  return 1
}

PYTHON_BIN="$(resolve_python)"
echo "Usando Python: $PYTHON_BIN ($("$PYTHON_BIN" --version))"

VENV_DIR="$ROOT/.build-venv"
PYTHON="$VENV_DIR/bin/python"
PIP="$VENV_DIR/bin/pip"

if [[ ! -x "$PYTHON" ]]; then
  echo "Creando entorno de build (.build-venv)..."
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

echo "Instalando dependencias en .build-venv..."
"$PYTHON" -m pip install --upgrade pip --quiet
"$PIP" install -r requirements.txt pyinstaller pillow

if [[ -f "assets/icons/app_icon_512.png" ]]; then
  echo "Actualizando iconos desde app_icon_512.png..."
  "$PYTHON" scripts/generate_app_icons.py
fi

if [[ ! -f "assets/icons/app_icon.icns" ]]; then
  echo "No se encontro app_icon.icns. Genera iconos con generate_app_icons.py en macOS." >&2
  exit 1
fi

echo "Compilando LiBooks.app..."
"$PYTHON" -m PyInstaller libooks_mac.spec --noconfirm

APP="$ROOT/dist/LiBooks.app"
if [[ -d "$APP" ]]; then
  echo ""
  echo "Listo: $APP"
  echo "Opcional - firmar y notarizar: ver installer/README_macos.md"
else
  echo "No se genero LiBooks.app." >&2
  exit 1
fi