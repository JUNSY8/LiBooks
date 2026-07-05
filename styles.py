"""Tema visual LiBooks — paleta y hojas de estilo QSS."""

# Paleta
BG_MAIN = "#121e24"
BG_SECONDARY = "#1e2d36"
BG_INPUT = "#1a2a33"
BG_INPUT_ALT = "#243436"
BG_SIDEBAR = "#0f1a20"
BG_TAG = "#065f46"
BG_TAG_HOVER = "#087a5a"

ACCENT = "#4adea9"
ACCENT_HOVER = "#34d399"
ACCENT_TEXT = "#0f172a"

TEXT_PRIMARY = "#ffffff"
TEXT_SECONDARY = "#9ca3af"
TEXT_LABEL = "#94a3b8"

DANGER = "#f87171"
DANGER_BORDER = "#ef4444"
DANGER_HOVER = "#fca5a5"

BORDER_SUBTLE = "#2a3f4a"
RADIUS = "10px"
RADIUS_SM = "8px"
RADIUS_LG = "12px"

TITLE_BAR_ICON = "#a8b4be"
TITLE_BAR_ICON_HOVER = "#e8eef2"
TITLE_BAR_CLOSE = "#e81123"
TITLE_BAR_CLOSE_PRESSED = "#bf0f1d"

STATUS_UNREAD_BG = "#374151"
STATUS_UNREAD_TEXT = "#d1d5db"
STATUS_UNREAD_HOVER = "#3f4b5e"
STATUS_READING_BG = "#1e3a5f"
STATUS_READING_TEXT = "#93c5fd"
STATUS_READING_HOVER = "#214068"
STATUS_COMPLETED_BG = "#064e3b"
STATUS_COMPLETED_TEXT = "#6ee7b7"
STATUS_COMPLETED_HOVER = "#075641"
STATUS_PAUSED_BG = "#78350f"
STATUS_PAUSED_TEXT = "#fcd34d"
STATUS_PAUSED_HOVER = "#843a10"
STATUS_ABANDONED_BG = "#4c1d24"
STATUS_ABANDONED_TEXT = "#fca5a5"
STATUS_ABANDONED_HOVER = "#542028"

FONT_FAMILY = "Segoe UI, Arial, sans-serif"


def _hex_rgb(hex_color: str) -> tuple:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def rgba(hex_color: str, alpha: float) -> str:
    r, g, b = _hex_rgb(hex_color)
    return f"rgba({r}, {g}, {b}, {alpha})"


def accent_rgba(alpha: float) -> str:
    return rgba(ACCENT, alpha)


def danger_rgba(alpha: float) -> str:
    return rgba(DANGER_BORDER, alpha)


def bg_secondary_rgba(alpha: float) -> str:
    return rgba(BG_SECONDARY, alpha)


def sidebar_rgba(alpha: float) -> str:
    return rgba(BG_SIDEBAR, alpha)


def apply_color_palette(palette: dict) -> None:
    """Actualiza constantes de color desde un dict de tokens."""
    from color_theme import COLOR_TOKEN_ATTRS, normalize_hex

    for key, attr in COLOR_TOKEN_ATTRS.items():
        if key in palette:
            globals()[attr] = normalize_hex(palette[key])


