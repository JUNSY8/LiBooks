"""Validación criptográfica de licencias LiBooks.

Las claves de licencia son tokens firmados con RSA. La aplicación solo incluye
la **clave pública** (``keys/license_public.pem``); la clave privada permanece
en poder del titular del software y nunca se publica.

Formato de clave: ``LIBOOKS-<payload_b64>.<firma_b64>``

Aunque el código fuente sea público, generar claves válidas sin la clave
privada es computacionalmente inviable. Evitar el control requiere modificar
el binario o el código — el objetivo es elevar ese esfuerzo por encima del
uso casual no autorizado.
"""

import base64
import hashlib
import json
import logging
import platform
import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from paths import resource_path
from i18n import tr

logger = logging.getLogger(__name__)

LICENSE_PREFIX = "LIBOOKS"
_PUBLIC_KEY = None


class LicenseError(Exception):
    """La licencia no es válida o no cumple los requisitos."""


def get_machine_id() -> str:
    """Identificador estable del equipo (para licencias vinculadas a máquina)."""
    raw = f"{uuid.getnode()}-{platform.node()}-{platform.system()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16].upper()


def _load_public_key():
    global _PUBLIC_KEY
    if _PUBLIC_KEY is not None:
        return _PUBLIC_KEY

    key_path = resource_path("keys/license_public.pem")
    try:
        with open(key_path, "rb") as f:
            _PUBLIC_KEY = serialization.load_pem_public_key(f.read())
        return _PUBLIC_KEY
    except FileNotFoundError:
        raise LicenseError(tr("license.error.public_key"))


def _b64url_decode(data: str) -> bytes:
    padding_needed = 4 - len(data) % 4
    if padding_needed != 4:
        data += "=" * padding_needed
    return base64.urlsafe_b64decode(data)


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def parse_license_key(key: str) -> Tuple[dict, bytes]:
    """Separa payload y firma de una clave de licencia."""
    key = key.strip()
    if not key.upper().startswith(LICENSE_PREFIX):
        raise LicenseError(tr("license.error.bad_format"))

    body = key[len(LICENSE_PREFIX):].lstrip("-")
    if "." not in body:
        raise LicenseError(tr("license.error.incomplete"))

    payload_b64, signature_b64 = body.rsplit(".", 1)
    try:
        payload_bytes = _b64url_decode(payload_b64)
        signature = _b64url_decode(signature_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))
    except (ValueError, json.JSONDecodeError) as e:
        raise LicenseError(tr("license.error.decode")) from e

    return payload, signature


def verify_license_key(key: str) -> dict:
    """Verifica firma, caducidad y (opcional) vinculación a máquina.

    Returns:
        dict con los datos de la licencia si es válida.

    Raises:
        LicenseError: si la licena no es válida.
    """
    payload, signature = parse_license_key(key)
    public_key = _load_public_key()

    payload_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()

    try:
        public_key.verify(
            signature,
            payload_bytes,
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
    except InvalidSignature as e:
        raise LicenseError(tr("license.error.authentic")) from e

    # Caducidad.
    expires = payload.get("expires")
    if expires:
        try:
            expiry = datetime.fromisoformat(expires.replace("Z", "+00:00"))
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > expiry:
                raise LicenseError(tr("license.error.expired"))
        except ValueError as e:
            raise LicenseError(tr("license.error.bad_expiry")) from e

    # Vinculación opcional a equipo.
    bound_machine = payload.get("machine_id")
    if bound_machine and bound_machine != get_machine_id():
        raise LicenseError(
            tr("license.error.wrong_machine", machine_id=get_machine_id())
        )

    return payload


def format_license_info(payload: dict) -> str:
    """Texto legible con los datos de una licencia activa."""
    holder = payload.get("holder", "User")
    email = payload.get("email", "")
    expires = payload.get("expires")
    expiry_text = expires[:10] if expires else tr("license.no_expiry")
    lines = [tr("license.holder", holder=holder)]
    if email:
        lines.append(tr("license.email", email=email))
    lines.append(tr("license.valid_until", date=expiry_text))
    if payload.get("machine_id"):
        lines.append(tr("license.machine", machine_id=payload["machine_id"]))
    return "\n".join(lines)


def sign_license_payload(payload: dict, private_key_pem: bytes) -> str:
    """Firma un payload y devuelve la clave de licencia (solo uso del titular)."""
    private_key = serialization.load_pem_private_key(private_key_pem, password=None)
    payload_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    signature = private_key.sign(payload_bytes, padding.PKCS1v15(), hashes.SHA256())
    payload_b64 = _b64url_encode(payload_bytes)
    signature_b64 = _b64url_encode(signature)
    return f"{LICENSE_PREFIX}-{payload_b64}.{signature_b64}"
