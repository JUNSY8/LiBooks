# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for macOS (.app bundle)."""

import os
import sys

sys.path.insert(0, os.path.abspath("."))
from version import APP_VERSION

block_cipher = None

_assets = []
if os.path.isdir("locales"):
    _assets.append(("locales", "locales"))
if os.path.isdir("assets"):
    _assets.append(("assets", "assets"))
if os.path.isdir("keys"):
    _assets.append(("keys", "keys"))
if os.path.isfile("alembic.ini"):
    _assets.append(("alembic.ini", "."))
if os.path.isdir("alembic"):
    _assets.append(("alembic", "alembic"))

_icon = "assets/icons/app_icon.icns"
if not os.path.isfile(_icon):
    _icon = None

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=_assets,
    hiddenimports=["fitz", "cryptography", "alembic", "logging.config"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tensorflow", "torch", "keras", "matplotlib", "pandas", "numpy",
        "scipy", "sklearn", "IPython", "jupyter", "notebook", "zmq",
        "pytest", "setuptools", "pip", "wheel",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="LiBooks",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=os.environ.get("LIBOOKS_CODESIGN_IDENTITY"),
    entitlements_file="scripts/entitlements.plist"
    if os.path.isfile("scripts/entitlements.plist")
    else None,
    icon=_icon,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="LiBooks",
)

app = BUNDLE(
    coll,
    name="LiBooks.app",
    icon=_icon,
    bundle_identifier="com.junsy.libooks",
    info_plist={
        "CFBundleName": "LiBooks",
        "CFBundleDisplayName": "LiBooks",
        "CFBundleShortVersionString": APP_VERSION,
        "CFBundleVersion": APP_VERSION,
        "NSHighResolutionCapable": True,
        "NSPrincipalClass": "NSApplication",
        "LSMinimumSystemVersion": "11.0",
    },
)