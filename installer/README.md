# LiBooks Windows Installer (Signed)

## Requirements

| Tool | Purpose |
|------|---------|
| **Python 3.9+** | Build the executable with PyInstaller |
| **Windows SDK** | `signtool.exe` (Signing Tools for Desktop Apps) |
| **Inno Setup 6** | Produce `LiBooks-Setup-x.x.x.exe` |
| **Authenticode certificate** | Code signing (`.pfx` file or Windows certificate store) |

Install Inno Setup 6 via [the official download](https://jrsoftware.org/isdl.php) or:

```powershell
winget install JRSoftware.InnoSetup
```

## Signing certificate

For Windows and SmartScreen to trust the installer you need an **Authenticode** certificate from a recognized CA (Sectigo, DigiCert, SSL.com, etc.).

| Type | Typical use |
|------|-------------|
| **OV Code Signing** | Standard release; SmartScreen reputation builds over time |
| **EV Code Signing** | USB token / HSM; often faster SmartScreen trust |

**Never commit** the `.pfx` file or its password to the repository.

### Configure credentials (PowerShell session)

```powershell
# Option A: .pfx file (recommended for CI with secrets)
$env:LIBOOKS_SIGN_PFX = "C:\certs\your-codesign.pfx"
$env:LIBOOKS_SIGN_PASSWORD = "your-secure-password"

# Option B: certificate already in the Windows store (e.g. EV token)
$env:LIBOOKS_SIGN_THUMB = "ABCDEF1234567890..."   # SHA1 thumbprint
```

## Build the signed installer

From the project root:

```powershell
.\scripts\build_installer.ps1
```

This runs, in order:

1. `build_windows.ps1` — creates an isolated `.build-venv`, installs dependencies, runs PyInstaller → `dist\LiBooks.exe`
2. Signs `LiBooks.exe` with `signtool`
3. Inno Setup — `dist\LiBooks-Setup-{version}.exe`
4. Signs the installer

### Local testing without a certificate

```powershell
.\scripts\build_installer.ps1 -SkipSign
```

### Reuse an already-built executable

```powershell
.\scripts\build_installer.ps1 -SkipBuild -SkipSign
```

## Sign a file manually

```powershell
$env:LIBOOKS_SIGN_PFX = "C:\certs\codesign.pfx"
$env:LIBOOKS_SIGN_PASSWORD = "..."
.\scripts\code_sign.ps1 -FilePath dist\LiBooks.exe
```

## Verify the signature

```powershell
signtool verify /pa /v dist\LiBooks-Setup-1.0.0.exe
```

Or right-click the file → **Properties** → **Digital Signatures**.

## Self-signed certificate (dev only)

```powershell
.\scripts\create_self_signed_cert.ps1
# Set LIBOOKS_SIGN_* as printed, then:
.\scripts\build_installer.ps1
```

SmartScreen will still warn on self-signed builds.

## CI/CD (GitHub Actions)

Workflows in `.github/workflows/`:

| Workflow | Trigger | What it does |
|----------|---------|--------------|
| **CI** (`ci.yml`) | Push / PR to `main` | Smoke test (Ubuntu) + build `LiBooks.exe` (Windows) + `LiBooks.app` (macOS). Artifacts kept 7 days. |
| **Release** (`release.yml`) | Tag `v*` (e.g. `v1.0.1`) | Builds Windows installer + macOS ZIP and publishes a GitHub Release. |

### Secrets (optional, for signed Windows releases)

Store in repository **Settings → Secrets and variables → Actions**:

| Secret | Value |
|--------|--------|
| `LIBOOKS_SIGN_PFX` | Base64-encoded `.pfx` file |
| `LIBOOKS_SIGN_PASSWORD` | PFX password |

PowerShell to encode the PFX:

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("C:\path\to\codesign.pfx"))
```

If secrets are missing, the release workflow builds an **unsigned** installer (`-SkipSign`).

### Create a release

```bash
git tag v1.0.1
git push origin v1.0.1
```

The **Release** workflow uploads `LiBooks-Setup-x.x.x.exe`, `LiBooks-x.x.x-macOS-arm64.zip` (Apple Silicon), and `LiBooks-x.x.x-macOS-intel.zip` (Intel) to the GitHub Release page.

### Local smoke test (same as CI)

```bash
pip install -r requirements.txt
python scripts/ci_smoke_test.py
```

## Notes

- Installer version is read from `version.py` (`APP_VERSION`).
- The EULA shown in the setup wizard is the root `LICENSE` file.
- App icons are generated from `assets/icons/app_icon_512.png` during the build (`scripts/generate_app_icons.py`).
- Alembic migrations are bundled inside the executable so the database initializes correctly on first launch.
- After the first signed release, SmartScreen may still warn until reputation is established; EV signing shortens that period.
