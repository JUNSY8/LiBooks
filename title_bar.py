"""Barra de titulo personalizada y ventana sin marco nativo."""

import sys
from typing import Optional

from PyQt5.QtCore import Qt, QEvent, QObject, QPoint, QTimer
from PyQt5.QtWidgets import (
    QWidget, QDialog, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFrame,
)

from icons import app_icon, icon_label, set_button_icon
from i18n import tr
from styles import TITLE_BAR_ICON, TITLE_BAR_ICON_HOVER

_RESIZE_BORDER = 6
_TITLE_BAR_HEIGHT = 36
_WIN_BTN_WIDTH = 46
_WIN_BTN_HEIGHT = 36
_TITLE_ICON_SIZE = 14


def _resize_edge_at(pos: QPoint, size, border: int = _RESIZE_BORDER) -> Optional[Qt.Edge]:
    """Devuelve el borde de redimensionado bajo pos, o None."""
    x, y = pos.x(), pos.y()
    w, h = size.width(), size.height()
    on_left = x < border
    on_right = x >= w - border
    on_top = y < border
    on_bottom = y >= h - border

    if on_top and on_left:
        return Qt.TopEdge | Qt.LeftEdge
    if on_top and on_right:
        return Qt.TopEdge | Qt.RightEdge
    if on_bottom and on_left:
        return Qt.BottomEdge | Qt.LeftEdge
    if on_bottom and on_right:
        return Qt.BottomEdge | Qt.RightEdge
    if on_left:
        return Qt.LeftEdge
    if on_right:
        return Qt.RightEdge
    if on_top:
        return Qt.TopEdge
    if on_bottom:
        return Qt.BottomEdge
    return None


def _cursor_for_edge(edge: Qt.Edge):
    if edge in (Qt.LeftEdge, Qt.RightEdge):
        return Qt.SizeHorCursor
    if edge in (Qt.TopEdge, Qt.BottomEdge):
        return Qt.SizeVerCursor
    if edge in (Qt.TopEdge | Qt.LeftEdge, Qt.BottomEdge | Qt.RightEdge):
        return Qt.SizeFDiagCursor
    if edge in (Qt.TopEdge | Qt.RightEdge, Qt.BottomEdge | Qt.LeftEdge):
        return Qt.SizeBDiagCursor
    return Qt.ArrowCursor



def _detach_resize_filter(widget: QWidget) -> None:
    filt = getattr(widget, "_resize_filter", None)
    if filt is not None:
        widget.removeEventFilter(filt)
        widget._resize_filter = None


class _ResizeEventFilter(QObject):
    """Redimensionado por bordes en plataformas sin WM_NCHITTEST."""

    def __init__(self, window: QWidget):
        super().__init__(window)
        self._window = window

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Close, QEvent.DeferredDelete):
            return False
        try:
            window = self._window
            if window is None or window.isMaximized():
                return False
        except RuntimeError:
            return False

        if event.type() == QEvent.MouseButtonPress:
            if event.button() != Qt.LeftButton:
                return False
            try:
                edge = _resize_edge_at(
                    window.mapFromGlobal(event.globalPos()),
                    window.size(),
                )
                if edge is None:
                    return False
                handle = window.windowHandle()
                if handle is not None:
                    handle.startSystemResize(edge)
                return True
            except RuntimeError:
                return False

        if event.type() == QEvent.MouseMove and not event.buttons():
            try:
                edge = _resize_edge_at(
                    window.mapFromGlobal(event.globalPos()),
                    window.size(),
                )
                window.setCursor(
                    _cursor_for_edge(edge) if edge is not None else Qt.ArrowCursor
                )
            except RuntimeError:
                return False

        return False



def _set_title_icon(button, name: str, color: str = TITLE_BAR_ICON) -> None:
    set_button_icon(button, name, _TITLE_ICON_SIZE, color)


def _wire_title_button_hover(button, icon_name: str, *, close: bool = False) -> None:
    """Actualiza el color del icono al pasar el raton."""
    hover = "#ffffff" if close else TITLE_BAR_ICON_HOVER

    def _enter(_event):
        _set_title_icon(button, icon_name, hover)

    def _leave(_event):
        _set_title_icon(button, icon_name, TITLE_BAR_ICON)

    button.enterEvent = _enter
    button.leaveEvent = _leave



