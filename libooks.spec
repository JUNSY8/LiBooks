# -*- mode: python ; coding: utf-8 -*-
"""Especificación de PyInstaller para empaquetar LiBooks.

Uso:
    pyinstaller libooks.spec

Genera un ejecutable único en dist/. La base de datos, los PDFs y los logs
NO se incluyen en el ejecutable: se crean en el directorio de datos del
usuario la primera vez que se ejecuta la aplicación.
"""

import os

block_cipher = None

# Incluir recursos empaquetados si existen.
_assets = []
if os.path.isdir('locales'):
    _assets.append(('locales', 'locales'))
if os.path.isdir('assets'):
    _assets.append(('assets', 'assets'))
if os.path.isdir('keys'):
    _assets.append(('keys', 'keys'))
if os.path.isfile('alembic.ini'):
    _assets.append(('alembic.ini', '.'))
if os.path.isdir('alembic'):
    _assets.append(('alembic', 'alembic'))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=_assets,
    hiddenimports=['fitz', 'cryptography', 'alembic', 'logging.config'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tensorflow', 'torch', 'keras', 'matplotlib', 'pandas', 'numpy',
        'scipy', 'sklearn', 'IPython', 'jupyter', 'notebook', 'zmq',
        'pytest', 'setuptools', 'pip', 'wheel',
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
    a.binaries,
    a.datas,
    [],
    name='LiBooks',
    debug=False,
    icon='assets/icons/app_icon.ico',
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
