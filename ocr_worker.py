"""Hilo de trabajo para OCR en segundo plano."""

from PyQt5.QtCore import QObject, QThread, pyqtSignal


class OcrWorker(QObject):
    progress = pyqtSignal(int, int)  # actual, total
    page_done = pyqtSignal(int)
    finished = pyqtSignal(bool)
    error = pyqtSignal(str)

    def __init__(self, ocr_manager, start_page=0, end_page=0):
        super().__init__()
        self._ocr = ocr_manager
        self._start = start_page
        self._end = end_page

    def run(self):
        try:
            self._ocr.enable()
            total = self._end - self._start + 1
            for i, page_num in enumerate(range(self._start, self._end + 1)):
                self._ocr.ensure_page(page_num)
                self.page_done.emit(page_num)
                self.progress.emit(i + 1, total)
            self.finished.emit(True)
        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit(False)


def start_ocr_thread(ocr_manager, start_page, end_page, parent, callbacks):
    """Inicia OCR en un QThread. callbacks: on_progress, on_page, on_done, on_error."""
    thread = QThread(parent)
    worker = OcrWorker(ocr_manager, start_page, end_page)
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    worker.progress.connect(callbacks.get("progress", lambda *_: None))
    worker.page_done.connect(callbacks.get("page", lambda *_: None))
    worker.error.connect(callbacks.get("error", lambda *_: None))
    worker.finished.connect(callbacks.get("done", lambda *_: None))
    worker.finished.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    thread.start()
    return thread
