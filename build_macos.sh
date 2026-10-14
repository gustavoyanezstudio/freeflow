#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Compila freeflow y secretflow para macOS y deja los .dmg en dist/.
#
# Genera DOS versiones por edición:
#   freeflow.dmg / secretflow.dmg
#       Universal (Apple Silicon nativa + Intel). Intel: macOS 10.13+.
#       Apple Silicon: macOS 12+.
#   freeflow-legacy.dmg / secretflow-legacy.dmg
#       Solo Intel (x86_64), macOS 10.13+. En Apple Silicon usa Rosetta 2.
#
# Se corre EN un Mac, desde esta carpeta:
#     bash build_macos.sh
#
# Requisitos: macOS con las herramientas de línea de comandos de Xcode
# (sips, iconutil, hdiutil, lipo vienen con el sistema) y Python 3.
# Para la versión universal conviene el instalador universal2 de python.org;
# si tu Python es de una sola arquitectura, el script compila solo la legacy.
# ---------------------------------------------------------------------------
set -euo pipefail
cd "$(dirname "$0")"

PY="${PYTHON:-python3}"
echo "== Python =="
"$PY" -VV

# ¿El Python es universal2? (con lipo vemos si el ejecutable tiene las 2 rodajas)
PUEDE_UNIVERSAL=1
if lipo -archs "$("$PY" -c 'import sys; print(sys.executable)')" 2>/dev/null | grep -q "x86_64.*arm64\|arm64.*x86_64"; then
  echo "Python universal2: sí."
else
  echo "AVISO: tu Python no es universal2; la versión universal se saltea."
  PUEDE_UNIVERSAL=0
fi

echo "== Dependencias =="
"$PY" -m pip install --upgrade pyinstaller yt-dlp >/dev/null

# --- ffmpeg (se incrusta adentro de la app, no hay que instalar nada) ---
# El ffmpeg de imageio ya no arranca en macOS viejo (pide 11/12), así que:
#   bin/ffmpeg        -> universal (x86_64 de evermeet + arm64 de imageio)
#   bin/ffmpeg-legacy -> x86_64 solo (evermeet, macOS 10.13+)
echo "== ffmpeg =="
mkdir -p bin
URL="$(curl -fsSL https://evermeet.cx/ffmpeg/info/ffmpeg/release \
        | "$PY" -c 'import sys,json; print(json.load(sys.stdin)["download"]["zip"]["url"])')"
curl -fsSL -o /tmp/evermeet.zip "$URL"
rm -rf /tmp/evermeet && mkdir -p /tmp/evermeet
unzip -o /tmp/evermeet.zip -d /tmp/evermeet >/dev/null
cp "$(find /tmp/evermeet -type f -name ffmpeg | head -1)" bin/ffmpeg-legacy
chmod +x bin/ffmpeg-legacy

if [ "$PUEDE_UNIVERSAL" = "1" ]; then
  curl -fsSL -o /tmp/ffmpeg-arm64 \
    "https://github.com/imageio/imageio-binaries/raw/master/ffmpeg/ffmpeg-osx-arm64-v7.0"
  chmod +x /tmp/ffmpeg-arm64
  lipo -create -output bin/ffmpeg bin/ffmpeg-legacy /tmp/ffmpeg-arm64
  chmod +x bin/ffmpeg
else
  cp bin/ffmpeg-legacy bin/ffmpeg
fi
echo "universal: $(lipo -archs bin/ffmpeg 2>/dev/null || echo '?')"
echo "legacy:    $(lipo -archs bin/ffmpeg-legacy)"

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

hacer_dmg() { # $1 = app, $2 = archivo destino, $3 = nombre del volumen
  local app="$1" dmg="$2" vol="$3" stage="dist/dmg_$app"
  rm -rf "$stage" "$dmg"; mkdir -p "$stage"
  cp -R "dist/$app.app" "$stage/"
  cp "README_$app.txt" "$stage/"
  hdiutil create -volname "$vol" -srcfolder "$stage" -ov -format UDZO "$dmg"
  rm -rf "$stage"
}

mkdir -p dist
rm -f dist/*.dmg

# --- versión universal ---
if [ "$PUEDE_UNIVERSAL" = "1" ]; then
  echo "== PyInstaller (universal2) =="
  for ed in freeflow secretflow; do
    FF_ARCH=universal2 "$PY" -m PyInstaller --noconfirm --clean "${ed}_macos.spec"
  done
  bash scripts/verificar_minos.sh "universal2"
  for ed in freeflow secretflow; do
    hacer_dmg "$ed" "dist/$ed.dmg" "$ed"
  done
  rm -rf dist/freeflow.app dist/secretflow.app
fi

# --- versión legacy (solo Intel x86_64) ---
if lipo -archs "$("$PY" -c 'import sys; print(sys.executable)')" 2>/dev/null | grep -q x86_64; then
  echo "== PyInstaller (legacy, Intel) =="
  cp bin/ffmpeg-legacy bin/ffmpeg
  for ed in freeflow secretflow; do
    FF_ARCH=x86_64 FF_ETIQUETA=legacy "$PY" -m PyInstaller --noconfirm --clean "${ed}_macos.spec"
  done
  bash scripts/verificar_minos.sh "legacy"
  for ed in freeflow secretflow; do
    hacer_dmg "$ed legacy" "dist/$ed-legacy.dmg" "$ed legacy"
  done
else
  echo "AVISO: tu Python no tiene la rodaja x86_64; no se generó la versión legacy."
fi

echo "== Listo =="
ls -lh dist/*.dmg