def app_stylesheet() -> str:
    a06 = accent_rgba(0.06)
    a08 = accent_rgba(0.08)
    a10 = accent_rgba(0.10)
    a12 = accent_rgba(0.12)
    a15 = accent_rgba(0.15)
    a18 = accent_rgba(0.18)
    a28 = accent_rgba(0.28)
    a45 = accent_rgba(0.45)
    d12 = danger_rgba(0.12)
    d15 = danger_rgba(0.15)
    nav_hover = bg_secondary_rgba(0.6)
    drop_overlay = sidebar_rgba(0.92)
    return f"""
    * {{
        font-family: {FONT_FAMILY};
    }}

    QToolTip {{
        background-color: {BG_SECONDARY};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER_SUBTLE};
        border-radius: {RADIUS_SM};
        padding: 6px 10px;
        font-size: 12px;
        font-weight: 500;
    }}

    QWidget[tourHighlight="true"],
    QFrame[tourHighlight="true"],
    QPushButton[tourHighlight="true"],
    QLineEdit[tourHighlight="true"],
    QComboBox[tourHighlight="true"],
    QListWidget[tourHighlight="true"],
    QScrollArea[tourHighlight="true"] {{
        border: 2px solid {ACCENT};
        border-radius: {RADIUS_SM};
        background-color: {a06};
    }}

    QFrame#tourCallout {{
        background-color: {BG_SECONDARY};
        border: 1px solid {BORDER_SUBTLE};
        border-left: 4px solid {ACCENT};
        border-radius: {RADIUS_LG};
        max-width: 360px;
    }}

    QFrame#tourCallout QLabel {{
        background: transparent;
        border: none;
    }}

    QProgressBar#tourProgress {{
        background-color: {BG_INPUT};
        border: none;
        border-radius: 3px;
        max-height: 4px;
        min-height: 4px;
    }}
    QProgressBar#tourProgress::chunk {{
        background-color: {ACCENT};
        border-radius: 3px;
    }}

    QLabel#tourStepIndicator {{
        color: {ACCENT};
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.4px;
        text-transform: uppercase;
    }}

    QLabel#tourTitle {{
        color: {TEXT_PRIMARY};
        font-size: 15px;
        font-weight: 600;
    }}

    QLabel#tourBody {{
        color: {TEXT_SECONDARY};
        font-size: 13px;
        line-height: 1.4;
    }}

    QWidget {{
        background-color: {BG_MAIN};
        color: {TEXT_PRIMARY};
    }}

    /* ── Barra de título personalizada ── */
    QFrame#titleBar {{
        background-color: {BG_SIDEBAR};
        border: none;
        border-bottom: 1px solid {BORDER_SUBTLE};
    }}

    QLabel#titleBarLabel {{
        color: {TEXT_PRIMARY};
        font-size: 13px;
        font-weight: 600;
        background: transparent;
    }}

    QPushButton#titleBarButton {{
        background-color: transparent;
        border: none;
        border-radius: 0;
        padding: 0;
    }}
    QPushButton#titleBarButton:hover {{
        background-color: rgba(255, 255, 255, 0.08);
    }}
    QPushButton#titleBarButton:pressed {{
        background-color: rgba(255, 255, 255, 0.04);
    }}

    QPushButton#titleBarClose {{
        background-color: transparent;
        border: none;
        border-radius: 0;
        padding: 0;
    }}
    QPushButton#titleBarClose:hover {{
        background-color: {TITLE_BAR_CLOSE};
    }}
    QPushButton#titleBarClose:pressed {{
        background-color: {TITLE_BAR_CLOSE_PRESSED};
    }}

    /* ── Sidebar ── */
    QFrame#sidebar {{
        background-color: {BG_SIDEBAR};
        border: none;
    }}

    QLabel#appTitle {{
        color: {TEXT_PRIMARY};
        font-size: 18px;
        font-weight: bold;
        padding: 4px 0;
    }}

    QLabel#appSubtitle {{
        color: {TEXT_SECONDARY};
        font-size: 11px;
    }}

    QPushButton#navButton {{
        background-color: transparent;
        color: {TEXT_SECONDARY};
        border: none;
        border-radius: {RADIUS};
        padding: 12px 16px;
        text-align: left;
        font-size: 14px;
        font-weight: 500;
    }}
    QPushButton#navButton:hover {{
        background-color: {nav_hover};
        color: {TEXT_PRIMARY};
    }}
    QPushButton#navButton[active="true"] {{
        background-color: {BG_SECONDARY};
        color: {TEXT_PRIMARY};
    }}

    QFrame#navItem {{
        background-color: transparent;
        border: none;
        border-radius: {RADIUS};
    }}
    QFrame#navItem:hover {{
        background-color: {nav_hover};
    }}
    QFrame#navItem[active="true"] {{
        background-color: {BG_SECONDARY};
    }}
    QLabel#navItemLabel {{
        color: {TEXT_SECONDARY};
        font-size: 14px;
        font-weight: 500;
        background: transparent;
    }}
    QFrame#navItem[active="true"] QLabel#navItemLabel {{
        color: {TEXT_PRIMARY};
    }}

    QLabel#navBadge {{
        background-color: {BG_SECONDARY};
        color: {TEXT_SECONDARY};
        border-radius: 10px;
        padding: 2px 8px;
        font-size: 12px;
        min-width: 20px;
    }}

    QFrame#sidebarDivider {{
        background-color: {BORDER_SUBTLE};
        max-height: 1px;
    }}

    /* ── Área principal ── */
    QFrame#mainContent {{
        background-color: {BG_MAIN};
    }}

    QLineEdit#searchBar {{
        background-color: {BG_INPUT};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER_SUBTLE};
        border-radius: {RADIUS_LG};
        padding: 12px 20px;
        font-size: 14px;
        min-height: 20px;
    }}
    QLineEdit#searchBar:focus {{
        border: 1px solid {ACCENT};
    }}
    QLineEdit#searchBar::placeholder {{
        color: {TEXT_SECONDARY};
    }}

    QPushButton#primaryButton {{
        background-color: {ACCENT};
        color: {ACCENT_TEXT};
        border: none;
        border-radius: {RADIUS};
        padding: 12px 24px;
        font-size: 14px;
        font-weight: 600;
    }}
    QPushButton#primaryButton:hover {{
        background-color: {ACCENT_HOVER};
    }}
    QPushButton#primaryButton:default {{
        outline: 2px solid rgba(255, 255, 255, 0.35);
        outline-offset: 1px;
    }}

    QPushButton#secondaryButton {{
        background-color: {BG_INPUT};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER_SUBTLE};
        border-radius: {RADIUS_SM};
        padding: 10px 20px;
        font-size: 14px;
    }}
    QPushButton#secondaryButton:hover {{
        background-color: {BG_SECONDARY};
        border-color: {TEXT_SECONDARY};
    }}

    QPushButton#ghostButton {{
        background-color: transparent;
        color: {ACCENT};
        border: 1px solid {ACCENT};
        border-radius: {RADIUS};
        padding: 8px 16px;
        font-size: 13px;
    }}
    QPushButton#ghostButton:hover {{
        background-color: {a10};
    }}

    QPushButton#dangerButton {{
        background-color: transparent;
        color: {DANGER};
        border: 1px solid {DANGER_BORDER};
        border-radius: {RADIUS_SM};
        padding: 10px 20px;
        font-size: 14px;
    }}
    QPushButton#dangerButton:hover {{
        background-color: {d12};
    }}

    QPushButton#iconButton {{
        background-color: {BG_INPUT};
        color: {TEXT_SECONDARY};
        border: 1px solid {BORDER_SUBTLE};
        border-radius: {RADIUS_SM};
        padding: 6px;
        min-width: 36px;
        max-width: 36px;
        min-height: 36px;
        max-height: 36px;
        font-size: 14px;
    }}
    QPushButton#iconButton:hover {{
        background-color: {BG_SECONDARY};
        color: {TEXT_PRIMARY};
    }}
    QPushButton#iconButtonDanger {{
        background-color: {BG_INPUT};
        color: {DANGER};
        border: 1px solid {BORDER_SUBTLE};
        border-radius: {RADIUS_SM};
        padding: 6px;
        min-width: 36px;
        max-width: 36px;
        min-height: 36px;
        max-height: 36px;
        font-size: 14px;
    }}
    QPushButton#iconButtonDanger:hover {{
        background-color: {d15};
        border-color: {DANGER_BORDER};
    }}

    QPushButton#addCollectionBtn {{
        background-color: transparent;
        color: {ACCENT};
        border: 1px solid {ACCENT};
        border-radius: 14px;
        padding: 2px 10px;
        font-size: 16px;
        font-weight: bold;
        min-width: 28px;
        max-width: 28px;
        min-height: 28px;
        max-height: 28px;
    }}
    QPushButton#addCollectionBtn:hover {{
        background-color: {a15};
    }}

    QLabel#emptyState {{
        color: {TEXT_SECONDARY};
        font-size: 13px;
        padding: 40px;
    }}

    /* ── Tarjetas de libro ── */
    QFrame#bookCard {{
        background-color: {BG_SECONDARY};
        border: none;
        border-radius: {RADIUS_LG};
    }}

    QLabel#bookTitle {{
        color: {TEXT_PRIMARY};
        font-size: 15px;
        font-weight: 600;
        background: transparent;
    }}

    QLabel#bookAuthor {{
        color: {TEXT_SECONDARY};
        font-size: 13px;
        background: transparent;
    }}

    QFrame#bookIconBox {{
        background-color: {BG_INPUT};
        border-radius: {RADIUS_SM};
        min-width: 48px;
        max-width: 48px;
        min-height: 48px;
        max-height: 48px;
    }}

    QLabel#bookCover {{
        background-color: {BG_INPUT};
        border-radius: {RADIUS_SM};
        border: 1px solid {BORDER_SUBTLE};
    }}

    QFrame#bookGridCard {{
        background-color: {BG_SECONDARY};
        border: 1px solid {BORDER_SUBTLE};
        border-radius: {RADIUS_LG};
    }}
    QFrame#bookGridCard:hover {{
        border-color: {ACCENT};
    }}

    QLabel#bookGridCover {{
        background-color: {BG_INPUT};
        border-radius: {RADIUS_SM};
        border: 1px solid {BORDER_SUBTLE};
        padding: 0px;
        margin: 0px;
    }}

    QLabel#bookGridTitle {{
        color: {TEXT_PRIMARY};
        font-size: 13px;
        font-weight: 600;
        background: transparent;
    }}

    QFrame#continueReadingCard {{
        background-color: {BG_SECONDARY};
        border: 1px solid {BORDER_SUBTLE};
        border-radius: {RADIUS_LG};
        max-height: 132px;
        min-height: 132px;
    }}
    QFrame#continueReadingCard:hover {{
        border-color: {ACCENT};
    }}

    QLabel#continueReadingLabel {{
        color: {ACCENT};
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
        background: transparent;
    }}

    QLabel#continueReadingTitle {{
        color: {TEXT_PRIMARY};
        font-size: 18px;
        font-weight: 600;
        background: transparent;
    }}

    QProgressBar#readingProgress {{
        background-color: {BG_INPUT};
        border: none;
        border-radius: 3px;
        max-height: 6px;
        min-height: 6px;
    }}
    QProgressBar#readingProgress::chunk {{
        background-color: {ACCENT};
        border-radius: 3px;
    }}

    QLabel#continueReadingProgress {{
        color: {TEXT_SECONDARY};
        font-size: 12px;
        background: transparent;
        padding-top: 2px;
    }}

    QPushButton#viewToggleBtn {{
        background-color: transparent;
        border: 1px solid {BORDER_SUBTLE};
        border-radius: {RADIUS_SM};
        padding: 6px;
        min-width: 36px;
        max-width: 36px;
        min-height: 36px;
        max-height: 36px;
    }}
    QPushButton#viewToggleBtn:hover {{
        border-color: {ACCENT};
        background-color: {a08};
    }}
    QPushButton#viewToggleBtn[active="true"] {{
        border-color: {ACCENT};
        background-color: {a15};
    }}

    QScrollArea#bookGridScroll {{
        background-color: transparent;
        border: none;
    }}

    QLabel#dropOverlay {{
        background-color: {drop_overlay};
        border: 2px dashed {ACCENT};
        border-radius: {RADIUS_LG};
        color: {ACCENT};
        font-size: 16px;
        font-weight: 600;
    }}

    /* ── Lista de libros ── */
    QListWidget#bookList {{
        background-color: transparent;
        border: none;
        outline: none;
    }}
    QListWidget#bookList::item {{
        background-color: transparent;
        border: none;
        padding: 0;
        margin-bottom: 8px;
    }}
    QListWidget#bookList::item:selected {{
        background-color: transparent;
    }}

    /* ── Colecciones en sidebar ── */
    QScrollArea#collectionsScroll {{
        border: none;
        background: transparent;
    }}
    QScrollArea#collectionsScroll > QWidget > QWidget {{
        background: transparent;
    }}

    QFrame#collectionRow {{
        background-color: transparent;
        border: none;
        border-radius: {RADIUS_SM};
        min-height: 52px;
        max-height: 52px;
    }}
    QFrame#collectionRow:hover {{
        background-color: {nav_hover};
    }}
    QFrame#collectionRow[active="true"] {{
        background-color: {BG_SECONDARY};
    }}

    QFrame#collectionCoverWrap {{
        background: transparent;
        border: none;
    }}

    QLabel#collectionCoverThumb {{
        background-color: {BG_INPUT};
        border-radius: 4px;
        border: 1px solid {BORDER_SUBTLE};
    }}

    QLabel#collectionName {{
        color: {TEXT_PRIMARY};
        font-size: 13px;
        font-weight: 500;
        background: transparent;
        min-width: 0;
    }}
    QFrame#collectionRow[active="true"] QLabel#collectionName {{
        color: {TEXT_PRIMARY};
    }}

    QLabel#collectionMeta {{
        color: {TEXT_SECONDARY};
        font-size: 11px;
        background: transparent;
        min-width: 0;
    }}

    QLabel#collectionEmpty {{
        color: {TEXT_SECONDARY};
        font-size: 12px;
        padding: 8px 12px;
        background: transparent;
    }}

    QPushButton#collectionEdit {{
        background-color: transparent;
        color: {TEXT_SECONDARY};
        border: none;
        border-radius: 14px;
        min-width: 28px;
        max-width: 28px;
        min-height: 28px;
        max-height: 28px;
    }}
    QPushButton#collectionEdit:hover {{
        background-color: {BG_SECONDARY};
        color: {TEXT_PRIMARY};
    }}

    QPushButton#collectionDelete {{
        background-color: transparent;
        color: {TEXT_SECONDARY};
        border: none;
        border-radius: 14px;
        min-width: 28px;
        max-width: 28px;
        min-height: 28px;
        max-height: 28px;
    }}
    QPushButton#collectionDelete:hover {{
        background-color: {d15};
        color: {DANGER};
    }}

    /* ── Scrollbars ── */
    QScrollArea {{
        border: none;
        background: transparent;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 6px;
        margin: 4px 0;
    }}
    QScrollBar::handle:vertical {{
        background: {BORDER_SUBTLE};
        border-radius: 3px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {TEXT_SECONDARY};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: transparent;
    }}

    /* ── Diálogos modales ── */
    QDialog {{
        background-color: {BG_MAIN};
    }}

    QLabel#dialogTitle {{
        color: {TEXT_PRIMARY};
        font-size: 18px;
        font-weight: bold;
    }}

    QLabel#fieldLabel {{
        color: {TEXT_LABEL};
        font-size: 12px;
        font-weight: 500;
        padding-bottom: 2px;
        background: transparent;
    }}

    QLineEdit, QTextEdit, QComboBox {{
        background-color: {BG_INPUT_ALT};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER_SUBTLE};
        border-radius: {RADIUS_SM};
        padding: 10px 12px;
        font-size: 14px;
        min-height: 20px;
        min-width: 0;
    }}
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
        border: 1px solid {ACCENT};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox::down-arrow {{
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 6px solid {TEXT_SECONDARY};
        margin-right: 8px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {BG_SECONDARY};
        color: {TEXT_PRIMARY};
        selection-background-color: {BG_INPUT};
        border: 1px solid {BORDER_SUBTLE};
        border-radius: {RADIUS_SM};
        padding: 4px;
    }}

    QListWidget#dialogBookList {{
        background-color: {BG_INPUT_ALT};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER_SUBTLE};
        border-radius: {RADIUS_SM};
        padding: 4px;
    }}
    QListWidget#dialogBookList::item {{
        padding: 8px 10px;
        border-radius: 6px;
    }}
    QListWidget#dialogBookList::item:selected {{
        background-color: {BG_TAG};
        color: {TEXT_PRIMARY};
    }}
    QListWidget#dialogBookList::item:hover {{
        background-color: {BG_SECONDARY};
    }}

    QFrame#dialogDivider {{
        background-color: {BORDER_SUBTLE};
        max-height: 1px;
    }}

    QFrame#dialogIconBox {{
        background-color: {a15};
        border-radius: {RADIUS_SM};
        min-width: 40px;
        max-width: 40px;
        min-height: 40px;
        max-height: 40px;
    }}

    QFrame#fileInfoBox {{
        background-color: {BG_SECONDARY};
        border-radius: {RADIUS};
        padding: 4px;
    }}

    QPushButton#iconButton, QPushButton#iconButtonDanger {{
        padding: 8px;
    }}

    QPushButton#closeDialogBtn {{
        background-color: transparent;
        color: {TEXT_SECONDARY};
        border: none;
        font-size: 18px;
        min-width: 32px;
        max-width: 32px;
        min-height: 32px;
        max-height: 32px;
        border-radius: 16px;
    }}
    QPushButton#closeDialogBtn:hover {{
        background-color: {BG_SECONDARY};
        color: {TEXT_PRIMARY};
    }}

    QFrame#tagChip, QFrame#tagChipCustom {{
        background-color: {a12};
        border: 1px solid {a28};
        border-radius: 16px;
    }}
    QFrame#classificationChip {{
        background-color: rgba(96, 165, 250, 0.12);
        border: 1px solid rgba(96, 165, 250, 0.32);
        border-radius: 16px;
    }}

    QLabel#ratingLevelLabel {{
        font-size: 13px;
        font-weight: 600;
        color: {TEXT_PRIMARY};
    }}
    QFrame#tagStatusChipUnread {{
        background-color: rgba(55, 65, 81, 0.55);
        border: 1px solid rgba(209, 213, 219, 0.25);
        border-radius: 16px;
    }}
    QFrame#tagStatusChipReading {{
        background-color: rgba(30, 58, 95, 0.65);
        border: 1px solid rgba(147, 197, 253, 0.35);
        border-radius: 16px;
    }}
    QFrame#tagStatusChipCompleted {{
        background-color: rgba(6, 78, 59, 0.55);
        border: 1px solid rgba(110, 231, 183, 0.35);
        border-radius: 16px;
    }}
    QFrame#tagStatusChipPaused {{
        background-color: rgba(120, 53, 15, 0.55);
        border: 1px solid rgba(252, 211, 77, 0.35);
        border-radius: 16px;
    }}
    QFrame#tagStatusChipAbandoned {{
        background-color: rgba(76, 29, 36, 0.55);
        border: 1px solid rgba(252, 165, 165, 0.35);
        border-radius: 16px;
    }}
    QScrollArea#tagsBadgeScroll {{
        background-color: {BG_INPUT_ALT};
        border: 1px solid {BORDER_SUBTLE};
        border-radius: {RADIUS};
    }}
    QScrollArea#tagsBadgeScroll > QWidget > QWidget {{
        background: transparent;
    }}
    QFrame#tagsSection {{
        margin-top: 8px;
    }}
    QLabel#fieldHint {{
        color: {TEXT_SECONDARY};
        font-size: 12px;
        background: transparent;
        padding: 0 0 4px 0;
    }}
    QLabel#tagText {{
        color: {TEXT_PRIMARY};
        font-size: 12px;
        font-weight: 500;
        background: transparent;
        padding: 6px 4px 6px 10px;
    }}
    QLabel#tagTextStatus {{
        color: {TEXT_PRIMARY};
        font-size: 12px;
        font-weight: 600;
        background: transparent;
        padding: 6px 12px;
    }}
    QPushButton#tagRemove {{
        background-color: transparent;
        color: {TEXT_SECONDARY};
        border: none;
        min-width: 22px;
        max-width: 22px;
        min-height: 22px;
        max-height: 22px;
        border-radius: 11px;
        margin-right: 4px;
    }}
    QPushButton#tagRemove:hover {{
        background-color: rgba(255, 255, 255, 0.12);
        color: {TEXT_PRIMARY};
    }}

    QLabel#badgeLabel {{
        background: transparent;
        font-size: 11px;
        font-weight: 600;
        padding: 0;
    }}

    QPushButton#bookTagBadge {{
        background-color: {BG_TAG};
        color: {TEXT_PRIMARY};
        border: none;
        border-radius: 10px;
        padding: 2px 10px;
        font-size: 11px;
        font-weight: 500;
        min-height: 22px;
        max-height: 24px;
    }}
    QPushButton#bookTagBadge:hover {{
        background-color: {BG_TAG_HOVER};
    }}

    QPushButton#bookGridTagBadge {{
        background-color: {BG_TAG};
        color: {TEXT_PRIMARY};
        border: none;
        border-radius: 10px;
        padding: 3px 8px;
        font-size: 11px;
        font-weight: 500;
        min-height: 24px;
        max-height: 26px;
    }}
    QPushButton#bookGridTagBadge:hover {{
        background-color: {BG_TAG_HOVER};
    }}

    QPushButton#statusBadgeUnread,
    QPushButton#statusBadgeReading,
    QPushButton#statusBadgeCompleted,
    QPushButton#statusBadgePaused,
    QPushButton#statusBadgeAbandoned {{
        min-height: 24px;
        max-height: 26px;
    }}

    QFrame#bookGridMeta {{
        background: transparent;
    }}

    QFrame#tagPickerPopup {{
        background-color: {BG_SECONDARY};
        border: 1px solid {BORDER_SUBTLE};
        border-radius: {RADIUS_LG};
        min-width: 260px;
        max-width: 300px;
    }}
    QScrollArea#tagPickerScroll {{
        background: transparent;
        border: none;
    }}
    QLabel#tagPickerSectionHeader {{
        color: {TEXT_LABEL};
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        padding: 8px 14px 4px 14px;
        background: transparent;
    }}
    QFrame#tagPickerSeparator {{
        background-color: {BORDER_SUBTLE};
        max-height: 1px;
        margin: 6px 12px;
    }}
    QLabel#tagPickerEmpty {{
        color: {TEXT_SECONDARY};
        font-size: 12px;
        padding: 12px 14px;
        background: transparent;
    }}
    QFrame#tagPickerFooter {{
        background-color: rgba(0, 0, 0, 0.15);
        border-top: 1px solid {BORDER_SUBTLE};
    }}
    QPushButton#tagPickerNewBtn {{
        background-color: transparent;
        color: {ACCENT};
        border: none;
        font-size: 13px;
        font-weight: 500;
        text-align: left;
        padding: 4px 2px;
    }}
    QPushButton#tagPickerNewBtn:hover {{
        color: {ACCENT_HOVER};
    }}
    QPushButton#tagPickerOption {{
        background-color: transparent;
        color: {TEXT_PRIMARY};
        border: none;
        border-radius: {RADIUS_SM};
        font-size: 13px;
        text-align: left;
        padding: 0 12px;
        margin: 0 6px;
    }}
    QPushButton#tagPickerOption:hover {{
        background-color: {BG_INPUT};
    }}
    QPushButton#tagPickerOption:checked {{
        background-color: {a15};
        color: {ACCENT};
        font-weight: 600;
    }}

    QLabel#statusBadgeUnread, QPushButton#statusBadgeUnread {{
        background-color: {STATUS_UNREAD_BG};
        color: {STATUS_UNREAD_TEXT};
        border-radius: 10px;
        padding: 2px 10px;
        font-size: 11px;
        font-weight: 600;
        border: none;
        min-height: 22px;
        max-height: 24px;
    }}
    QLabel#statusBadgeReading, QPushButton#statusBadgeReading {{
        background-color: {STATUS_READING_BG};
        color: {STATUS_READING_TEXT};
        border-radius: 10px;
        padding: 2px 10px;
        font-size: 11px;
        font-weight: 600;
        border: none;
        min-height: 22px;
        max-height: 24px;
    }}
    QLabel#statusBadgeCompleted, QPushButton#statusBadgeCompleted {{
        background-color: {STATUS_COMPLETED_BG};
        color: {STATUS_COMPLETED_TEXT};
        border-radius: 10px;
        padding: 2px 10px;
        font-size: 11px;
        font-weight: 600;
        border: none;
        min-height: 22px;
        max-height: 24px;
    }}
    QLabel#statusBadgePaused, QPushButton#statusBadgePaused {{
        background-color: {STATUS_PAUSED_BG};
        color: {STATUS_PAUSED_TEXT};
        border-radius: 10px;
        padding: 2px 10px;
        font-size: 11px;
        font-weight: 600;
        border: none;
        min-height: 22px;
        max-height: 24px;
    }}
    QLabel#statusBadgeAbandoned, QPushButton#statusBadgeAbandoned {{
        background-color: {STATUS_ABANDONED_BG};
        color: {STATUS_ABANDONED_TEXT};
        border-radius: 10px;
        padding: 2px 10px;
        font-size: 11px;
        font-weight: 600;
        border: none;
        min-height: 22px;
        max-height: 24px;
    }}
    QPushButton#statusBadgeUnread:hover {{
        background-color: {STATUS_UNREAD_HOVER};
    }}
    QPushButton#statusBadgeReading:hover {{
        background-color: {STATUS_READING_HOVER};
    }}
    QPushButton#statusBadgeCompleted:hover {{
        background-color: {STATUS_COMPLETED_HOVER};
    }}
    QPushButton#statusBadgePaused:hover {{
        background-color: {STATUS_PAUSED_HOVER};
    }}
    QPushButton#statusBadgeAbandoned:hover {{
        background-color: {STATUS_ABANDONED_HOVER};
    }}

    /* ── QMessageBox ── */
    QMessageBox {{
        background-color: {BG_MAIN};
    }}
    QMessageBox QLabel {{
        color: {TEXT_PRIMARY};
        font-size: 14px;
    }}
    QMessageBox QPushButton {{
        background-color: {BG_INPUT};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER_SUBTLE};
        border-radius: {RADIUS_SM};
        padding: 8px 20px;
        font-size: 13px;
        min-width: 80px;
    }}
    QMessageBox QPushButton:hover {{
        background-color: {BG_SECONDARY};
    }}
    """


