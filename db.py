"""Configuración de la base de datos.

Usa SQLite embebido (sin servidor) almacenado en el directorio de datos del
usuario. Las migraciones de esquema se gestionan con Alembic.
"""

import logging
import os

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, declarative_base

from paths import DB_PATH, PDF_FOLDER, resource_path  # noqa: F401  (PDF_FOLDER se re-exporta)

logger = logging.getLogger(__name__)

DATABASE_URL = f"sqlite:///{DB_PATH}"

# check_same_thread=False permite compartir la conexión con los callbacks de Qt.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()

_ALEMBIC_INI = resource_path("alembic.ini")
_ALEMBIC_SCRIPTS = resource_path("alembic")


def _alembic_config() -> Config:
    if os.path.isfile(_ALEMBIC_INI):
        cfg = Config(_ALEMBIC_INI)
    else:
        cfg = Config()
    cfg.set_main_option("script_location", _ALEMBIC_SCRIPTS)
    cfg.set_main_option("sqlalchemy.url", DATABASE_URL)
    return cfg


def init_db() -> None:
    """Aplica migraciones pendientes. Compatible con instalaciones previas."""
    import models  # noqa: F401  (registra los modelos en Base.metadata)

    cfg = _alembic_config()
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    # Instalaciones antiguas creadas con create_all(): marcar como migradas.
    has_app_tables = bool(existing_tables & {"libro", "autor", "genero"})
    has_alembic = "alembic_version" in existing_tables

    if has_app_tables and not has_alembic:
        logger.info("Base de datos existente detectada; aplicando stamp inicial")
        command.stamp(cfg, "head")
    else:
        command.upgrade(cfg, "head")

    logger.info("Base de datos lista en %s", DB_PATH)
