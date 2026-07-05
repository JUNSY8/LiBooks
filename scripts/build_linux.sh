#!/usr/bin/env bash
# Empaqueta LiBooks para Linux (ejecutable unico) con PyInstaller.
# Uso: bash scripts/build_linux.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "Este script debe ejecutarse en Linux." >&2
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
  echo "No se encontro Python 3.9-3.13." >&2
  return 1
}

PYTHON_BIN="$(resolve_python)"
ARCH="$(uname -m)"
echo "Arquitectura de build: $ARCH"
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

echo "Verificando PyQt5..."
"$PYTHON" -c "from PyQt5.QtWidgets import QApplication; print('PyQt5 OK')"

if [[ -f "assets/icons/app_icon_512.png" ]]; then
  echo "Generando iconos (render nativo por tamano)..."
  "$PYTHON" scripts/generate_app_icons.py
fi

echo "Compilando LiBooks..."
"$PYTHON" -m PyInstaller libooks.spec --noconfirm

EXE="$ROOT/dist/LiBooks"
if [[ -f "$EXE" ]]; then
  chmod +x "$EXE"
  echo ""
  echo "Listo: $EXE"
else
  echo "No se genero dist/LiBooks." >&2
  exit 1
fi
