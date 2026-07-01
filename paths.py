"""Rutas de la aplicación y configuración de logging.

Centraliza la resolución de rutas para que la aplicación funcione tanto
ejecutándose desde el código fuente como empaquetada con PyInstaller, y
almacena los datos del usuario (base de datos, PDFs y logs) en el directorio
de datos del sistema operativo en lugar de junto al ejecutable.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

APP_NAME = "LiBooks"


def resource_path(relative_path: str) -> str:
    """Devuelve la ruta absoluta a un recurso empaquetado (imágenes, iconos).

    Compatible con PyInstaller: cuando la app está empaquetada los recursos se
    extraen en ``sys._MEIPASS``; en desarrollo se resuelven junto a este módulo.
    """
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def user_data_dir() -> str:
    """Directorio de datos del usuario, específico por sistema operativo."""
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")

    path = os.path.join(base, APP_NAME)
    os.makedirs(path, exist_ok=True)
    return path


# Carpeta donde se copian los PDFs importados.
PDF_FOLDER = os.path.join(user_data_dir(), "libros")
os.makedirs(PDF_FOLDER, exist_ok=True)

# Ubicación del archivo de base de datos SQLite.
DB_PATH = os.path.join(user_data_dir(), "libooks.db")

# Archivo de log.
LOG_FILE = os.path.join(user_data_dir(), "libooks.log")


def setup_logging(level: int = logging.INFO) -> None:
    """Configura el logging global a archivo (con rotación) y consola.

    Sustituye a los ``print`` dispersos: en una app empaquetada no hay consola
    visible, por lo que los errores deben quedar registrados en disco.
    """
    root = logging.getLogger()
    if root.handlers:  # Evitar configurar dos veces.
        return

    root.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root.addHandler(stream_handler)
