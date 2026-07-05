import logging
import sys
import traceback

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont

from paths import setup_logging, LOG_FILE
from db import init_db
from interfaz import BibliotecaApp
from license_core import LicenseError
from license_manager import ensure_license_valid, get_active_license_info
from license_dialog import prompt_for_license
from trial_manager import is_trial_active, ensure_trial_started, trial_days_remaining
from i18n import init_i18n, tr
from message_boxes import show_warning, show_error
from color_theme import load_active_theme
from styles import app_stylesheet, FONT_FAMILY
from icons import app_icon

logger = logging.getLogger(__name__)


def _configure_platform_before_app() -> None:
    """Atributos Qt que deben fijarse antes de crear QApplication."""
    if sys.platform == "darwin":
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)


def _configure_platform(app: QApplication) -> None:
    """Ajustes por sistema operativo tras crear QApplication."""
    if sys.platform == "darwin":
        app.setAttribute(Qt.AA_DontShowIconsInMenus, False)


def _install_exception_hook() -> None:
    """Registra errores no capturados en log y muestra un aviso al usuario."""
    def _handle(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        logger.critical(
            "Excepción no capturada:\n%s",
            "".join(traceback.format_exception(exc_type, exc_value, exc_tb)),
        )
        for handler in logging.getLogger().handlers:
            try:
                handler.flush()
            except Exception:
                pass
        try:
            show_error(
                None,
                tr("main.crash_title"),
                tr("main.crash_message", log=LOG_FILE),
            )
        except Exception:
            pass
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = _handle


def _require_valid_license(app: QApplication) -> bool:
    """Comprueba licencia activa o período de prueba."""
    try:
        payload = ensure_license_valid()
        logger.info("Licencia válida: %s", payload.get("holder", "?"))
        return True
    except LicenseError:
        logger.info("Sin licencia de pago; comprobando trial")

    if not get_active_license_info():
        ensure_trial_started()

    if is_trial_active():
        logger.info("Trial activo: %d días restantes", trial_days_remaining())
        return True

    show_warning(
        None,
        tr("trial.expired_title"),
        tr("trial.expired_message"),
    )

    if prompt_for_license():
        try:
            ensure_license_valid()
            return True
        except LicenseError as e:
            show_error(
                None,
                tr("license.invalid_title"),
                tr("license.invalid_startup", error=e),
            )
    return False


def main():
    """
    Punto de entrada principal de la aplicación.
    Configura logging, verifica licencia, inicializa la BD y muestra la ventana.
    """
    setup_logging()
    init_i18n()
    logger.info("Starting LiBooks on %s", sys.platform)

    _configure_platform_before_app()
    app = QApplication(sys.argv)
    _configure_platform(app)
    _install_exception_hook()
    app.setStyle("Fusion")
    load_active_theme()
    app.setStyleSheet(app_stylesheet())
    app.setFont(QFont(FONT_FAMILY.split(",")[0].strip(), 10))
    app.setWindowIcon(app_icon())

    if not _require_valid_license(app):
        logger.warning("Salida: licencia no activada")
        sys.exit(1)

    try:
        init_db()
    except Exception as e:
        logger.exception("No se pudo inicializar la base de datos: %s", e)
        show_error(
            None,
            tr("main.db_error_title"),
            tr("main.db_error", error=e),
        )
        sys.exit(1)

    from sync_engine import sync_if_enabled
    sync_if_enabled(pull_only=True)

    window = BibliotecaApp()
    window.show()

    from onboarding_dialog import show_onboarding_if_needed
    show_onboarding_if_needed(window)

    from product_tour import schedule_section_tour
    schedule_section_tour(window, "navigation", delay_ms=900)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
