"""Genera el par de claves RSA para firmar licencias LiBooks.

Ejecutar UNA sola vez (o cuando se rote la clave):

    python scripts/generate_keypair.py

Crea:
  keys/license_private.pem  → NUNCA subir a Git (queda en .gitignore)
  keys/license_public.pem   → Sí commitear al repo (la app la usa para verificar)

La clave privada debe guardarse en un lugar seguro fuera del repositorio.
"""

import os
import sys

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEYS_DIR = os.path.join(ROOT, "keys")
PRIVATE_PATH = os.path.join(KEYS_DIR, "license_private.pem")
PUBLIC_PATH = os.path.join(KEYS_DIR, "license_public.pem")


def main():
    if os.path.isfile(PRIVATE_PATH):
        print(f"ERROR: Ya existe {PRIVATE_PATH}")
        print("Elimínala manualmente si quieres generar un nuevo par.")
        sys.exit(1)

    os.makedirs(KEYS_DIR, exist_ok=True)

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    with open(PRIVATE_PATH, "wb") as f:
        f.write(private_pem)
    with open(PUBLIC_PATH, "wb") as f:
        f.write(public_pem)

    print("Par de claves generado:")
    print(f"  Privada (NO commitear): {PRIVATE_PATH}")
    print(f"  Pública  (commitear):   {PUBLIC_PATH}")
    print()
    print("Siguiente paso — genera tu licencia de desarrollo:")
    print('  python scripts/generate_license.py --holder "JUNSY" --perpetual')


if __name__ == "__main__":
    main()
