content = """Graduable eye-comfort filters for the PDF viewer (Kindle-style)."""

from typing import List, Optional, Tuple

from i18n import tr

MODES = ("none", "warm", "sepia", "night")
DEFAULT_MODE = "none"
DEFAULT_INTENSITY = 50
MAX_INTENSITY = 100

_OVERLAYS = {
    "warm": (255, 196, 120, 110),
    "sepia": (170, 115, 55, 130),
    "night": (20, 35, 70, 150),
}


def normalize_mode(mode):
    return mode if mode in MODES else DEFAULT_MODE


def normalize_intensity(value):
    try:
        n = int(value)
    except (TypeError, ValueError):
        return 0
    return max(0, min(MAX_INTENSITY, n))


def overlay_for_mode(mode, intensity):
    mode = normalize_mode(mode)
    intensity = normalize_intensity(intensity)
    if mode == "none" or intensity == 0:
        return None
    r, g, b, max_a = _OVERLAYS[mode]
    alpha = int(max_a * intensity / MAX_INTENSITY)
    return (r, g, b, alpha)


def is_active(mode, intensity):
    return overlay_for_mode(mode, intensity) is not None


def filter_options():
    return [
        ("none", tr("pdf.eye_comfort.none")),
        ("warm", tr("pdf.eye_comfort.warm")),
        ("sepia", tr("pdf.eye_comfort.sepia")),
        ("night", tr("pdf.eye_comfort.night")),
    ]