def msgbox_stylesheet() -> str:
    return f"""
    QMessageBox {{
        background-color: {BG_MAIN};
    }}
    QMessageBox QLabel {{
        color: {TEXT_PRIMARY};
        font-size: 14px;
    }}
    QMessageBox QLabel#qt_msgbox_label {{
        min-width: 300px;
        padding: 4px 0;
    }}
    QMessageBox QLabel#qt_msgbox_informativelabel {{
        color: {TEXT_SECONDARY};
        font-size: 13px;
    }}
    QMessageBox QPushButton {{
        background-color: {BG_INPUT};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER_SUBTLE};
        border-radius: {RADIUS_SM};
        padding: 8px 20px;
        font-size: 13px;
        min-width: 90px;
    }}
    QMessageBox QPushButton:hover {{
        background-color: {BG_SECONDARY};
    }}
    QMessageBox QPushButton:default {{
        border-color: {ACCENT};
    }}
    """


def notes_dialog_stylesheet() -> str:
    return f"""
    QDialog {{
        background-color: {BG_MAIN};
        color: {TEXT_PRIMARY};
        font-family: {FONT_FAMILY};
    }}
    QListWidget {{
        background-color: {BG_INPUT};
        border: 1px solid {BORDER_SUBTLE};
        border-radius: {RADIUS_SM};
        padding: 4px;
        color: {TEXT_PRIMARY};
        font-size: 14px;
        outline: none;
    }}
    QListWidget::item {{
        padding: 10px;
        border-radius: 6px;
        margin: 2px 0;
    }}
    QListWidget::item:selected {{
        background-color: {BG_TAG};
        color: {TEXT_PRIMARY};
    }}
    QListWidget::item:hover {{
        background-color: {BG_SECONDARY};
    }}
    QPushButton {{
        background-color: {BG_INPUT};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER_SUBTLE};
        border-radius: {RADIUS_SM};
        padding: 8px 16px;
        font-size: 14px;
        min-width: 100px;
    }}
    QPushButton:hover {{
        background-color: {BG_SECONDARY};
        border-color: {ACCENT};
    }}
    QPushButton:pressed {{
        background-color: {BG_INPUT_ALT};
    }}
    QLineEdit, QTextEdit, QTextBrowser {{
        background-color: {BG_INPUT};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER_SUBTLE};
        border-radius: {RADIUS_SM};
        padding: 10px;
        font-size: 14px;
        selection-background-color: {BG_TAG};
        min-width: 0;
    }}
    QLineEdit:focus, QTextEdit:focus {{
        border-color: {ACCENT};
    }}
    QLabel {{
        color: {TEXT_PRIMARY};
        font-size: 14px;
        background: transparent;
    }}
    QLabel#fieldLabel {{
        color: {TEXT_LABEL};
        font-size: 12px;
        font-weight: 500;
        padding-bottom: 2px;
    }}
    QComboBox#libraryFilterCombo {{
        background-color: {BG_INPUT};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER_SUBTLE};
        border-radius: {RADIUS_SM};
        padding: 6px 10px;
        min-width: 120px;
        font-size: 13px;
    }}
    QComboBox#libraryFilterCombo:focus, QComboBox#libraryFilterCombo:hover {{
        border-color: {ACCENT};
    }}
    QLabel#statsTitle {{
        font-size: 22px;
        font-weight: 700;
        color: {TEXT_PRIMARY};
    }}
    QLabel#statsSubtitle {{
        font-size: 13px;
        color: {TEXT_SECONDARY};
    }}
    QFrame#statCard {{
        background-color: {BG_SECONDARY};
        border: 1px solid {BORDER_SUBTLE};
        border-radius: {RADIUS_LG};
    }}
    QLabel#statValue {{
        font-size: 28px;
        font-weight: 700;
        color: {ACCENT};
    }}
    QLabel#statLabel {{
        font-size: 12px;
        color: {TEXT_SECONDARY};
    }}
    QFrame#statsRecentList {{
        background-color: {BG_INPUT};
        border: 1px solid {BORDER_SUBTLE};
        border-radius: {RADIUS_SM};
    }}
    QLabel#statsRecentTitle {{
        font-size: 14px;
        color: {TEXT_PRIMARY};
    }}
    QLabel#statsRecentMeta {{
        font-size: 12px;
        color: {TEXT_SECONDARY};
    }}
    QLabel#statsEmpty {{
        color: {TEXT_SECONDARY};
        font-size: 13px;
    }}
  """