class CustomTitleBar(QFrame):
    """Barra superior con titulo y controles de ventana."""

    def __init__(self, window: QWidget):
        super().__init__(window)
        self._window = window
        self.setObjectName("titleBar")
        self.setFixedHeight(_TITLE_BAR_HEIGHT)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 0, 0)
        layout.setSpacing(8)

        self._icon = icon_label("app", 18)
        layout.addWidget(self._icon)

        self._window_title = "LiBooks"
        self._title = QLabel(self._window_title)
        self._title.setObjectName("titleBarLabel")
        layout.addWidget(self._title)
        layout.addStretch()

        self._btn_min = QPushButton()
        self._btn_min.setObjectName("titleBarButton")
        self._btn_min.setFixedSize(_WIN_BTN_WIDTH, _WIN_BTN_HEIGHT)
        self._btn_min.clicked.connect(window.showMinimized)

        self._btn_max = QPushButton()
        self._btn_max.setObjectName("titleBarButton")
        self._btn_max.setFixedSize(_WIN_BTN_WIDTH, _WIN_BTN_HEIGHT)
        self._btn_max.clicked.connect(self._toggle_maximize)

        self._btn_close = QPushButton()
        self._btn_close.setObjectName("titleBarClose")
        self._btn_close.setFixedSize(_WIN_BTN_WIDTH, _WIN_BTN_HEIGHT)
        self._btn_close.clicked.connect(window.close)

        layout.addWidget(self._btn_min)
        layout.addWidget(self._btn_max)
        layout.addWidget(self._btn_close)

        self._wire_button_hovers()
        self.retranslate_ui()
        self.sync_window_state()

    def _wire_button_hovers(self):
        _wire_title_button_hover(self._btn_min, "minimize")
        _wire_title_button_hover(self._btn_close, "close", close=True)
        self._btn_max.enterEvent = self._on_max_enter
        self._btn_max.leaveEvent = self._on_max_leave

    def _max_icon_name(self) -> str:
        return "restore" if self._window.isMaximized() else "maximize"

    def _on_max_enter(self, _event):
        _set_title_icon(self._btn_max, self._max_icon_name(), TITLE_BAR_ICON_HOVER)

    def _on_max_leave(self, _event):
        _set_title_icon(self._btn_max, self._max_icon_name(), TITLE_BAR_ICON)

    def retranslate_ui(self):
        self._title.setText(self._window_title)
        _set_title_icon(self._btn_min, "minimize")
        self._btn_min.setToolTip(tr("title_bar.minimize"))
        self._refresh_maximize_button()
        _set_title_icon(self._btn_close, "close")
        self._btn_close.setToolTip(tr("title_bar.close"))

    def set_title(self, text: str):
        self._window_title = text
        self._title.setText(text)

    def sync_window_state(self):
        self._refresh_maximize_button()

    def _refresh_maximize_button(self):
        name = self._max_icon_name()
        _set_title_icon(self._btn_max, name)
        key = "title_bar.restore" if name == "restore" else "title_bar.maximize"
        self._btn_max.setToolTip(tr(key))

    def _toggle_maximize(self):
        if self._window.isMaximized():
            self._window.showNormal()
        else:
            self._window.showMaximized()
        QTimer.singleShot(0, self.sync_window_state)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            target = self.childAt(event.pos())
            if isinstance(target, QPushButton):
                super().mousePressEvent(event)
                return
            handle = self._window.windowHandle()
            if handle is not None:
                handle.startSystemMove()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            target = self.childAt(event.pos())
            if not isinstance(target, QPushButton):
                self._toggle_maximize()
                event.accept()
                return
        super().mouseDoubleClickEvent(event)


