"""Período de prueba de 14 días sin tarjeta."""

import datetime
import logging
from typing import Optional, Tuple

from app_settings import get_setting, set_setting
from license_manager import get_active_license_info

logger = logging.getLogger(__name__)

TRIAL_DAYS = 14


def _parse_dt(value: str) -> Optional[datetime.datetime]:
    try:
        if value.endswith("Z"):
            value = value[:-1]
        return datetime.datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None


def get_trial_started_at() -> Optional[datetime.datetime]:
    raw = get_setting("trial_started_at")
    return _parse_dt(raw) if raw else None


def ensure_trial_started() -> datetime.datetime:
    started = get_trial_started_at()
    if started:
        return started
    started = datetime.datetime.utcnow()
    set_setting("trial_started_at", started.replace(microsecond=0).isoformat() + "Z")
    logger.info("Trial iniciado: %s", started.isoformat())
    return started


def trial_days_remaining() -> int:
    started = get_trial_started_at()
    if not started:
        return TRIAL_DAYS
    elapsed = datetime.datetime.utcnow() - started
    remaining = TRIAL_DAYS - elapsed.days
    return max(0, remaining)


def is_trial_active() -> bool:
    return access_status()[0] == "trial"


def trial_expired() -> bool:
    if get_active_license_info():
        return False
    ensure_trial_started()
    return trial_days_remaining() <= 0


def access_status() -> Tuple[str, int]:
    """Devuelve ('licensed'|'trial'|'expired', días trial restantes)."""
    if get_active_license_info():
        return "licensed", 0
    started = get_trial_started_at()
    if not started:
        return "trial", TRIAL_DAYS
    remaining = trial_days_remaining()
    if remaining > 0:
        return "trial", remaining
    return "expired", 0
