"""Onboarding de bienvenida (3 pasos)."""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QWidget, QFrame,
)
from PyQt5.QtCore import Qt

from app_settings import get_setting, set_setting
from icons import app_icon, icon_label, set_button_icon
from i18n import tr
from styles import ACCENT, ACCENT_TEXT, TEXT_SECONDARY


class OnboardingDialog(QDialog):
    """Guía inicial: importar → organizar → leer."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowIcon(app_icon())
        self.setMinimumSize(520, 420)
        self.setModal(True)
        self._step = 0
        self._build_ui()
        self.retranslate_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        header = QHBoxLayout()
        icon_box = QFrame()
        icon_box.setObjectName("dialogIconBox")
        il = QHBoxLayout(icon_box)
        il.setContentsMargins(0, 0, 0, 0)
        il.addWidget(icon_label("app", 28))
        self._title = QLabel()
        self._title.setObjectName("dialogTitle")
        header.addWidget(icon_box)
        header.addWidget(self._title, 1)
        root.addLayout(header)

        self._stack = QStackedWidget()
        self._pages = []
        for key in ("welcome", "organize", "read"):
            page = QWidget()
            lay = QVBoxLayout(page)
            lay.setSpacing(12)
            heading = QLabel()
            heading.setObjectName("dialogTitle")
            heading.setProperty("stepKey", key)
            body = QLabel()
            body.setObjectName("appSubtitle")
            body.setWordWrap(True)
            body.setProperty("stepKey", key)
            lay.addWidget(heading)
            lay.addWidget(body)
            lay.addStretch()
            self._stack.addWidget(page)
            self._pages.append((heading, body))
        root.addWidget(self._stack, 1)

        self._dots = QLabel("● ○ ○")
        self._dots.setAlignment(Qt.AlignCenter)
        self._dots.setObjectName("appSubtitle")
        root.addWidget(self._dots)

        footer = QHBoxLayout()
        self._btn_skip = QPushButton()
        self._btn_skip.setObjectName("ghostButton")
        self._btn_skip.clicked.connect(self._skip)
        footer.addWidget(self._btn_skip)
        footer.addStretch()
        self._btn_back = QPushButton()
        self._btn_back.setObjectName("secondaryButton")
        self._btn_back.clicked.connect(self._back)
        self._btn_next = QPushButton()
        self._btn_next.setObjectName("primaryButton")
        self._btn_next.clicked.connect(self._next)
        footer.addWidget(self._btn_back)
        footer.addWidget(self._btn_next)
        root.addLayout(footer)

        self._update_nav()

    def retranslate_ui(self):
        self.setWindowTitle(tr("onboarding.title"))
        self._title.setText(tr("onboarding.title"))
        steps = [
            ("onboarding.step1_title", "onboarding.step1_body"),
            ("onboarding.step2_title", "onboarding.step2_body"),
            ("onboarding.step3_title", "onboarding.step3_body"),
        ]
        for (heading, body), (tk, bk) in zip(self._pages, steps):
            heading.setText(tr(tk))
            body.setText(tr(bk))
        self._btn_skip.setText(tr("onboarding.skip"))
        self._btn_back.setText(tr("onboarding.back"))
        self._update_nav()

    def _update_nav(self):
        dots = ["○", "○", "○"]
        dots[self._step] = "●"
        self._dots.setText("  ".join(dots))
        self._btn_back.setVisible(self._step > 0)
        if self._step >= 2:
            set_button_icon(self._btn_next, "check", 16, ACCENT_TEXT, tr("onboarding.finish"))
        else:
            set_button_icon(self._btn_next, "check", 16, ACCENT_TEXT, tr("onboarding.next"))

    def _back(self):
        if self._step > 0:
            self._step -= 1
            self._stack.setCurrentIndex(self._step)
            self._update_nav()

    def _next(self):
        if self._step < 2:
            self._step += 1
            self._stack.setCurrentIndex(self._step)
            self._update_nav()
        else:
            self._complete()

    def _skip(self):
        self._complete()

    def _complete(self):
        set_setting("onboarding_completed", True)
        self.accept()


def should_show_onboarding() -> bool:
    return not get_setting("onboarding_completed", False)


def show_onboarding_if_needed(parent) -> None:
    if should_show_onboarding():
        OnboardingDialog(parent).exec_()