def _win_native_event(widget, message):
  import ctypes
  from ctypes import wintypes

  msg = wintypes.MSG.from_address(int(message))

  if msg.message == 0x0084:  # WM_NCHITTEST
      if widget.isMaximized():
          return True, 1  # HTCLIENT

      pos = widget.mapFromGlobal(QPoint(msg.pt.x, msg.pt.y))
      edge = _resize_edge_at(pos, widget.size())
      if edge is None:
          return False, 0

      hit_tests = {
          Qt.LeftEdge: 10,
          Qt.RightEdge: 11,
          Qt.TopEdge: 12,
          Qt.BottomEdge: 15,
          Qt.TopEdge | Qt.LeftEdge: 13,
          Qt.TopEdge | Qt.RightEdge: 14,
          Qt.BottomEdge | Qt.LeftEdge: 16,
          Qt.BottomEdge | Qt.RightEdge: 17,
      }
      return True, hit_tests.get(edge, 1)

  if msg.message == 0x0024:  # WM_GETMINMAXINFO
      class POINT(ctypes.Structure):
          _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]

      class RECT(ctypes.Structure):
          _fields_ = [
              ("left", wintypes.LONG),
              ("top", wintypes.LONG),
              ("right", wintypes.LONG),
              ("bottom", wintypes.LONG),
          ]

      class MONITORINFO(ctypes.Structure):
          _fields_ = [
              ("cbSize", wintypes.DWORD),
              ("rcMonitor", RECT),
              ("rcWork", RECT),
              ("dwFlags", wintypes.DWORD),
          ]

      class MINMAXINFO(ctypes.Structure):
          _fields_ = [
              ("ptReserved", POINT),
              ("ptMaxSize", POINT),
              ("ptMaxPosition", POINT),
              ("ptMinTrackSize", POINT),
              ("ptMaxTrackSize", POINT),
          ]

      mmi = MINMAXINFO.from_address(msg.lParam)
      monitor = ctypes.windll.user32.MonitorFromWindow(msg.hWnd, 2)
      mi = MONITORINFO()
      mi.cbSize = ctypes.sizeof(MONITORINFO)
      if ctypes.windll.user32.GetMonitorInfoW(monitor, ctypes.byref(mi)):
          mmi.ptMaxSize.x = mi.rcWork.right - mi.rcWork.left
          mmi.ptMaxSize.y = mi.rcWork.bottom - mi.rcWork.top
          mmi.ptMaxPosition.x = mi.rcWork.left
          mmi.ptMaxPosition.y = mi.rcWork.top
      return True, 0

  return False, 0


class FramelessWidget(QWidget):
    """Ventana principal sin barra nativa del SO."""

    def _init_frameless_window(self):
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setWindowIcon(app_icon())
        self.setMinimumSize(800, 500)
        self._resize_filter = _ResizeEventFilter(self)
        self.installEventFilter(self._resize_filter)



    def closeEvent(self, event):
        _detach_resize_filter(self)
        super().closeEvent(event)



    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            title_bar = getattr(self, "_title_bar", None)
            if title_bar is not None:
                QTimer.singleShot(0, title_bar.sync_window_state)
        super().changeEvent(event)

    def nativeEvent(self, event_type, message):
        if sys.platform == "win32" and event_type == b"windows_generic_MSG":
            handled, result = _win_native_event(self, message)
            if handled:
                return result, True
        return super().nativeEvent(event_type, message)


class FramelessDialog(QDialog):
    """Dialogo modal sin barra nativa del SO."""

    def _init_frameless_dialog(self, title: str = ""):
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setWindowIcon(app_icon())
        self._resize_filter = _ResizeEventFilter(self)
        self.installEventFilter(self._resize_filter)
        self._setup_frameless_shell(title)

    def _setup_frameless_shell(self, title: str = ""):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._title_bar = CustomTitleBar(self)
        if title:
            self._title_bar.set_title(title)
        outer.addWidget(self._title_bar)

        self._frameless_body = QWidget()
        outer.addWidget(self._frameless_body, 1)

    def frameless_layout(self, margins=(24, 20, 24, 20), spacing: int = 16):
        layout = QVBoxLayout(self._frameless_body)
        layout.setContentsMargins(*margins)
        layout.setSpacing(spacing)
        return layout

    def set_frameless_title(self, title: str):
        self.setWindowTitle(title)
        if hasattr(self, "_title_bar"):
            self._title_bar.set_title(title)
            self._title_bar.retranslate_ui()

    def closeEvent(self, event):
        _detach_resize_filter(self)
        super().closeEvent(event)

    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            title_bar = getattr(self, "_title_bar", None)
            if title_bar is not None:
                QTimer.singleShot(0, title_bar.sync_window_state)
        super().changeEvent(event)

    def nativeEvent(self, event_type, message):
        if sys.platform == "win32" and event_type == b"windows_generic_MSG":
            handled, result = _win_native_event(self, message)
            if handled:
                return result, True
        return super().nativeEvent(event_type, message)


