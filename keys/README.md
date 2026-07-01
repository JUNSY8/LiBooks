# License keys

## Contents of this folder

| File | In Git? | Description |
|------|---------|-------------|
| `license_public.pem` | **Yes** | RSA public key. The app uses it to verify licenses. |
| `license_private.pem` | **No** | RSA private key. Only the software owner holds this. |

## Initial setup (owner only)

```bash
pip install cryptography
python scripts/generate_keypair.py
python scripts/generate_license.py --holder "YOUR NAME" --perpetual
```

1. `generate_keypair.py` creates both keys.
2. Commit **only** `license_public.pem`.
3. Store `license_private.pem` in a secure location **outside the repository** (keep a backup).
4. Use `generate_license.py` to issue keys for each customer.

## Security

- The repository can be **public**: without the private key, no one can generate valid licenses.
- Bypassing verification requires modifying the code or the executable; the legal license (EULA) complements this technical protection.
