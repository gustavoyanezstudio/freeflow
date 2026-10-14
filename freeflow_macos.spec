# -*- mode: python ; coding: utf-8 -*-
"""Receta de PyInstaller para macOS — edición freeflow.

Se compila EN un Mac (PyInstaller no compila para macOS desde Windows).
Desde la carpeta del proyecto:

    python3 -m PyInstaller --noconfirm --clean freeflow_macos.spec

Deja `dist/freeflow.app`. El .dmg lo arma `build_macos.sh` (o el workflow de
GitHub Actions).

La arquitectura se elige con la variable de entorno FF_ARCH:
  universal2 (por defecto) · arm64 · x86_64
Para universal2, el Python y el binario bin/ffmpeg tienen que ser universal2.
"""

import os
from PyInstaller.utils.hooks import collect_all

NOMBRE = "freeflow"
ARQ = os.environ.get("FF_ARCH", "universal2")

datas = [
    (NOMBRE + ".png", "."),   # ícono para el Dock/la ventana (iconphoto)
    ("README_" + NOMBRE + ".txt", "."),   # la ayuda que abre el botón «¿Cómo se usa?»
]
binaries = [("bin/ffmpeg", "ffmpeg")]

hiddenimports = []
tmp = collect_all("yt_dlp")
datas += tmp[0]
binaries += tmp[1]
hiddenimports += tmp[2]

a = Analysis(
    ["recuperador.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="freeflow",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=ARQ,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="freeflow")
app = BUNDLE(
    coll,
    name="freeflow.app",
    icon="freeflow.icns",
    bundle_identifier="com.freeflow.desktop",
    info_plist={
        "CFBundleName": "freeflow",
        "CFBundleDisplayName": "freeflow",
        "CFBundleShortVersionString": "1.0",
        "CFBundleVersion": "1.0",
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": "11.0",
    },
)
