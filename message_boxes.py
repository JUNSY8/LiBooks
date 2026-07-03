"""Cuadros de mensaje y botones de dialogo: Enter confirma la accion principal."""

from typing import Optional

from PyQt5.QtWidgets import QMessageBox, QPushButton, QWidget

from i18n import tr
from styles import msgbox_stylesheet, msgbox_danger_button_style


def wire_dialog_buttons(
    cancel_btn: Optional[QPushButton],
    accept_btn: Optional[QPushButton],
) -> None:
    """Enter activa accept_btn; Escape sigue cancelando."""
    if cancel_btn is not None:
        cancel_btn.setAutoDefault(False)
        cancel_btn.setDefault(False)
    if accept_btn is not None:
        accept_btn.setAutoDefault(True)
        accept_btn.setDefault(True)


def disable_button_default(btn: Optional[QPushButton]) -> None:
    if btn is None:
        return
    btn.setAutoDefault(False)
    btn.setDefault(False)


def _styled_box(parent, icon, title, text, informative: str = ""):
    msg = QMessageBox(parent)
    msg.setIcon(icon)
    msg.setWindowTitle(title)
    msg.setText(text)
    if informative:
        msg.setInformativeText(informative)
    msg.setStyleSheet(msgbox_stylesheet())
    return msg


def show_info(parent: Optional[QWidget], title: str, text: str) -> None:
    msg = _styled_box(parent, QMessageBox.Information, title, text)
    ok_btn = msg.addButton(tr("common.ok"), QMessageBox.AcceptRole)
    msg.setDefaultButton(ok_btn)
    msg.exec_()


def show_warning(parent: Optional[QWidget], title: str, text: str) -> None:
    msg = _styled_box(parent, QMessageBox.Warning, title, text)
    ok_btn = msg.addButton(tr("common.ok"), QMessageBox.AcceptRole)
    msg.setDefaultButton(ok_btn)
    msg.exec_()


def show_error(parent: Optional[QWidget], title: str, text: str) -> None:
    msg = _styled_box(parent, QMessageBox.Critical, title, text)
    ok_btn = msg.addButton(tr("common.ok"), QMessageBox.AcceptRole)
    ok_btn.setStyleSheet(msgbox_danger_button_style())
    msg.setDefaultButton(ok_btn)
    msg.exec_()


def confirm(
    parent: Optional[QWidget],
    title: str,
    text: str,
    *,
    informative: str = "",
    yes_text: Optional[str] = None,
    no_text: Optional[str] = None,
    destructive: bool = False,
    icon=QMessageBox.Question,
) -> bool:
    msg = _styled_box(parent, icon, title, text, informative)
    yes_btn = msg.addButton(
        yes_text or tr("common.ok"),
        QMessageBox.YesRole,
    )
    no_btn = msg.addButton(
        no_text or tr("common.cancel"),
        QMessageBox.NoRole,
    )
    msg.setDefaultButton(yes_btn)
    if destructive:
        yes_btn.setStyleSheet(msgbox_danger_button_style())
    disable_button_default(no_btn)
    msg.exec_()
    return msg.clickedButton() == yes_btn