def pdf_viewer_stylesheet() -> str:
    a12 = accent_rgba(0.12)
    a45 = accent_rgba(0.45)
    a10 = accent_rgba(0.10)
    a18 = accent_rgba(0.18)
    return f"""
    QDialog#pdfViewer {{
        background-color: {BG_MAIN};
        color: {TEXT_PRIMARY};
        font-family: {FONT_FAMILY};
    }}
    QFrame#viewerToolbar {{
        background-color: {BG_SIDEBAR};
        border-bottom: 1px solid {BORDER_SUBTLE};
    }}
    QLabel#viewerToolbarLabel {{
        color: {TEXT_SECONDARY};
        font-size: 13px;
        background: transparent;
    }}
    QLineEdit#viewerSearch {{
        background-color: {BG_INPUT};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER_SUBTLE};
        border-radius: {RADIUS_SM};
        padding: 6px 10px;
        font-size: 13px;
        min-width: 160px;
    }}
    QLineEdit#viewerSearch:focus {{
        border-color: {ACCENT};
    }}
    QLineEdit#pageInput {{
        background-color: {BG_INPUT};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER_SUBTLE};
        border-radius: {RADIUS_SM};
        padding: 4px 8px;
        max-width: 52px;
        font-size: 13px;
    }}
    QPushButton#viewerToolBtn {{
        background-color: transparent;
        border: 1px solid {BORDER_SUBTLE};
        border-radius: {RADIUS_SM};
        padding: 6px 10px;
        min-width: 36px;
        min-height: 36px;
    }}
    QPushButton#viewerToolBtn:hover {{
        border-color: {ACCENT};
        background-color: {a10};
    }}
    QPushButton#viewerToolBtn[active="true"] {{
        border-color: {ACCENT};
        background-color: {a18};
    }}
    QPushButton#viewerTextBtn {{
        background-color: transparent;
        color: {TEXT_SECONDARY};
        border: 1px solid {BORDER_SUBTLE};
        border-radius: {RADIUS_SM};
        padding: 5px 10px;
        font-size: 12px;
        min-height: 30px;
    }}
    QPushButton#viewerTextBtn:hover {{
        border-color: {ACCENT};
        color: {TEXT_PRIMARY};
        background-color: {a10};
    }}
    QPushButton#viewerTextBtn[active="true"] {{
        border-color: {ACCENT};
        color: {ACCENT};
        background-color: {a18};
    }}
    QLabel#viewerSearchCount {{
        color: {ACCENT};
        font-size: 12px;
        font-weight: 600;
        padding: 0 4px;
        min-width: 48px;
        background: transparent;
    }}
    QScrollArea#viewerScroll {{
        background-color: {BG_MAIN};
        border: none;
    }}
    QFrame#viewerSidebar {{
        background-color: {BG_SIDEBAR};
        border-left: 1px solid {BORDER_SUBTLE};
    }}
    QLabel#viewerSidebarTitle {{
        color: {TEXT_PRIMARY};
        font-size: 14px;
        font-weight: 600;
    }}
    QTabWidget#viewerTabs::pane {{
        border: none;
        background: transparent;
    }}
    QTabBar::tab {{
        background: transparent;
        color: {TEXT_SECONDARY};
        padding: 6px 12px;
        border-bottom: 2px solid transparent;
    }}
    QTabBar::tab:selected {{
        color: {ACCENT};
        border-bottom: 2px solid {ACCENT};
    }}
    QListWidget#viewerList {{
        background-color: transparent;
        border: none;
        padding: 0;
        outline: none;
    }}
    QListWidget#viewerList::item {{
        background: transparent;
        border: none;
        padding: 0;
        margin: 0;
    }}
    QListWidget#viewerList::item:selected {{
        background: transparent;
    }}
    QFrame#annotationCard {{
        background-color: {BG_INPUT};
        border: 1px solid {BORDER_SUBTLE};
        border-radius: {RADIUS_SM};
    }}
    QFrame#annotationCard:hover {{
        border-color: {a45};
        background-color: {BG_SECONDARY};
    }}
    QFrame#annotationCard[selected="true"] {{
        border-color: {ACCENT};
        background-color: {a12};
    }}
    QFrame#annotationAccentBookmark {{
        background-color: #60a5fa;
        border-radius: 2px;
    }}
    QFrame#annotationAccentNote {{
        background-color: {ACCENT};
        border-radius: 2px;
    }}
    QFrame#annotationAccentHighlight {{
        background-color: #fbbf24;
        border-radius: 2px;
    }}
    QLabel#annotationPageBadge {{
        background-color: {BG_SECONDARY};
        color: {TEXT_SECONDARY};
        border-radius: 10px;
        padding: 2px 8px;
        font-size: 11px;
        font-weight: 600;
    }}
    QLabel#annotationKindLabel {{
        color: {TEXT_LABEL};
        font-size: 10px;
        font-weight: 600;
        background: transparent;
    }}
    QLabel#annotationTitle {{
        color: {TEXT_PRIMARY};
        font-size: 13px;
        font-weight: 600;
        background: transparent;
    }}
    QLabel#annotationPreview {{
        color: {TEXT_SECONDARY};
        font-size: 12px;
        background: transparent;
    }}
    QLabel#annotationHighlightQuote {{
        color: #fde68a;
        font-size: 12px;
        font-style: italic;
        background: transparent;
    }}
    QLabel#annotationEmpty {{
        color: {TEXT_SECONDARY};
        font-size: 13px;
        padding: 24px 12px;
        background: transparent;
    }}
    QFrame#selectionPopup {{
        background-color: {BG_SECONDARY};
        border: 1px solid {ACCENT};
        border-radius: {RADIUS_SM};
    }}
    QFrame#eyeComfortPopup {{
        background-color: {BG_SECONDARY};
        border: 1px solid {BORDER_SUBTLE};
        border-radius: {RADIUS_SM};
        min-width: 260px;
    }}
    QLabel#eyeComfortTitle {{
        color: {TEXT_PRIMARY};
        font-size: 14px;
        font-weight: 600;
        background: transparent;
    }}
    QLabel#eyeComfortHint {{
        color: {TEXT_SECONDARY};
        font-size: 12px;
        background: transparent;
    }}
    QLabel#eyeComfortIntensityValue {{
        color: {ACCENT};
        font-size: 12px;
        font-weight: 600;
        background: transparent;
    }}
    QComboBox#eyeComfortCombo {{
        background-color: {BG_INPUT};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER_SUBTLE};
        border-radius: {RADIUS_SM};
        padding: 6px 10px;
        font-size: 13px;
    }}
    QComboBox#eyeComfortCombo:focus, QComboBox#eyeComfortCombo:hover {{
        border-color: {ACCENT};
    }}
    QSlider#eyeComfortSlider::groove:horizontal {{
        height: 4px;
        background: {BG_INPUT};
        border-radius: 2px;
    }}
    QSlider#eyeComfortSlider::handle:horizontal {{
        background: {ACCENT};
        width: 14px;
        height: 14px;
        margin: -5px 0;
        border-radius: 7px;
    }}
    QSlider#eyeComfortSlider::sub-page:horizontal {{
        background: {a45};
        border-radius: 2px;
    }}
    QLabel#readingModeHint {{
        color: {TEXT_SECONDARY};
        font-size: 12px;
        padding: 8px;
        background: transparent;
    }}
    QFrame#ocrBanner {{
        background-color: {BG_SECONDARY};
        border-bottom: 1px solid {BORDER_SUBTLE};
    }}
    QLabel#ocrBannerText {{
        color: {TEXT_PRIMARY};
        font-size: 13px;
        background: transparent;
    }}
    QLabel#ocrBannerProgress {{
        color: {ACCENT};
        font-size: 12px;
        background: transparent;
    }}
    """


