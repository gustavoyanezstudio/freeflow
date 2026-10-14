#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Muestra la arquitectura y la versión MÍNIMA de macOS ("minos") de cada
# binario que hay dentro de las .app de dist/. Sirve para comprobar que la app
# realmente arranca en Macs viejos (p. ej. x86_64 = 10.13).
#
# Se corre EN un Mac, desde la raíz del proyecto:
#     bash scripts/verificar_minos.sh <etiqueta>
# ---------------------------------------------------------------------------
set -euo pipefail

etiqueta="${1:-app}"

minos_of() { # $1 = binario, $2 = arquitectura
  otool -arch "$2" -l "$1" 2>/dev/null | awk '
    /LC_BUILD_VERSION/{b=1} b&&/minos/{print $2; exit}
    /LC_VERSION_MIN_MACOSX/{v=1} v&&/^ *version/{print $2; exit}'
}

x86="0.0"
arm="0.0"
shopt -s nullglob
for appdir in dist/*.app; do
  echo "== [$etiqueta] $appdir =="
  while IFS= read -r f; do
    archs="$(lipo -archs "$f" 2>/dev/null)" || continue
    [ -n "$archs" ] || continue
    line="  ${f#dist/} [$(echo $archs | tr ' ' ',')]"
    for a in $archs; do
      m="$(minos_of "$f" "$a")" || true
      [ -n "$m" ] || continue
      line="$line ${a}=${m}"
      if [ "$a" = "x86_64" ]; then
        x86="$(printf '%s\n%s\n' "$x86" "$m" | sort -V | tail -1)"
      fi
      if [ "$a" = "arm64" ]; then
        arm="$(printf '%s\n%s\n' "$arm" "$m" | sort -V | tail -1)"
      fi
    done
    echo "$line"
  done < <(find "$appdir" -type f)
  echo "  Info.plist LSMinimumSystemVersion: $(/usr/libexec/PlistBuddy -c 'Print :LSMinimumSystemVersion' "$appdir/Contents/Info.plist")"
done
echo "== [$etiqueta] PEOR minos: x86_64=macOS $x86  arm64=macOS $arm =="
