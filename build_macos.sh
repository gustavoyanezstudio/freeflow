#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Compila las DOS ediciones para macOS y deja los .dmg en dist/.
#
# Se corre EN un Mac, desde esta carpeta:
#     bash build_macos.sh
#
# Requisitos: macOS con las herramientas de línea de comandos de Xcode
# (sips, iconutil, hdiutil vienen con el sistema) y Python 3.
#
# Para un .app universal (Apple Silicon + Intel) hay que usar un Python
# universal2 (el instalador de python.org "macOS 64-bit universal2"). Si tu
# Python es de una sola arquitectura, el script compila igual pero avisa:
# la app va a correr sólo en tu tipo de Mac.
# ---------------------------------------------------------------------------
set -euo pipefail
cd "$(dirname "$0")"

PY="${PYTHON:-python3}"
echo "== Python =="
"$PY" -VV

ARQ="$( "$PY" -c 'import platform,sys; print("universal2" if sys.maxsize>2**32 and platform.machine()=="arm64" else platform.machine())' )"
# ¿Es un Python universal2? (con lipo podemos ver si tiene las dos rodajas)
if lipo -archs "$("$PY" -c 'import sys; print(sys.executable)')" 2>/dev/null | grep -q "x86_64.*arm64\|arm64.*x86_64"; then
  ARQ="universal2"
else
  echo "AVISO: tu Python no es universal2 (es $ARQ)."
  echo "       La app correrá sólo en Macs $ARQ. Para una app universal,"
  echo "       instalá el Python universal2 de python.org y volvé a correr."
fi
echo "Arquitectura de la app: $ARQ"
export FF_ARCH="$ARQ"

echo "== Dependencias =="
"$PY" -m pip install --upgrade pyinstaller yt-dlp >/dev/null

# --- ffmpeg (se incrusta adentro de la app, no hay que instalar nada) ---
if [ ! -f bin/ffmpeg ]; then
  echo "== ffmpeg =="
  "$PY" -m pip install imageio-ffmpeg >/dev/null
  FF="$( "$PY" -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())' )"
  mkdir -p bin
  cp "$FF" bin/ffmpeg
  chmod +x bin/ffmpeg
fi
echo "ffmpeg: $( bin/ffmpeg -version 2>/dev/null | head -1 || true )"

# --- ícono .icns a partir del .png de cada edición ---
hacer_icns() {
  local src="$1" out="$2" d="icon.iconset"
  rm -rf "$d"; mkdir -p "$d"
  for n in 16 32 128 256 512; do
    sips -z "$n" "$n" "$src" --out "$d/icon_${n}x${n}.png" >/dev/null
    sips -z "$((n*2))" "$((n*2))" "$src" --out "$d/icon_${n}x${n}@2x.png" >/dev/null
  done
  iconutil -c icns "$d" -o "$out"
  rm -rf "$d"
}
echo "== Íconos =="
hacer_icns freeflow.png   freeflow.icns
hacer_icns secretflow.png secretflow.icns

# --- compilar cada edición ---
for ed in freeflow secretflow; do
  echo "== PyInstaller: $ed =="
  "$PY" -m PyInstaller --noconfirm --clean "${ed}_macos.spec"
done

# --- armar los .dmg (la app + el README suelto) ---
hacer_dmg() {
  local app="$1" stage="dist/dmg_$1"
  rm -rf "$stage" "dist/$app.dmg"
  mkdir -p "$stage"
  cp -R "dist/$app.app" "$stage/"
  cp "README_$app.txt" "$stage/"
  hdiutil create -volname "$app" -srcfolder "$stage" -ov -format UDZO "dist/$app.dmg" >/dev/null
  rm -rf "$stage"
}
echo "== DMG =="
hacer_dmg freeflow
hacer_dmg secretflow

echo
echo "Listo. Quedó en dist/:"
ls -lh dist/*.dmg
