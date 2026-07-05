"""Utilidades de layout para dialogos modales."""

from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLayout, QSizePolicy, QVBoxLayout, QWidget

DIALOG_PAGE_MARGINS = (28, 24, 28, 20)
DIALOG_FOOTER_MARGINS = (28, 14, 28, 20)


def compact_button_row(*widgets: QWidget, spacing: int = 10) -> QHBoxLayout:
    """Fila de botones alineada a la izquierda, sin estirarse."""
    row = QHBoxLayout()
    row.setSpacing(spacing)
    for widget in widgets:
        widget.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        row.addWidget(widget)
    row.addStretch()
    return row


def compact_action_button(button: QWidget, max_width: int = 320) -> None:
    button.setMaximumWidth(max_width)
    button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)


def attach_footer_bar(outer: QVBoxLayout, footer: QHBoxLayout,
                      margins: tuple = DIALOG_FOOTER_MARGINS) -> None:
    """Barra inferior a ancho completo con separador superior."""
    bar = QFrame()
    bar.setObjectName("dialogFooter")
    wrap = QVBoxLayout(bar)
    wrap.setContentsMargins(0, 0, 0, 0)
    wrap.setSpacing(0)
    line = QFrame()
    line.setObjectName("dialogDivider")
    line.setFrameShape(QFrame.HLine)
    wrap.addWidget(line)
    footer.setContentsMargins(*margins)
    wrap.addLayout(footer)
    outer.addWidget(bar)


def two_column_page(left: QLayout, right: QLayout,
                    margins: tuple = DIALOG_PAGE_MARGINS,
                    spacing: int = 32) -> QWidget:
    """Pagina con dos columnas que reparten el ancho disponible."""
    page = QWidget()
    row = QHBoxLayout(page)
    row.setContentsMargins(*margins)
    row.setSpacing(spacing)
    row.addLayout(left, 1)
    row.addLayout(right, 1)
    return page
