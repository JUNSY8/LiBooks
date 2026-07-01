"""OCR para PDFs escaneados (PyMuPDF + Tesseract)."""

import json
import logging
import os
import re
import shutil
from typing import Callable, Dict, List, Optional, Tuple

import fitz

from i18n import get_language
from paths import user_data_dir
from pdf_meta import hash_archivo

logger = logging.getLogger(__name__)

_TESSDATA_CANDIDATES = [
    os.environ.get("TESSDATA_PREFIX", ""),
    r"C:\Program Files\Tesseract-OCR\tessdata",
    r"C:\Program Files (x86)\Tesseract-OCR\tessdata",
    "/usr/share/tesseract-ocr/5/tessdata",
    "/usr/share/tesseract-ocr/4.00/tessdata",
    "/usr/local/share/tessdata",
]


def _configure_tesseract() -> Optional[str]:
    for path in _TESSDATA_CANDIDATES:
        if path and os.path.isdir(path):
            os.environ.setdefault("TESSDATA_PREFIX", path)
            if hasattr(fitz, "TESSDATA_PREFIX"):
                fitz.TESSDATA_PREFIX = path
            return path
    return None


def is_tesseract_available() -> bool:
    if shutil.which("tesseract"):
        return True
    return _configure_tesseract() is not None


def ocr_language() -> str:
    return "spa" if get_language() == "es" else "eng"


def pagina_tiene_texto(page: fitz.Page, min_chars: int = 12) -> bool:
    try:
        return len((page.get_text() or "").strip()) >= min_chars
    except Exception:
        return False


def documento_necesita_ocr(doc: fitz.Document, muestra: int = 5) -> bool:
    """Heurística: si las primeras páginas no tienen texto extraíble."""
    if not doc or doc.page_count == 0:
        return False
    n = min(muestra, doc.page_count)
    sin_texto = 0
    for i in range(n):
        if not pagina_tiene_texto(doc.load_page(i)):
            sin_texto += 1
    return sin_texto >= max(1, n // 2)


def _cache_dir(cache_key: str) -> str:
    path = os.path.join(user_data_dir(), "ocr_cache", cache_key)
    os.makedirs(path, exist_ok=True)
    return path


def _cache_path(cache_key: str, page_num: int) -> str:
    return os.path.join(_cache_dir(cache_key), f"page_{page_num}.json")


def _ocr_page_words(page: fitz.Page, language: str) -> List[list]:
    _configure_tesseract()
    tp = page.get_textpage_ocr(language=language, dpi=200, full=True)
    words = []
    for w in page.get_text("words", textpage=tp):
        words.append([w[0], w[1], w[2], w[3], w[4]])
    return words


def cargar_palabras_cache(cache_key: str, page_num: int) -> Optional[List[list]]:
    path = _cache_path(cache_key, page_num)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logger.warning("Cache OCR corrupta %s: %s", path, e)
        return None


def guardar_palabras_cache(cache_key: str, page_num: int, words: List[list]) -> None:
    with open(_cache_path(cache_key, page_num), "w", encoding="utf-8") as f:
        json.dump(words, f)


class OcrManager:
    """Gestiona OCR bajo demanda y búsqueda en PDFs escaneados."""

    def __init__(self, doc: fitz.Document, pdf_path: str, file_hash: Optional[str] = None):
        self.doc = doc
        self.pdf_path = pdf_path
        self.cache_key = file_hash or hash_archivo(pdf_path) or os.path.basename(pdf_path)
        self.active = False
        self.language = ocr_language()
        self._words: Dict[int, List[list]] = {}
        self._needs_ocr = documento_necesita_ocr(doc)

    def needs_ocr(self) -> bool:
        return self._needs_ocr

    def enable(self) -> bool:
        if not is_tesseract_available():
            return False
        self.active = True
        return True

    def ensure_page(self, page_num: int) -> List[list]:
        if page_num in self._words:
            return self._words[page_num]
        cached = cargar_palabras_cache(self.cache_key, page_num)
        if cached is not None:
            self._words[page_num] = cached
            return cached
        if not self.active:
            return []
        try:
            page = self.doc.load_page(page_num)
            words = _ocr_page_words(page, self.language)
            self._words[page_num] = words
            guardar_palabras_cache(self.cache_key, page_num, words)
            return words
        except Exception as e:
            logger.exception("OCR falló en página %s: %s", page_num, e)
            return []

    def ensure_range(self, start: int, end: int,
                     progress: Optional[Callable[[int, int], None]] = None) -> None:
        if not self.active:
            return
        for i in range(start, end + 1):
            self.ensure_page(i)
            if progress:
                progress(i - start + 1, end - start + 1)

    def get_words(self, page_num: int) -> List[list]:
        return self.ensure_page(page_num) if self.active else []

    def search(self, query: str) -> List[Tuple[int, fitz.Rect]]:
        if not query.strip() or not self.active:
            return []
        pattern = re.compile(re.escape(query.strip()), re.IGNORECASE)
        matches: List[Tuple[int, fitz.Rect]] = []
        for page_num in range(self.doc.page_count):
            words = self.ensure_page(page_num)
            if not words:
                continue
            text_line = " ".join(w[4] for w in words)
            for m in pattern.finditer(text_line):
                start, end = m.start(), m.end()
                rects = _rects_for_span(words, start, end, text_line)
                for rect in rects:
                    matches.append((page_num, rect))
        return matches

    def progress_cached(self) -> Tuple[int, int]:
        total = self.doc.page_count if self.doc else 0
        done = sum(
            1 for i in range(total)
            if os.path.isfile(_cache_path(self.cache_key, i))
        )
        return done, total


def _rects_for_span(words: List[list], start: int, end: int, full_text: str) -> List[fitz.Rect]:
    """Mapea un rango de caracteres al texto unido a rectángulos de palabras."""
    rects = []
    pos = 0
    for w in words:
        word = w[4]
        word_start = pos
        word_end = pos + len(word)
        if word_end > start and word_start < end:
            rects.append(fitz.Rect(w[0], w[1], w[2], w[3]))
        pos = word_end + 1
        if pos > end:
            break
    if not rects and words:
        rects.append(fitz.Rect(words[0][0], words[0][1], words[0][2], words[0][3]))
    return rects


def guardar_pdf_buscable(
    src_path: str,
    dest_path: str,
    language: Optional[str] = None,
    progress: Optional[Callable[[int, int], None]] = None,
) -> bool:
    """Genera una copia del PDF con capa de texto invisible (buscable)."""
    if not is_tesseract_available():
        return False
    lang = language or ocr_language()
    _configure_tesseract()
    try:
        src = fitz.open(src_path)
        out = fitz.open()
        total = src.page_count
        for i in range(total):
            page = src.load_page(i)
            out_page = out.new_page(width=page.rect.width, height=page.rect.height)
            out_page.insert_image(page.rect, pixmap=page.get_pixmap(dpi=150))
            if not pagina_tiene_texto(page):
                for w in _ocr_page_words(page, lang):
                    rect = fitz.Rect(w[0], w[1], w[2], w[3])
                    out_page.insert_textbox(
                        rect, w[4], fontsize=max(6, rect.height * 0.8), render_mode=3
                    )
            if progress:
                progress(i + 1, total)
        out.save(dest_path, garbage=4, deflate=True)
        out.close()
        src.close()
        return True
    except Exception as e:
        logger.exception("No se pudo guardar PDF buscable: %s", e)
        return False
