"""Genera claves de licencia firmadas para clientes de LiBooks.

Requiere ``keys/license_private.pem`` (generada con generate_keypair.py).

Ejemplos:

  # Licencia perpetua
  python scripts/generate_license.py --holder "Juan Pérez" --email "juan@mail.com" --perpetual

  # Licencia por 365 días
  python scripts/generate_license.py --holder "Juan Pérez" --days 365

  # Vinculada al equipo actual del cliente
  python scripts/generate_license.py --holder "Juan Pérez" --bind-machine

  # Vinculada a un ID de equipo concreto (el cliente te lo envía)
  python scripts/generate_license.py --holder "Juan Pérez" --machine-id ABCD1234EF567890
"""

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from license_core import sign_license_payload, get_machine_id  # noqa: E402

PRIVATE_PATH = os.path.join(ROOT, "keys", "license_private.pem")


def main():
    parser = argparse.ArgumentParser(description="Generar licencia LiBooks")
    parser.add_argument("--holder", required=True, help="Nombre del titular")
    parser.add_argument("--email", default="", help="Correo del titular")
    parser.add_argument("--days", type=int, default=None, help="Días de validez")
    parser.add_argument("--perpetual", action="store_true", help="Sin fecha de caducidad")
    parser.add_argument(
        "--bind-machine", action="store_true",
        help="Vincular la licencia al equipo donde se ejecuta este script",
    )
    parser.add_argument(
        "--machine-id", default=None,
        help="ID de equipo concreto (16 caracteres hex)",
    )
    args = parser.parse_args()

    if not os.path.isfile(PRIVATE_PATH):
        print(f"ERROR: No se encontró {PRIVATE_PATH}")
        print("Ejecuta primero: python scripts/generate_keypair.py")
        sys.exit(1)

    if args.perpetual and args.days:
        print("ERROR: Usa --perpetual o --days, no ambos.")
        sys.exit(1)

    payload = {
        "holder": args.holder,
        "email": args.email,
        "issued": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "product": "LiBooks",
        "version": "1",
    }

    if args.perpetual:
        payload["expires"] = None
    elif args.days:
        expiry = datetime.now(timezone.utc) + timedelta(days=args.days)
        payload["expires"] = expiry.strftime("%Y-%m-%dT23:59:59Z")
    else:
        # Por defecto: 1 año.
        expiry = datetime.now(timezone.utc) + timedelta(days=365)
        payload["expires"] = expiry.strftime("%Y-%m-%dT23:59:59Z")

    if args.bind_machine:
        payload["machine_id"] = get_machine_id()
    elif args.machine_id:
        payload["machine_id"] = args.machine_id.upper()

    with open(PRIVATE_PATH, "rb") as f:
        private_pem = f.read()

    license_key = sign_license_payload(payload, private_pem)

    print("=" * 60)
    print("LICENCIA GENERADA — entregar al cliente:")
    print("=" * 60)
    print(license_key)
    print("=" * 60)
    print(f"Titular:  {payload['holder']}")
    if payload.get("email"):
        print(f"Correo:   {payload['email']}")
    print(f"Expira:   {payload.get('expires') or 'Nunca'}")
    if payload.get("machine_id"):
        print(f"Equipo:   {payload['machine_id']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
