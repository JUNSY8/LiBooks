import logging
import sys

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtGui import QFont

from paths import setup_logging
from db import init_db
from interfaz import BibliotecaApp
from license_core import LicenseError
from license_manager import ensure_license_valid, get_active_license_info
from license_dialog import prompt_for_license
from trial_manager import is_trial_active, ensure_trial_started, trial_days_remaining, access_status
from i18n import init_i18n, tr
from styles import app_stylesheet, FONT_FAMILY
from icons import app_icon

logger = logging.getLogger(__name__)


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

    QMessageBox.warning(
        None,
        tr("trial.expired_title"),
        tr("trial.expired_message"),
    )

    if prompt_for_license():
        try:
            ensure_license_valid()
            return True
        except LicenseError as e:
            QMessageBox.critical(
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
    logger.info("Starting LiBooks")

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
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
        QMessageBox.critical(
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

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