def msgbox_danger_button_style() -> str:
    return f"""
    QPushButton {{
        background-color: {DANGER_BORDER};
        color: white;
        border: none;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: {DANGER};
    }}
    """


def tour_callout_stylesheet() -> str:
    """Estilos del callout flotante del tour guiado."""
    return f"""
    QFrame#tourCallout {{
        background-color: {BG_SECONDARY};
        border: 1px solid {BORDER_SUBTLE};
        border-left: 4px solid {ACCENT};
        border-radius: {RADIUS_LG};
    }}
    QFrame#tourCallout QLabel {{
        background: transparent;
        border: none;
    }}
    QProgressBar#tourProgress {{
        background-color: {BG_INPUT};
        border: none;
        border-radius: 3px;
        max-height: 4px;
    }}
    QProgressBar#tourProgress::chunk {{
        background-color: {ACCENT};
        border-radius: 3px;
    }}
    QLabel#tourStepIndicator {{
        color: {ACCENT};
        font-size: 11px;
        font-weight: 700;
    }}
    QLabel#tourTitle {{
        color: {TEXT_PRIMARY};
        font-size: 15px;
        font-weight: 600;
    }}
    QLabel#tourBody {{
        color: {TEXT_SECONDARY};
        font-size: 13px;
    }}
    QPushButton#ghostButton, QPushButton#secondaryButton, QPushButton#primaryButton {{
        font-size: 13px;
    }}
    """
