"""Tema visual LiBooks — paleta y hojas de estilo QSS."""

# Paleta
BG_MAIN = "#121e24"
BG_SECONDARY = "#1e2d36"
BG_INPUT = "#1a2a33"
BG_INPUT_ALT = "#243436"
BG_SIDEBAR = "#0f1a20"
BG_TAG = "#065f46"

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

FONT_FAMILY = "Segoe UI, Arial, sans-serif"


def app_stylesheet() -> str:
    return f"""
    * {{
        font-family: {FONT_FAMILY};
    }}

    QWidget {{
        background-color: {BG_MAIN};
        color: {TEXT_PRIMARY};
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
        background-color: rgba(30, 45, 54, 0.6);
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
        background-color: rgba(30, 45, 54, 0.6);
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
        background-color: rgba(74, 222, 169, 0.1);
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
        background-color: rgba(239, 68, 68, 0.12);
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
        background-color: rgba(239, 68, 68, 0.15);
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
        background-color: rgba(74, 222, 169, 0.15);
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
        background-color: rgba(74, 222, 169, 0.08);
    }}
    QPushButton#viewToggleBtn[active="true"] {{
        border-color: {ACCENT};
        background-color: rgba(74, 222, 169, 0.15);
    }}

    QScrollArea#bookGridScroll {{
        background-color: transparent;
        border: none;
    }}

    QLabel#dropOverlay {{
        background-color: rgba(15, 26, 32, 0.92);
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
    QPushButton#collectionItem {{
        background-color: transparent;
        color: {TEXT_SECONDARY};
        border: none;
        border-radius: {RADIUS_SM};
        padding: 8px 12px;
        text-align: left;
        font-size: 13px;
    }}
    QPushButton#collectionItem:hover {{
        background-color: {BG_SECONDARY};
        color: {TEXT_PRIMARY};
    }}

    QPushButton#collectionDelete {{
        background-color: transparent;
        color: {DANGER};
        border: none;
        border-radius: 14px;
        font-size: 16px;
        min-width: 28px;
        max-width: 28px;
        min-height: 28px;
        max-height: 28px;
    }}
    QPushButton#collectionDelete:hover {{
        background-color: rgba(239, 68, 68, 0.15);
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
        background-color: rgba(74, 222, 169, 0.15);
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

    QFrame#tagChip {{
        background-color: {BG_TAG};
        border-radius: 14px;
        padding: 2px 4px;
    }}
    QLabel#tagText {{
        color: {TEXT_PRIMARY};
        font-size: 12px;
        background: transparent;
        padding: 4px 8px;
    }}
    QPushButton#tagRemove {{
        background-color: transparent;
        color: {TEXT_PRIMARY};
        border: none;
        font-size: 12px;
        min-width: 20px;
        max-width: 20px;
        min-height: 20px;
        max-height: 20px;
        border-radius: 10px;
    }}
    QPushButton#tagRemove:hover {{
        background-color: rgba(255, 255, 255, 0.15);
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
        background-color: rgba(74, 222, 169, 0.1);
    }}
    QPushButton#viewerToolBtn[active="true"] {{
        border-color: {ACCENT};
        background-color: rgba(74, 222, 169, 0.18);
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
        background-color: rgba(74, 222, 169, 0.1);
    }}
    QPushButton#viewerTextBtn[active="true"] {{
        border-color: {ACCENT};
        color: {ACCENT};
        background-color: rgba(74, 222, 169, 0.18);
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
        background-color: {BG_INPUT};
        border: 1px solid {BORDER_SUBTLE};
        border-radius: {RADIUS_SM};
        padding: 4px;
    }}
    QListWidget#viewerList::item {{
        padding: 8px;
        border-radius: 6px;
    }}
    QListWidget#viewerList::item:selected {{
        background-color: {BG_TAG};
    }}
    QFrame#selectionPopup {{
        background-color: {BG_SECONDARY};
        border: 1px solid {ACCENT};
        border-radius: {RADIUS_SM};
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
        background-color: #dc2626;
    }}
    """
