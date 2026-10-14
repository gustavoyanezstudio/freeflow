# -*- coding: utf-8 -*-
"""
freeflow
========

Busca sets/audios con los términos que escribas en SoundCloud, YouTube,
Mixcloud y Bandcamp, los lista con su formato, calidad y peso, te deja elegir
cuáles querés y los descarga en la mejor calidad disponible, pudiendo convertir
el video a audio.

Motor: yt-dlp.   Búsqueda en Mixcloud/Bandcamp: sus API públicas.   Conversión:
ffmpeg.  El botón «Descargar original» baja el archivo tal cual viene (WAV/FLAC
o la mejor versión) sin recomprimir, por si querés conservar la mejor versión
además del MP3.

La ventana es lo único interactivo; buscar, analizar y descargar corren en
segundo plano para que la interfaz no se congele.
"""

import glob
import html
import concurrent.futures
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import queue
import urllib.parse
import urllib.request
import zipfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

import yt_dlp

# --------------------------------------------------------------------------
# Edición: "freeflow" (general, para compartir) o "secretflow" (Tectónica
# Radio). Se detecta por el nombre del ejecutable (freeflow.exe /
# secretflow.exe). Si se corre desde el código, se puede forzar con la
# variable de entorno FREEFLOW_EDICION.
# --------------------------------------------------------------------------
def _detectar_edicion():
    nombre = os.path.basename(sys.executable or "").lower()
    if "secretflow" in nombre:
        return "secretflow"
    if "freeflow" in nombre:
        return "freeflow"
    return (os.environ.get("FREEFLOW_EDICION") or "freeflow").strip().lower()


MARCAS = {
    "freeflow": {
        "app": "freeflow",
        "descargas": "Freeflow Downloads",
        "cfg": "freeflow",
        "icono": "freeflow.ico",
        "png": "freeflow.png",
        "btn": "freeflow_btn.png",
        "readme": "README_freeflow.txt",
        "terminos": "",
    },
    "secretflow": {
        "app": "secretflow",
        "descargas": "Secretflow Downloads",
        "cfg": "secretflow",
        "icono": "secretflow.ico",
        "png": "secretflow.png",
        "btn": "secretflow_btn.png",
        "readme": "README_secretflow.txt",
        "terminos": "tectonica radio\ntectonica radio set\ntectonicaradio",
    },
}

EDICION = _detectar_edicion()
if EDICION not in MARCAS:
    EDICION = "freeflow"
MARCA = MARCAS[EDICION]

APP = MARCA["app"]
VERSION = "1.0.1"

TERMINOS_DEF = MARCA["terminos"]

# --------------------------------------------------------------------------
# Paleta de cada edición. Sólo cambia el color de fondo, los acentos y la
# tipografía: la disposición y los tamaños de letra no se tocan.
#   freeflow   -> «Menta suave": fondo claro y acentos con el verde de la pluma.
#   secretflow -> "Terminal verde": oscuro, verde fósforo y monoespaciada.
# --------------------------------------------------------------------------
TEMAS = {
    "freeflow": {
        "fuente": ("Segoe UI", 9),
        "bg": "#eef6f3", "panel": "#ffffff", "line": "#c6ddd7", "line2": "#dcebe7",
        "fg": "#12332c", "mute": "#5c7a73",
        "accent": "#14a886", "onc": "#063a37",
        "head": "#3f6f65", "th": "#e0efeb", "sel": "#c6e6dd", "selfg": "#063a37",
        "logbg": "#fbfefd", "logfg": "#2f534b", "bar": "#e0eeea",
        "chkline": "#8fbcb1", "onmark": "#ffffff",
    },
    "secretflow": {
        "fuente": ("Consolas", 9),
        "bg": "#0f1a13", "panel": "#0b130e", "line": "#2a4632", "line2": "#1e3326",
        "fg": "#d7efe0", "mute": "#7fa88a",
        "accent": "#4fd08a", "onc": "#04140f",
        "head": "#8fb79a", "th": "#13251a", "sel": "#1d3a29", "selfg": "#dff5e6",
        "logbg": "#0a120d", "logfg": "#8fe0a8", "bar": "#0d1811",
        "chkline": "#3d6b4d", "onmark": "#04140f",
    },
}

TEMA = TEMAS[EDICION]


def _fuente_mono():
    """Monoespaciada para mostrar el README dentro de la app: así la cabecera
    de arte ASCII no se desarma. Se usa la que trae cada sistema."""
    if sys.platform == "darwin":
        return ("Menlo", 11)
    if os.name == "nt":
        return ("Consolas", 11)
    return ("DejaVu Sans Mono", 11)

FUENTES = ("SoundCloud", "YouTube", "Mixcloud", "Bandcamp")

# Cuántos resultados se analizan a la vez (formato/calidad/peso). Paralelizarlo
# hace que el dato aparezca mucho antes; el número es a la vez un tope para no
# comerse un "429 Too Many Requests" de SoundCloud/YouTube. Medido con datos
# reales: 16 es el mejor punto (más hilos ya frenan por límites de las fuentes).
MAX_ANALISIS = 16

# Búsquedas simultáneas (término × fuente). Cada una es una sola petición.
MAX_BUSQUEDAS = 6

# Modo especial del botón «Descargar original»: baja el mejor archivo tal cual
# viene, sin recomprimir y sin tope de 320 (WAV/FLAC si existen).
FORMATO_ORIGINAL = "ORIGINAL"

# Uniforma todo a MP3 320 y deja anotado en el nombre el formato/bitrate de
# origen (p. ej. «... [id] (origen MP3 128 kbps).mp3»). Pensado para canciones.
FORMATO_TAG = "320 + tag de origen (para canciones)"

FORMATOS = [
    "Mejor calidad (hasta 320 kbps, sin recomprimir)",
    FORMATO_TAG,
    "MP3 320 kbps (convierte)",
    "M4A / AAC (convierte)",
    "WAV (sin comprimir)",
    "Video MP4 (mejor calidad)",
]
FORMATOS_CON_FFMPEG = {
    FORMATO_TAG,
    "MP3 320 kbps (convierte)",
    "M4A / AAC (convierte)",
    "WAV (sin comprimir)",
}

# Filtro de calidad: el mejor audio disponible pero sin pasar de 320 kbps.
# Si por algún motivo no hay ninguno por debajo, cae al mejor posible.
FORMATO_AUDIO = "bestaudio[abr<=320]/bestaudio/best"

# Navegador "de mentira" para las búsquedas que no pasan por yt-dlp (Mixcloud).
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122 Safari/537.36"
)

# Bandcamp devuelve la página vieja (con los datos del ítem: precio mínimo,
# página de descarga gratuita) sólo a ciertos UA. Con un Chrome más nuevo sí
# la sirve; se usa únicamente para leer si un ítem es «name your price».
UA_HTML = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# Prefijos de búsqueda de yt-dlp. Mixcloud y Bandcamp no tienen: van por su API.
PREFIJOS = {
    "SoundCloud": "scsearch",
    "YouTube": "ytsearch",
}

BANDCAMP_API = "https://bandcamp.com/api/bcsearch_public_api/1/autocomplete_elastic"


def elegir_audio(meta):
    """Elige el mejor audio disponible y dice si hay que bajarlo de calidad.

    Prioriza sin pérdida (WAV/FLAC) si existe; si no, el de mayor bitrate.
    'excede' = True cuando la fuente supera los 320 kbps o es sin pérdida.
    """
    formatos = [
        f
        for f in (meta.get("formats") or [])
        if f.get("vcodec") in (None, "none") and f.get("acodec") not in (None, "none")
    ]
    if not formatos:
        return None

    def es_sin_perdida(f):
        ext = (f.get("ext") or "").lower()
        acodec = (f.get("acodec") or "").lower()
        return ext in ("wav", "flac", "alac", "aiff", "aif", "caf") or acodec.startswith("pcm")

    sin_perdida = [f for f in formatos if es_sin_perdida(f)]
    if sin_perdida:
        # Entre formatos sin pérdida el audio es idéntico: se prefiere el más
        # liviano (FLAC/ALAC comprimen; WAV/AIFF no). Ahorra espacio en el server.
        pref = {"flac": 0, "m4a": 1, "alac": 1, "aif": 2, "aiff": 2, "wav": 3}
        mejor = min(
            sin_perdida,
            key=lambda f: (
                pref.get((f.get("ext") or "").lower(), 9),
                -(f.get("tbr") or f.get("abr") or 0),
            ),
        )
    else:
        mejor = max(formatos, key=lambda f: f.get("abr") or f.get("tbr") or 0)

    ext = (mejor.get("ext") or "").lower()
    acodec = (mejor.get("acodec") or "").lower()
    abr = mejor.get("abr") or mejor.get("tbr") or 0
    lossless = es_sin_perdida(mejor)
    return {
        "format_id": mejor.get("format_id"),
        "ext": ext,
        "abr": abr,
        "acodec": acodec,
        "lossless": lossless,
        "excede": lossless or abr > 320,
    }


def tam_formato(f, dur):
    """Tamaño estimado (bytes) de un formato: el real si lo trae, si no por bitrate."""
    if not f:
        return None
    n = f.get("filesize") or f.get("filesize_approx")
    if n:
        return n
    tbr = f.get("abr") or f.get("tbr") or 0
    if tbr and dur:
        return tbr * 1000.0 / 8.0 * dur
    return None


def estimar_peso(meta, formato):
    """Cuánto pesará el archivo final, según el formato elegido (bytes)."""
    dur = meta.get("duration") or 0
    formatos = meta.get("formats") or []
    decision = elegir_audio(meta)

    def buscar(fid):
        for f in formatos:
            if f.get("format_id") == fid:
                return f
        return None

    # Formatos con tamaño previsible por su bitrate objetivo.
    if formato == "WAV (sin comprimir)":
        return dur * 176400 if dur else None
    if formato in (FORMATO_TAG, "MP3 320 kbps (convierte)"):
        return dur * 40000 if dur else None
    if formato == "Video MP4 (mejor calidad)":
        vids = [f for f in formatos if f.get("vcodec") not in (None, "none")]
        auds = [
            f
            for f in formatos
            if f.get("vcodec") in (None, "none") and f.get("acodec") not in (None, "none")
        ]
        if not vids:
            return None
        mejor_v = max(vids, key=lambda f: (f.get("height") or 0, f.get("tbr") or 0))
        mejor_a = max(auds, key=lambda f: f.get("abr") or f.get("tbr") or 0) if auds else None
        total = (tam_formato(mejor_v, dur) or 0) + (tam_formato(mejor_a, dur) or 0)
        return total or None

    # Audio: según lo que se baje (o cómo se recomprima).
    fuente = buscar(decision["format_id"]) if decision else None
    tam = tam_formato(fuente, dur)
    if formato == "Mejor calidad (hasta 320 kbps, sin recomprimir)":
        if decision and decision["excede"]:
            return dur * 40000 if dur else tam
        return tam
    # M4A / AAC: si la fuente es sin pérdida, se estima AAC (~160 kbps).
    if decision and decision.get("lossless"):
        return dur * 20000 if dur else tam
    return tam


# Tipo de audio típico de cada fuente. Sirve para mostrar el formato y un peso
# aproximado apenas aparece cada resultado, mientras el análisis real corre en
# segundo plano y después los reemplaza por los valores exactos.
TIPO_FUENTE = {
    "SoundCloud": ("M4A", 160),
    "YouTube": ("WEBM", 130),
    "Mixcloud": ("MP3", 128),
    "Bandcamp": ("MP3", 128),
}


def estimar_fila(fuente, dur, formato):
    """(formato, calidad, bytes) aproximados de una fila, según la fuente y la
    duración. Es sólo para mostrar algo al instante; el análisis lo pisa."""
    dur = dur or 0
    if not dur:
        return (None, None, None)
    if formato == "WAV (sin comprimir)":
        return ("WAV", "PCM", dur * 176400)
    if formato in (FORMATO_TAG, "MP3 320 kbps (convierte)"):
        return ("MP3", "320 kbps", dur * 40000)
    if formato == "Video MP4 (mejor calidad)":
        return ("MP4", "video", None)
    ext, abr = TIPO_FUENTE.get(fuente, (None, None))
    if not ext:
        return (None, None, None)
    return (ext, "%d kbps" % abr, dur * (abr * 1000.0 / 8.0))


def detalle_formato(meta, formato):
    """(formato, calidad) para mostrar en la lista, según el modo elegido."""
    formatos = meta.get("formats") or []
    if formato == "Video MP4 (mejor calidad)":
        vids = [f for f in formatos if f.get("vcodec") not in (None, "none")]
        if not vids:
            return ("—", "—")
        v = max(vids, key=lambda f: (f.get("height") or 0, f.get("tbr") or 0))
        h = v.get("height")
        return ((v.get("ext") or "?").upper(), ("%dp" % h) if h else "video")
    d = elegir_audio(meta)
    if not d:
        return ("—", "—")
    ext = (d.get("ext") or "?").upper()
    if d.get("lossless"):
        cal = "sin pérdida"
    elif d.get("abr"):
        cal = "%d kbps" % d["abr"]
    else:
        cal = "?"
    return (ext, cal)


# --------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------
def carpeta_app():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _ruta_recurso(nombre):
    base = getattr(sys, "_MEIPASS", None) or carpeta_app()
    for cand in (
        os.path.join(base, nombre),
        os.path.join(base, "recursos", nombre),
    ):
        if os.path.isfile(cand):
            return cand
    return None


def _ruta_icono():
    return _ruta_recurso(MARCA["icono"])


def abrir_ruta(ruta):
    """Abre una carpeta o un archivo con la aplicación del sistema (Explorer,
    Finder o el visor de turno). Funciona en Windows, Mac y Linux."""
    try:
        if sys.platform == "darwin":
            subprocess.Popen(["open", ruta])
        elif os.name == "nt":
            os.startfile(ruta)  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", ruta])
    except Exception:
        pass


def _poner_icono(ventana):
    """Pone el ícono de la edición. El PNG sirve en Windows, Mac y Linux; el
    .ico queda como respaldo para Windows."""
    ruta_png = _ruta_recurso(MARCA["png"])
    if ruta_png:
        try:
            img = tk.PhotoImage(master=ventana, file=ruta_png)
            ventana.iconphoto(True, img)
            ventana._icono_ref = img  # mantener viva la referencia
            return
        except Exception:
            pass
    ruta = _ruta_icono()
    if ruta:
        try:
            ventana.iconbitmap(ruta)
        except Exception:
            pass


def crear_iconos_fila(master, t):
    """Dibuja los íconos de la primera columna de la tabla: el cuadradito de
    selección (vacío / marcado) y el botón de descarga de los temas gratis.

    Se dibujan a mano (sin Pillow) para que el cuadradito y el botón tengan un
    tamaño fijo e independiente de la letra de la tabla, y para que el fondo
    quede transparente (así toma el color de la fila, seleccionada o no)."""
    CHK = 18                        # lado del cuadradito
    GAP = 5
    BTN_W, BTN_H = 18, 16
    W = 2 + CHK + GAP + BTN_W + 2   # ancho total del ícono (45)
    H = 20
    TOP = (H - CHK) // 2            # y del cuadradito
    BX = 2 + CHK + GAP              # x del botón
    BY = (H - BTN_H) // 2

    def rect(img, x0, y0, x1, y1, color):
        if x1 <= x0 or y1 <= y0:
            return
        img.put(color, to=(x0, y0, x1 - 1, y1 - 1))

    def linea(img, x0, y0, x1, y1, color, g=2):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for k in range(n + 1):
            x = round(x0 + (x1 - x0) * k / n)
            y = round(y0 + (y1 - y0) * k / n)
            rect(img, x, y, x + g, y + g, color)

    def cuadradito(img, marcado):
        x0, y0 = 2, TOP
        if marcado:
            rect(img, x0, y0, x0 + CHK, y0 + CHK, t["accent"])
            linea(img, x0 + 5, y0 + 9, x0 + 8, y0 + 12, t["onmark"], 2)
            linea(img, x0 + 8, y0 + 12, x0 + 13, y0 + 5, t["onmark"], 2)
        else:
            b = t["chkline"]
            rect(img, x0, y0, x0 + CHK, y0 + 2, b)              # borde arriba
            rect(img, x0, y0 + CHK - 2, x0 + CHK, y0 + CHK, b)  # borde abajo
            rect(img, x0, y0, x0 + 2, y0 + CHK, b)              # borde izq.
            rect(img, x0 + CHK - 2, y0, x0 + CHK, y0 + CHK, b)  # borde der.

    def boton(img):
        acc = t["accent"]
        r = 2
        for y in range(BTN_H):                     # rectángulo con esquinas suaves
            if y < r:
                dx = r - y
            elif y >= BTN_H - r:
                dx = r - (BTN_H - 1 - y)
            else:
                dx = 0
            rect(img, BX + dx, BY + y, BX + BTN_W - dx, BY + y + 1, acc)
        cx = BX + BTN_W // 2
        rect(img, cx - 1, BY + 4, cx + 1, BY + 11, t["onmark"])        # tallo
        for i in range(5):                                            # punta ⬇
            y = BY + 10 + i
            media = 4 - i
            rect(img, cx - media, y, cx + media + 1, y + 1, t["onmark"])

    ico = {}
    for clave, marcado, con_boton in (
        ("off", False, False),
        ("on", True, False),
        ("off_btn", False, True),
        ("on_btn", True, True),
    ):
        img = tk.PhotoImage(master=master, width=W, height=H)
        cuadradito(img, marcado)
        if con_boton:
            boton(img)
        ico[clave] = img
    return ico


def hallar_ffmpeg():
    # Nombre del ejecutable de ffmpeg según el sistema (el .exe es sólo Windows).
    nombre = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"

    # 1) Empaquetado DENTRO del ejecutable (modo portable: no hace falta instalar
    #    ffmpeg). PyInstaller deja los binarios en sys._MEIPASS.
    empaquetado = getattr(sys, "_MEIPASS", None)
    if empaquetado:
        for cand in (os.path.join(empaquetado, "ffmpeg"), empaquetado):
            if os.path.isfile(os.path.join(cand, nombre)):
                return cand
    # 2) Junto al ejecutable/programa (por si se prefiere un ffmpeg externo).
    base = carpeta_app()
    for cand in (os.path.join(base, "ffmpeg"), os.path.join(base, "ffmpeg", "bin"), base):
        if os.path.isfile(os.path.join(cand, nombre)):
            return cand
    # 3) En el PATH.
    exe = shutil.which("ffmpeg")
    if exe:
        return os.path.dirname(exe)
    # 4) Ubicaciones típicas de Windows (winget, C:\ffmpeg).
    if os.name == "nt":
        local = os.environ.get("LOCALAPPDATA", "")
        patrones = [
            os.path.join(local, "Microsoft", "WinGet", "Packages", "Gyan.FFmpeg*", "**", "bin", "ffmpeg.exe"),
            os.path.join(local, "Microsoft", "WinGet", "Links", "ffmpeg.exe"),
            r"C:\ffmpeg\bin\ffmpeg.exe",
        ]
        for pat in patrones:
            for hit in glob.glob(pat, recursive=True):
                return os.path.dirname(hit)
    return None


def carpeta_datos():
    """Carpeta de configuración/caché de esta edición (freeflow o secretflow)."""
    if sys.platform == "darwin":
        base = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    else:
        base = os.environ.get("LOCALAPPDATA") or carpeta_app()
    d = os.path.join(base, MARCA["cfg"])
    try:
        os.makedirs(d, exist_ok=True)
    except OSError:
        return None
    return d


def ruta_config():
    d = carpeta_datos()
    return os.path.join(d, "config.json") if d else None


def carpeta_cache():
    """Caché de yt-dlp (jugadores, manifests): acelera los análisis repetidos."""
    d = carpeta_datos()
    if not d:
        return None
    c = os.path.join(d, "cache")
    try:
        os.makedirs(c, exist_ok=True)
    except OSError:
        return None
    return c


_ytdl_local = threading.local()


_meta_mem = {}
_meta_mem_lock = threading.Lock()


def extraer_meta(url):
    """Formatos y duración de una URL, con una instancia de yt-dlp reutilizada
    por hilo. Pensada para llamarse en paralelo (una por hilo).

    Los resultados quedan en memoria: si la misma URL se vuelve a pedir (otra
    búsqueda, o el mismo set repetido en dos términos), se responde al instante.
    """
    if not url:
        return None
    with _meta_mem_lock:
        if url in _meta_mem:
            return _meta_mem[url]
    ydl = getattr(_ytdl_local, "ydl", None)
    if ydl is None:
        op = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "socket_timeout": 15,  # evita que una conexión colgada frene el análisis
        }
        cache = carpeta_cache()
        if cache:
            op["cachedir"] = cache
        ydl = yt_dlp.YoutubeDL(op)
        _ytdl_local.ydl = ydl
    meta = ydl.extract_info(url, download=False)
    with _meta_mem_lock:
        _meta_mem[url] = meta
    return meta


_bc_info_mem = {}
_bc_info_lock = threading.Lock()


def bandcamp_info(url, forzar=False):
    """Mira si un ítem de Bandcamp es «name your price» (gratis) y cuál es su
    página oficial de descarga gratuita.

    Sólo sirve para (1) mostrar el cartel «GRATIS» y (2) ofrecer el botón que
    abre esa página en el navegador. No descarga nada por su cuenta: la bajada
    la confirma la persona en la página de Bandcamp. Se cachea en memoria."""
    if not url:
        return None
    if not forzar:
        with _bc_info_lock:
            if url in _bc_info_mem:
                return _bc_info_mem[url]
    info = {"gratis": False, "free_page": None, "min_price": None, "require_email": None}
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": UA_HTML, "Accept-Language": "en"}
        )
        pagina = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "replace")
        m = re.search(r'data-tralbum="([^"]+)"', pagina)
        if m:
            datos = json.loads(html.unescape(m.group(1)))
            cur = datos.get("current") or {}
            mp = cur.get("minimum_price")
            info["min_price"] = mp
            info["require_email"] = cur.get("require_email")
            info["free_page"] = datos.get("freeDownloadPage")
            # Sólo mínimo $0: lo autoriza el propio artista (name your price).
            info["gratis"] = (mp == 0)
    except Exception:
        pass
    with _bc_info_lock:
        _bc_info_mem[url] = info
    return info


def leer_config():
    p = ruta_config()
    if p and os.path.isfile(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def guardar_config(datos):
    p = ruta_config()
    if not p:
        return
    try:
        with open(p, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


_ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def limpiar_ansi(s):
    return _ANSI.sub("", s or "")


def hms(seg):
    try:
        seg = int(seg)
    except (TypeError, ValueError):
        return "—"
    if seg <= 0:
        return "—"
    h, r = divmod(seg, 3600)
    m, s = divmod(r, 60)
    return "%d:%02d:%02d" % (h, m, s) if h else "%d:%02d" % (m, s)


def hbytes(n):
    try:
        n = float(n)
    except (TypeError, ValueError):
        return "?"
    for u in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return "%.1f %s" % (n, u)
        n /= 1024.0
    return "?"


# --------------------------------------------------------------------------
# Motor
# --------------------------------------------------------------------------
_CODECO = {
    "mp4a": "AAC",
    "aac": "AAC",
    "mp3": "MP3",
    "opus": "OPUS",
    "vorbis": "VORBIS",
    "flac": "FLAC",
    "alac": "ALAC",
    "wav": "WAV",
}


def sufijo_origen(decision):
    """Texto «(origen MP3 128 kbps)» para el nombre, según la fuente detectada."""
    d = decision or {}
    abr = d.get("abr")
    acodec = (d.get("acodec") or "").lower()
    etiqueta = ""
    for clave, valor in _CODECO.items():
        if acodec.startswith(clave):
            etiqueta = valor
            break
    if not etiqueta:
        etiqueta = (d.get("ext") or "").upper()
    partes = [p for p in (etiqueta, ("%d kbps" % int(abr)) if abr else "") if p]
    return " (origen %s)" % " ".join(partes) if partes else " (origen)"


def opciones_descarga(destino, formato, ffdir, hook, decision=None):
    base = "%(uploader,channel,creator,id)s - %(title)s [%(id)s]"
    sufijo = sufijo_origen(decision) if formato == FORMATO_TAG else ""
    op = {
        "outtmpl": os.path.join(destino, base + sufijo + ".%(ext)s"),
        "windowsfilenames": True,
        "trim_file_name": 200,
        "quiet": True,
        "no_warnings": False,
        "noprogress": True,
        "progress_hooks": [hook],
        "ignoreerrors": True,
        "noplaylist": True,
        "retries": 3,
        "fragment_retries": 3,
        "concurrent_fragment_downloads": 4,
    }
    if ffdir:
        op["ffmpeg_location"] = ffdir

    mp3 = [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "320"}]
    m4a = [{"key": "FFmpegExtractAudio", "preferredcodec": "m4a"}]
    wav = [{"key": "FFmpegExtractAudio", "preferredcodec": "wav"}]

    # El mejor audio detectado (o, si no se pudo sondear, el mejor ≤320).
    fuente = (decision or {}).get("format_id") or FORMATO_AUDIO

    if formato == FORMATO_ORIGINAL:
        # Tal cual viene: se baja el mejor original (WAV/FLAC o lo que haya)
        # sin recomprimir y sin tope de calidad.
        op["format"] = (decision or {}).get("format_id") or "bestaudio/best"
        return op

    if formato == FORMATO_TAG:
        # Uniforma a MP3 320 y el nombre queda anotado con el origen.
        op["format"] = fuente
        op["postprocessors"] = mp3
    elif formato == "MP3 320 kbps (convierte)":
        op["format"] = fuente
        op["postprocessors"] = mp3
    elif formato == "M4A / AAC (convierte)":
        op["format"] = fuente
        op["postprocessors"] = m4a
    elif formato == "WAV (sin comprimir)":
        op["format"] = fuente
        op["postprocessors"] = wav
    elif formato == "Video MP4 (mejor calidad)":
        op["format"] = "bv*+ba/b"
        op["merge_output_format"] = "mp4"
    else:  # Mejor calidad (hasta 320 kbps, sin recomprimir)
        op["format"] = fuente
        # Solo se recomprime cuando la fuente supera los 320 kbps (WAV/FLAC).
        if (decision or {}).get("excede"):
            op["postprocessors"] = mp3
    return op


def _buscar_ytdlp(fuente, termino, n):
    """Búsqueda nativa de yt-dlp (SoundCloud / YouTube)."""
    consulta = "%s%d:%s" % (PREFIJOS[fuente], n, termino)
    with yt_dlp.YoutubeDL(
        {"quiet": True, "no_warnings": True, "skip_download": True, "extract_flat": True}
    ) as ydl:
        info = ydl.extract_info(consulta, download=False)
    for e in info.get("entries") or []:
        yield {
            "id": e.get("id"),
            "titulo": e.get("title") or "(sin título)",
            "autor": e.get("uploader") or e.get("channel") or "",
            "dur": e.get("duration") or 0,
            "webpage": e.get("webpage_url") or e.get("url"),
        }


def _buscar_mixcloud(termino, n):
    """Búsqueda en Mixcloud por su API pública (sin clave).

    La API acepta como máximo 100 por página, así que se pagina con `offset`
    para poder devolver hasta el total pedido (p. ej. 200).
    """
    n = max(1, int(n))
    obtenidos = 0
    offset = 0
    while obtenidos < n:
        limite = min(100, n - obtenidos)
        url = "https://api.mixcloud.com/search/?" + urllib.parse.urlencode(
            {"q": termino, "type": "cloudcast", "limit": limite, "offset": offset}
        )
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.load(resp)
        items = data.get("data") or []
        if not items:
            break
        for c in items:
            yield {
                "id": "mc:" + (c.get("key") or c.get("url") or ""),
                "titulo": c.get("name") or "(sin título)",
                "autor": (c.get("user") or {}).get("name") or "",
                "dur": c.get("audio_length") or 0,
                "webpage": c.get("url"),
            }
            obtenidos += 1
            if obtenidos >= n:
                break
        offset += len(items)
        if len(items) < limite:  # no hay más resultados
            break


def _buscar_bandcamp(termino, n):
    """Búsqueda en Bandcamp por su API interna de autocompletado (sin clave).

    El buscador web de Bandcamp está detrás de un desafío JS, pero esta API
    responde siempre. Devuelve pistas y álbumes (los sellos/artistas se
    descartan porque no son descargables por sí solos).
    """
    cuerpo = json.dumps(
        {"search_text": termino, "search_filter": "", "fan_id": None, "full_page": False}
    ).encode("utf-8")
    req = urllib.request.Request(
        BANDCAMP_API,
        data=cuerpo,
        headers={
            "User-Agent": UA,
            "Content-Type": "application/json; charset=UTF-8",
            "Accept": "*/*",
            "Origin": "https://bandcamp.com",
            "Referer": "https://bandcamp.com/",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    vistos = set()
    c = 0
    for it in (data.get("auto") or {}).get("results") or []:
        if it.get("type") not in ("t", "a"):  # t = pista, a = álbum
            continue
        wp = it.get("item_url_path")
        if not wp or wp in vistos:
            continue
        vistos.add(wp)
        titulo = it.get("name") or "(sin título)"
        if it.get("type") == "a":
            titulo = "[ÁLBUM] " + titulo
        yield {
            "id": "bc:" + wp,
            "titulo": titulo,
            "autor": it.get("band_name") or "",
            "dur": 0,
            "webpage": wp,
        }
        c += 1
        if c >= n:
            break


def _buscar_a(fuente, termino, n):
    """Búsqueda de un término en una fuente, como lista (para ir en paralelo)."""
    if fuente == "Mixcloud":
        return list(_buscar_mixcloud(termino, n))
    if fuente == "Bandcamp":
        return list(_buscar_bandcamp(termino, n))
    return list(_buscar_ytdlp(fuente, termino, n))


def buscar(terminos, fuentes, por_pagina, cancelar=None):
    """Busca cada término en cada fuente y va entregando los resultados.

    Si se pasa `cancelar` (un threading.Event), se corta apenas quede activado:
    así el botón «Cerrar búsqueda» frena búsquedas largas al instante.
    """
    combos = []
    for termino in terminos:
        termino = (termino or "").strip()
        if not termino:
            continue
        for fuente in fuentes:
            combos.append((termino, fuente))
    if not combos:
        return
    vistos = set()
    # Las búsquedas se lanzan todas juntas: los resultados van saliendo a medida
    # que responde cada fuente, sin esperar a las demás.
    ex = concurrent.futures.ThreadPoolExecutor(max_workers=min(MAX_BUSQUEDAS, len(combos)))
    futuros = {ex.submit(_buscar_a, f, t, por_pagina): (t, f) for t, f in combos}
    for fut in concurrent.futures.as_completed(futuros):
        if cancelar is not None and cancelar.is_set():
            break
        termino, fuente = futuros[fut]
        try:
            resultados = fut.result()
        except Exception as e:
            yield {"error": "%s · «%s»" % (fuente, termino), "detalle": str(e)}
            continue
        for r in resultados:
            if cancelar is not None and cancelar.is_set():
                break
            clave = (r.get("id") or "").strip().lower()
            if not clave or clave in vistos:
                continue
            vistos.add(clave)
            r["fuente"] = fuente
            yield r
    ex.shutdown(wait=False)


class Pestana:
    """Una búsqueda con su propia tabla y su propio estado.

    Permite tener varias búsquedas abiertas a la vez, cada una en su pestaña,
    sin que se mezclen resultados, formatos ni el progreso del análisis.
    """

    def __init__(self, titulo):
        self.titulo = titulo
        self.nombre = None        # clave en Recuperador.pestanas
        self.marco = None         # contenedor dentro del Notebook
        self.tabla = None
        self.items = {}           # iid -> resultado de la búsqueda
        self.metas = {}           # iid -> metadata real (yt-dlp)
        self.pesos = {}           # iid -> bytes confirmados
        self.detalles = {}        # iid -> (formato, calidad)
        self.gratis = {}          # iid -> info de Bandcamp «name your price»
        self.analizados = set()   # iid ya enviados a analizar
        self.analisis_hechos = 0
        self.analisis_gen = 0
        self.cancelar = threading.Event()   # para cortar la búsqueda en curso
        self.viva = True          # pasa a False al cerrar la pestaña
        self.buscando = False


# --------------------------------------------------------------------------
# Ventana
# --------------------------------------------------------------------------
class Recuperador:
    def __init__(self, root):
        self.root = root
        self.cola = queue.Queue()
        self.pestanas = {}           # nombre interno -> Pestana
        self.actual = None           # pestaña visible
        self.en_busqueda = set()     # pestañas con búsqueda en curso
        self.ex_analisis = concurrent.futures.ThreadPoolExecutor(max_workers=MAX_ANALISIS)
        self.ex_gratis = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        self.ffdir = hallar_ffmpeg()
        self.ocupado = False
        cfg = leer_config()
        self._construir()
        if cfg.get("destino"):
            self.var_destino.set(cfg["destino"])
        if cfg.get("formato") in FORMATOS:
            self.var_formato.set(cfg["formato"])
        self._avisar_ffmpeg()
        self.root.protocol("WM_DELETE_WINDOW", self._cerrar)
        self.root.after(80, self._pump)

    # ---------------- construcción ----------------
    def _construir(self):
        self.root.title(APP + "  v" + VERSION)
        _poner_icono(self.root)
        self.iconos = crear_iconos_fila(self.root, TEMA)
        self.root.geometry("1150x780")
        self.root.minsize(900, 620)

        # barra superior
        top = ttk.Frame(self.root, padding=(10, 8, 10, 4))
        top.pack(fill="x")
        fila1 = ttk.Frame(top)
        fila1.pack(fill="x")
        ttk.Button(fila1, text="¿Cómo se usa?", command=self._ayuda).pack(side="right")
        ttk.Label(fila1, text="Buscar en:").pack(side="left")
        self.var_sc = tk.BooleanVar(value=True)
        self.var_yt = tk.BooleanVar(value=True)
        self.var_mc = tk.BooleanVar(value=True)
        self.var_bc = tk.BooleanVar(value=True)
        ttk.Checkbutton(fila1, text="SoundCloud", variable=self.var_sc).pack(side="left", padx=(8, 0))
        ttk.Checkbutton(fila1, text="YouTube", variable=self.var_yt).pack(side="left", padx=(8, 0))
        ttk.Checkbutton(fila1, text="Mixcloud", variable=self.var_mc).pack(side="left", padx=(8, 0))
        ttk.Checkbutton(fila1, text="Bandcamp", variable=self.var_bc).pack(side="left", padx=(8, 0))
        ttk.Label(fila1, text="   Resultados por término (máx 200):").pack(side="left")
        self.var_n = tk.IntVar(value=70)
        ttk.Spinbox(fila1, from_=5, to=200, width=4, textvariable=self.var_n).pack(side="left", padx=(4, 0))

        # Términos + botón Buscar. El botón lleva el logo (la pluma) y va pegado
        # al campo «Busca aquí…» para que se entienda que sirve para buscar.
        ttk.Label(top, text="Términos (uno por línea):").pack(anchor="w", pady=(8, 2))
        f_term = ttk.Frame(top)
        f_term.pack(fill="x")
        self.txt_terminos = tk.Text(
            f_term, height=3, wrap="none", font=TEMA["fuente"],
            bg=TEMA["panel"], fg=TEMA["fg"], insertbackground=TEMA["fg"],
            relief="flat", highlightthickness=1,
            highlightbackground=TEMA["line"], highlightcolor=TEMA["accent"],
        )
        self.txt_terminos.pack(side="left", fill="both", expand=True)
        img_buscar = self._cargar_imagen(MARCA["btn"])
        f_bus = ttk.Frame(f_term)
        f_bus.pack(side="left", padx=(8, 0), anchor="n")
        if img_buscar is not None:
            self._img_buscar = img_buscar  # mantener la referencia viva
            self.btn_buscar = ttk.Button(
                f_bus, image=self._img_buscar, text="Buscar",
                compound="top", command=self._buscar,
            )
        else:
            self.btn_buscar = ttk.Button(f_bus, text="Buscar", command=self._buscar)
        self.btn_buscar.pack()
        self._ph_terminos = "Busca aquí… (un término por línea)"
        self._ph_activo = False
        if TERMINOS_DEF.strip():
            self.txt_terminos.insert("1.0", TERMINOS_DEF)
        else:
            self._poner_placeholder()
        self.txt_terminos.bind("<FocusIn>", self._ph_in)
        self.txt_terminos.bind("<FocusOut>", self._ph_out)

        # pestañas: una por búsqueda, así se pueden tener varias abiertas a la vez
        medio = ttk.Frame(self.root, padding=(10, 4))
        medio.pack(fill="both", expand=True)
        self.nb = ttk.Notebook(medio)
        self.nb.pack(fill="both", expand=True)
        self.nb.bind("<<NotebookTabChanged>>", self._cambio_pestana)
        self._nueva_pestana()

        # carpeta destino
        f_dest = ttk.Frame(self.root, padding=(10, 0))
        f_dest.pack(fill="x")
        ttk.Label(f_dest, text="Carpeta destino:").pack(side="left")
        self.var_destino = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Music", MARCA["descargas"]))
        ttk.Entry(f_dest, textvariable=self.var_destino).pack(side="left", fill="x", expand=True, padx=(6, 6))
        ttk.Button(f_dest, text="Elegir…", command=self._elegir_destino).pack(side="left")
        ttk.Button(f_dest, text="Abrir", command=self._abrir_destino).pack(side="left", padx=(6, 0))
        ttk.Button(f_dest, text="Importar…", command=self._importar).pack(side="left", padx=(6, 0))

        # formato y acciones
        f_fmt = ttk.Frame(self.root, padding=(10, 6))
        f_fmt.pack(fill="x")
        ttk.Label(f_fmt, text="Formato:").pack(side="left")
        self.var_formato = tk.StringVar(value=FORMATOS[0])
        self.cmb_formato = ttk.Combobox(
            f_fmt, textvariable=self.var_formato, values=FORMATOS, state="readonly", width=36
        )
        self.cmb_formato.pack(side="left", padx=(6, 12))
        self.cmb_formato.bind("<<ComboboxSelected>>", self._cambio_formato)
        ttk.Button(f_fmt, text="Marcar todos", command=lambda: self._marcar_todos(True)).pack(side="left")
        ttk.Button(f_fmt, text="Desmarcar", command=lambda: self._marcar_todos(False)).pack(side="left", padx=(6, 0))
        if EDICION == "secretflow":
            ttk.Button(f_fmt, text="Marcar los de «Tectónica»", command=self._marcar_tectonica).pack(side="left", padx=(6, 0))
        self.btn_descargar = ttk.Button(f_fmt, text="Descargar seleccionados", command=self._descargar, style="Pri.TButton")
        self.btn_descargar.pack(side="right")
        self.btn_original = ttk.Button(
            f_fmt, text="Descargar original", command=self._descargar_original
        )
        self.btn_original.pack(side="right", padx=(0, 6))

        # progreso + registro
        fondo = ttk.Frame(self.root, padding=(10, 4, 10, 10))
        fondo.pack(fill="x")
        f_prog = ttk.Frame(fondo)
        f_prog.pack(fill="x")
        self.pb = ttk.Progressbar(f_prog, mode="determinate", maximum=100)
        self.pb.pack(side="left", fill="x", expand=True)
        self.lbl_prog = ttk.Label(f_prog, text="", width=44)
        self.lbl_prog.pack(side="left", padx=(8, 0))
        fila_est = ttk.Frame(fondo)
        fila_est.pack(fill="x", pady=(4, 4))
        self.lbl_estado = ttk.Label(fila_est, text="Listo")
        self.lbl_estado.pack(side="left")
        self.lbl_analisis = ttk.Label(fila_est, text="")
        self.lbl_analisis.pack(side="left", padx=(12, 0))
        self.btn_detener = ttk.Button(fila_est, text="Detener análisis", command=self._detener_analisis)
        self.btn_detener.pack(side="right")
        self.btn_cerrar_busqueda = ttk.Button(fila_est, text="Cerrar búsqueda", command=self._cerrar_busqueda)
        self.btn_cerrar_busqueda.pack(side="right", padx=(0, 6))
        self.lbl_peso = ttk.Label(fila_est, text="nada seleccionado")
        self.lbl_peso.pack(side="right", padx=(0, 12))
        self.txt_log = scrolledtext.ScrolledText(
            fondo, height=8, wrap="word", font=("Consolas", 9),
            bg=TEMA["logbg"], fg=TEMA["logfg"], insertbackground=TEMA["logfg"],
            relief="flat", highlightthickness=1, highlightbackground=TEMA["line"],
        )
        self.txt_log.pack(fill="x")
        self.txt_log.configure(state="disabled")

    # ---------------- pestañas (una por búsqueda) ----------------
    def _nueva_pestana(self, titulo=None):
        """Crea una pestaña nueva con su propia tabla y la deja visible."""
        base = (titulo or "").strip() or ("Búsqueda %d" % (len(self.pestanas) + 1))
        p = Pestana(self._titulo_unico(base))
        marco = ttk.Frame(self.nb, padding=(0, 4))
        p.marco = marco
        cols = ("marca", "titulo", "autor", "dur", "formato", "calidad", "peso", "fuente")
        tabla = ttk.Treeview(marco, columns=cols, show="tree headings", selectmode="browse",
                             style="Tabla.Treeview")
        p.tabla = tabla
        tabla.heading("#0", text="✓")
        tabla.heading("marca", text="")
        tabla.heading("titulo", text="Título")
        tabla.heading("autor", text="Subido por")
        tabla.heading("dur", text="Duración")
        tabla.heading("formato", text="Formato")
        tabla.heading("calidad", text="Calidad")
        tabla.heading("peso", text="Peso")
        tabla.heading("fuente", text="Fuente")
        # #0 lleva el cuadradito ✓ y (si es gratis) el botón de descarga, dibujados
        # como imagen para que tengan tamaño propio sin agrandar la letra.
        tabla.column("#0", width=52, minwidth=52, anchor="center", stretch=False)
        tabla.column("marca", width=0, minwidth=0, stretch=False)  # estado, oculto
        tabla.column("titulo", width=330)
        tabla.column("autor", width=190)
        tabla.column("dur", width=80, anchor="center", stretch=False)
        tabla.column("formato", width=70, anchor="center", stretch=False)
        tabla.column("calidad", width=90, anchor="center", stretch=False)
        tabla.column("peso", width=90, anchor="e", stretch=False)
        tabla.column("fuente", width=100, anchor="center", stretch=False)
        barra = ttk.Scrollbar(marco, orient="vertical", command=tabla.yview)
        tabla.configure(yscrollcommand=barra.set)
        tabla.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        tabla.bind("<Button-1>", lambda ev, p=p: self._click_tabla(p, ev))
        tabla.tag_configure("est", foreground=TEMA["mute"])
        tabla.tag_configure("gratis", foreground=TEMA["accent"])
        p.nombre = str(marco)
        self.pestanas[p.nombre] = p
        self.nb.add(marco, text=p.titulo)
        self.nb.select(marco)
        self.actual = p
        return p

    def _titulo_unico(self, titulo, evitar=None):
        usados = {q.titulo for q in self.pestanas.values() if q is not evitar}
        if titulo not in usados:
            return titulo
        n = 2
        while "%s (%d)" % (titulo, n) in usados:
            n += 1
        return "%s (%d)" % (titulo, n)

    def _renombrar_pestana(self, p, titulo):
        titulo = (titulo or "").strip()
        if not titulo:
            return
        p.titulo = self._titulo_unico(titulo[:28], evitar=p)
        try:
            self.nb.tab(p.marco, text=p.titulo)
        except Exception:
            pass

    def _cambio_pestana(self, *_):
        """Cuando cambia la pestaña visible, actualiza el estado de abajo."""
        nombre = self.nb.select()
        if nombre and nombre in self.pestanas:
            self.actual = self.pestanas[nombre]
        self._actualizar_total()
        self._refrescar_label_analisis()

    def _activar(self, p):
        self.actual = p
        self._actualizar_total()
        self._refrescar_label_analisis()

    def _cerrar_busqueda(self):
        """Cierra la pestaña actual: corta su búsqueda/análisis y la borra."""
        p = self.actual
        if not p:
            return
        p.viva = False
        p.cancelar.set()
        p.analisis_gen += 1
        self.en_busqueda.discard(p)
        if not self.en_busqueda:
            self.lbl_estado.config(text="Búsqueda cerrada")
        self.pestanas.pop(p.nombre, None)
        try:
            self.nb.forget(p.marco)
        except Exception:
            pass
        try:
            p.marco.destroy()
        except Exception:
            pass
        if not self.pestanas:
            self._nueva_pestana()
        else:
            self._cambio_pestana()

    # ---------------- imágenes / marcador de los términos ----------------
    def _cargar_imagen(self, nombre):
        ruta = _ruta_recurso(nombre)
        if not ruta:
            return None
        try:
            return tk.PhotoImage(master=self.root, file=ruta)
        except Exception:
            return None

    def _poner_placeholder(self):
        self.txt_terminos.delete("1.0", "end")
        self.txt_terminos.insert("1.0", self._ph_terminos)
        self.txt_terminos.tag_add("ph", "1.0", "end")
        self.txt_terminos.tag_config("ph", foreground=TEMA["mute"])
        self._ph_activo = True

    def _ph_in(self, *_):
        if self._ph_activo:
            self.txt_terminos.delete("1.0", "end")
            self.txt_terminos.tag_remove("ph", "1.0", "end")
            self._ph_activo = False

    def _ph_out(self, *_):
        if not self.txt_terminos.get("1.0", "end").strip():
            self._poner_placeholder()

    # ---------------- tabla ----------------
    def _icono_marca(self, p, iid, marcado):
        """Ícono de la fila: cuadradito solo, o cuadradito + botón si es gratis."""
        if iid in p.gratis:
            return self.iconos["on_btn"] if marcado else self.iconos["off_btn"]
        return self.iconos["on"] if marcado else self.iconos["off"]

    def _click_tabla(self, p, ev):
        if p.tabla.identify_region(ev.x, ev.y) not in ("cell", "tree"):
            return
        iid = p.tabla.identify_row(ev.y)
        if not iid:
            return
        if p.tabla.identify_column(ev.x) != "#0":
            return
        # Dentro de #0: el cuadradito ocupa la izquierda y el botón, la derecha.
        try:
            x0 = p.tabla.bbox(iid, "#0")[0]
        except (IndexError, TypeError):
            x0 = 0
        if (ev.x - x0) < 24 or iid not in p.gratis:
            self._alternar(p, iid)
        else:
            self._bajar_gratis_uno(p, iid)

    def _bajar_gratis_uno(self, p, iid):
        """Abre la página oficial de descarga del tema GRATIS (Bandcamp «name
        your price») en el navegador, para completar el $0 y elegir FLAC."""
        r = p.items.get(iid) or {}
        self._log("\n=== Bajar gratis · %s ===" % (r.get("titulo") or ""))
        self._log("  Bandcamp «name your price»: elegí FLAC y confirmá la descarga ($0).")
        self._log("  Cuando termine, tocá «Importar…» y elegí lo que bajaste.")
        threading.Thread(target=self._abrir_gratis_una, args=(p, iid), daemon=True).start()

    def _alternar(self, p, iid):
        vals = list(p.tabla.item(iid, "values"))
        if not vals:
            return
        marcado = vals[0] != "☑"
        vals[0] = "☑" if marcado else "☐"
        p.tabla.item(iid, values=vals, image=self._icono_marca(p, iid, marcado))
        if p is self.actual:
            self._actualizar_total()

    def _marcar_todos(self, marcar):
        p = self.actual
        if not p:
            return
        signo = "☑" if marcar else "☐"
        ico = self.iconos["on"] if marcar else self.iconos["off"]
        ico_btn = self.iconos["on_btn"] if marcar else self.iconos["off_btn"]
        for iid in p.tabla.get_children():
            vals = list(p.tabla.item(iid, "values"))
            if not vals:
                continue
            vals[0] = signo
            p.tabla.item(iid, values=vals, image=(ico_btn if iid in p.gratis else ico))
        self._actualizar_total()

    def _marcar_tectonica(self):
        p = self.actual
        if not p:
            return
        for iid in p.tabla.get_children():
            autor = (p.items.get(iid, {}).get("autor") or "").lower()
            vals = list(p.tabla.item(iid, "values"))
            if not vals:
                continue
            marcado = "tect" in autor
            vals[0] = "☑" if marcado else "☐"
            p.tabla.item(iid, values=vals, image=self._icono_marca(p, iid, marcado))
        self._actualizar_total()

    def _agregar_fila(self, p, r):
        iid = p.tabla.insert(
            "", "end",
            image=self.iconos["off"],
            values=("☐", r["titulo"], r["autor"], hms(r["dur"]), "…", "…", "…", r["fuente"]),
            tags=("est",),
        )
        p.items[iid] = r
        self._pintar_estimado(p, iid)
        return iid

    # ----------------- análisis -----------------
    def _reiniciar_analisis(self, p):
        p.analisis_gen += 1
        p.analizados.clear()
        p.analisis_hechos = 0
        if p is self.actual:
            self.lbl_analisis.config(text="")
    def _programar_analisis(self, p, iid):
        """Encola una fila para averiguar su formato, calidad y peso.

        Se llama apenas llega cada resultado (no al final de la búsqueda), así
        el dato va apareciendo mientras la búsqueda sigue corriendo.
        """
        if iid in p.analizados:
            return
        p.analizados.add(iid)
        url = (p.items.get(iid) or {}).get("webpage")
        gen = p.analisis_gen
        if not url:
            self._analisis_listo(p, None, iid, gen)
            return
        fut = self.ex_analisis.submit(extraer_meta, url)
        fut.add_done_callback(lambda f, p=p, iid=iid, gen=gen: self._analisis_listo(p, f, iid, gen))
        self._programar_gratis(p, iid)

    def _programar_gratis(self, p, iid):
        """Pregunta, en un hilo aparte, si el ítem de Bandcamp es «name your
        price» (gratis). Va en su propio ejecutor para no competir con el
        análisis de formato/peso."""
        r = p.items.get(iid) or {}
        if r.get("fuente") != "Bandcamp":
            return
        url = r.get("webpage")
        if not url:
            return
        fut = self.ex_gratis.submit(bandcamp_info, url)
        fut.add_done_callback(lambda f, p=p, iid=iid: self._info_listo(p, f, iid))

    def _info_listo(self, p, fut, iid):
        try:
            info = fut.result()
        except Exception:
            info = None
        self.cola.put(("gratis", (p, iid, info)))

    def _marcar_gratis(self, p, iid):
        """Marca la fila como GRATIS (name your price) y le pone el botón ⬇."""
        r = p.items.get(iid) or {}
        vals = list(p.tabla.item(iid, "values"))
        if not vals:
            return
        titulo = vals[1] if len(vals) > 1 else ""
        if not str(titulo).startswith("GRATIS"):
            vals[1] = "GRATIS · " + (r.get("titulo") or str(titulo))
        marcado = vals[0] == "☑"
        p.tabla.item(iid, values=vals, image=self._icono_marca(p, iid, marcado),
                     tags=("gratis",))

    def _analisis_listo(self, p, fut, iid, gen):
        """Terminó el análisis de una fila (puede venir de otro hilo)."""
        if fut is None:
            meta = None
        else:
            try:
                meta = fut.result()
            except Exception:
                meta = None
        if gen == p.analisis_gen:
            self.cola.put(("detalle", (p, iid, meta)))
    def _refrescar_label_analisis(self):
        p = self.actual
        if not p:
            self.lbl_analisis.config(text="")
            return
        total = len(p.analizados)
        if not total or p.analisis_hechos >= total:
            self.lbl_analisis.config(text="")
        else:
            self.lbl_analisis.config(text="analizando %d/%d…" % (p.analisis_hechos, total))

    def _detener_analisis(self):
        p = self.actual
        if not p:
            return
        p.analisis_gen += 1
        self.lbl_analisis.config(text="análisis detenido")
    def _pintar_detalle(self, p, iid):
        meta = p.metas.get(iid)
        if not meta:
            return
        fmt, cal = detalle_formato(meta, self.var_formato.get())
        p.detalles[iid] = (fmt, cal)
        b = estimar_peso(meta, self.var_formato.get())
        p.pesos[iid] = b or 0
        p.tabla.set(iid, "formato", fmt)
        p.tabla.set(iid, "calidad", cal)
        p.tabla.set(iid, "peso", hbytes(b) if b else "?")
        p.tabla.item(iid, tags=("gratis",) if iid in p.gratis else ())  # dato real: deja de estar en gris

    def _pintar_estimado(self, p, iid):
        """Formato/peso aproximado mientras corre el análisis real (en gris)."""
        r = p.items.get(iid) or {}
        fmt, cal, b = estimar_fila(r.get("fuente"), r.get("dur"), self.var_formato.get())
        p.pesos.pop(iid, None)  # el estimado no cuenta como peso confirmado
        p.tabla.set(iid, "formato", fmt or "…")
        p.tabla.set(iid, "calidad", cal or "…")
        p.tabla.set(iid, "peso", ("~" + hbytes(b)) if b else "…")
        p.tabla.item(iid, tags=("gratis",) if iid in p.gratis else ("est",))

    def _cambio_formato(self, *_):
        for p in self.pestanas.values():
            for iid in p.tabla.get_children():
                if iid in p.metas:
                    self._pintar_detalle(p, iid)
                else:
                    self._pintar_estimado(p, iid)
        self._actualizar_total()

    def _actualizar_total(self):
        p = self.actual
        if not p:
            self.lbl_peso.config(text="nada seleccionado")
            return
        n = 0
        total = 0
        calculando = 0
        for iid in p.tabla.get_children():
            if p.tabla.set(iid, "marca") != "☑":
                continue
            n += 1
            b = p.pesos.get(iid) or 0
            if b:
                total += b
            elif iid not in p.metas:
                calculando += 1
        if not n:
            self.lbl_peso.config(text="nada seleccionado")
            return
        txt = "%d seleccionado(s)" % n
        if total:
            txt += "  ·  ~%s" % hbytes(total)
        if calculando:
            txt += "  ·  %d calculando…" % calculando
        self.lbl_peso.config(text=txt)

    # ----------------- búsqueda -----------------
    def _buscar(self):
        if self.ocupado:
            return
        fuentes = []
        if self.var_sc.get():
            fuentes.append("SoundCloud")
        if self.var_yt.get():
            fuentes.append("YouTube")
        if self.var_mc.get():
            fuentes.append("Mixcloud")
        if self.var_bc.get():
            fuentes.append("Bandcamp")
        if not fuentes:
            messagebox.showinfo(APP, "Elegí al menos una fuente (SoundCloud, YouTube, Mixcloud o Bandcamp).")
            return
        terminos = []
        if not self._ph_activo:
            terminos = [t for t in self.txt_terminos.get("1.0", "end").splitlines() if t.strip()]
        if not terminos:
            messagebox.showinfo(APP, "Escribí al menos un término de búsqueda.")
            return
        # La búsqueda usa la pestaña actual si está vacía; si no, abre una nueva.
        p = self.actual
        if p is None or p.tabla.get_children() or p.buscando:
            p = self._nueva_pestana((terminos[0] if terminos else "Búsqueda")[:28])
        else:
            self._renombrar_pestana(p, (terminos[0] if terminos else "")[:28])
            self.nb.select(p.marco)
        self._activar(p)
        for iid in p.tabla.get_children():
            p.tabla.delete(iid)
        p.items.clear()
        p.metas.clear()
        p.pesos.clear()
        p.detalles.clear()
        p.gratis.clear()
        p.cancelar.clear()
        p.viva = True
        self._reiniciar_analisis(p)
        self._actualizar_total()
        self._log("\n=== Buscando %d término(s) en %s ===" % (len(terminos), ", ".join(fuentes)))
        p.buscando = True
        self.en_busqueda.add(p)
        self.lbl_estado.config(text="Buscando…")
        threading.Thread(
            target=self._hilo_buscar, args=(p, terminos, fuentes, int(self.var_n.get())), daemon=True
        ).start()

    def _hilo_buscar(self, p, terminos, fuentes, n):
        try:
            c = 0
            for r in buscar(terminos, fuentes, n, cancelar=p.cancelar):
                if not p.viva:
                    break
                if "error" in r:
                    self.cola.put(("log", "  no se pudo buscar «%s»: %s" % (r["error"], r["detalle"])))
                else:
                    c += 1
                    self.cola.put(("fila", (p, r)))
            self.cola.put(("fin_busqueda", (p, c)))
        except Exception as e:
            self.cola.put(("log", "  error inesperado: %s" % e))
            self.cola.put(("fin_busqueda", (p, 0)))

    # ----------------- descarga -----------------
    def _hook(self):
        def h(d):
            estado = d.get("status")
            if estado == "downloading":
                tot = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                got = d.get("downloaded_bytes") or 0
                pct = (got * 100.0 / tot) if tot else 0
                self.cola.put(("prog", (pct, "%.0f%%  ·  %s / %s  ·  %s/s" % (
                    pct, hbytes(got), hbytes(tot) if tot else "?", hbytes(d.get("speed") or 0)))))
            elif estado == "finished":
                self.cola.put(("prog", (100, "procesando…")))
        return h

    def _descargar(self):
        self._lanzar_descarga(self.var_formato.get())

    def _descargar_original(self):
        """Baja el archivo tal cual viene (WAV/FLAC o la mejor versión), sin
        recomprimir ni tope de 320 kbps, por si se quiere conservar el original
        además del MP3."""
        self._lanzar_descarga(FORMATO_ORIGINAL)

    def _lanzar_descarga(self, formato):
        if self.ocupado:
            return
        p = self.actual
        objetivo = []
        if p:
            for iid in p.tabla.get_children():
                vals = p.tabla.item(iid, "values")
                if vals and vals[0] == "☑":
                    objetivo.append((iid, p.items.get(iid, {})))
        if not objetivo:
            messagebox.showinfo(APP, "No hay nada marcado. Hacé clic en la columna ✓ para elegir qué descargar.")
            return
        destino = self.var_destino.get().strip()
        try:
            os.makedirs(destino, exist_ok=True)
        except OSError as e:
            messagebox.showerror(APP, "No pude crear ni usar la carpeta destino:\n%s" % e)
            return
        formato = self.var_formato.get()
        if formato in FORMATOS_CON_FFMPEG and not self.ffdir:
            if os.name == "nt":
                como = ("  • Instalalo con:  winget install Gyan.FFmpeg\n"
                        "  • O poné ffmpeg.exe en una carpeta 'ffmpeg' junto a este programa.")
            elif sys.platform == "darwin":
                como = ("  • Instalalo con:  brew install ffmpeg\n"
                        "  • O poné el binario 'ffmpeg' en una carpeta 'ffmpeg' junto a la app.")
            else:
                como = "  • Instalalo con el gestor de paquetes de tu sistema."
            messagebox.showerror(
                APP,
                "Para convertir a %s hace falta ffmpeg y no lo encontré.\n\n%s" % (formato, como),
            )
            return
        # Al descargar, se frena el análisis de fondo para no competir por la red.
        p.analisis_gen += 1
        self.lbl_analisis.config(text="")
        peso = sum(p.pesos.get(iid, 0) for iid, _ in objetivo)
        etiqueta = "original (sin recomprimir)" if formato == FORMATO_ORIGINAL else formato
        self._log("\n=== Descargando %d archivo(s)  ·  %s ===" % (len(objetivo), etiqueta))
        if peso:
            self._log("    peso estimado: ~%s" % hbytes(peso))
        self._ocupar(True, "Descargando…")
        threading.Thread(target=self._hilo_descargar, args=(p, objetivo, destino, formato), daemon=True).start()
    def _hilo_descargar(self, p, objetivo, destino, formato):
        ok = 0
        total = len(objetivo)
        for i, (iid, info) in enumerate(objetivo, 1):
            self.cola.put(("log", "\n[%d/%d] %s  —  %s" % (i, total, info["titulo"], info.get("autor", ""))))
            decision = None
            if formato != "Video MP4 (mejor calidad)":
                meta = p.metas.get(iid)
                if not meta:
                    try:
                        meta = extraer_meta(info["webpage"])
                        p.metas[iid] = meta
                    except Exception as e:
                        self.cola.put(("log", "   (no pude leer los formatos: %s)" % e))
                if meta:
                    decision = elegir_audio(meta)
                if decision:
                    abr = ("%d kbps" % decision["abr"]) if decision["abr"] else "sin dato"
                    linea = "   fuente: %s %s" % (decision["ext"], abr)
                    if formato == "Mejor calidad (hasta 320 kbps, sin recomprimir)":
                        linea += " → " + ("se convierte a MP3 320" if decision["excede"] else "se guarda tal cual")
                    elif formato == FORMATO_TAG:
                        linea += " → se uniforma a MP3 320 (con tag de origen)"
                    elif formato == FORMATO_ORIGINAL:
                        if decision["lossless"]:
                            linea += " → original sin pérdida (se guarda tal cual)"
                        elif decision["excede"]:
                            linea += " → original de alta calidad (se guarda tal cual)"
                        else:
                            linea += " → no hay versión mayor; se guarda la mejor disponible"
                    self.cola.put(("log", linea))
            op = opciones_descarga(destino, formato, self.ffdir, self._hook(), decision)
            try:
                with yt_dlp.YoutubeDL(op) as ydl:
                    ydl.download([info["webpage"]])
                ok += 1
                self.cola.put(("log", "   ✓ descargado"))
            except Exception as e:
                self.cola.put(("log", "   ✗ %s" % e))
        self.cola.put(("fin_descarga", (ok, total)))

    # ----------------- bomba de mensajes -----------------
    def _pump(self):
        try:
            while True:
                tipo, dato = self.cola.get_nowait()
                if tipo == "fila":
                    p, r = dato
                    if not p.viva:
                        continue
                    iid = self._agregar_fila(p, r)
                    self._programar_analisis(p, iid)
                    if p is self.actual:
                        self._refrescar_label_analisis()
                elif tipo == "log":
                    self._log(dato)
                elif tipo == "prog":
                    pct, texto = dato
                    self.pb["value"] = pct
                    self.lbl_prog.config(text=texto)
                elif tipo == "detalle":
                    p, iid, meta = dato
                    if not p.viva:
                        continue
                    p.analisis_hechos += 1
                    if meta:
                        p.metas[iid] = meta
                        self._pintar_detalle(p, iid)
                    else:
                        p.tabla.item(iid, tags=("gratis",) if iid in p.gratis else ())
                        p.tabla.set(iid, "formato", "—")
                        p.tabla.set(iid, "calidad", "—")
                        p.tabla.set(iid, "peso", "?")
                    if p is self.actual:
                        self._refrescar_label_analisis()
                        self._actualizar_total()
                elif tipo == "gratis":
                    p, iid, info = dato
                    if p.viva and info and info.get("gratis") and iid in p.items:
                        p.gratis[iid] = info
                        self._marcar_gratis(p, iid)
                elif tipo == "fin_busqueda":
                    p, c = dato
                    p.buscando = False
                    self.en_busqueda.discard(p)
                    self._log("=== %d resultado(s) ===" % c)
                    if not self.en_busqueda:
                        self.lbl_estado.config(text=("%d resultado(s)" % c) if c else "Sin resultados")
                    if p is self.actual:
                        self._refrescar_label_analisis()
                elif tipo == "fin_descarga":
                    ok, total = dato
                    self._log("=== Terminado: %d de %d ===" % (ok, total))
                    self.pb["value"] = 0
                    self.lbl_prog.config(text="")
                    self._ocupar(False, "Listo: %d/%d" % (ok, total))
        except queue.Empty:
            pass
        self.root.after(80, self._pump)

    # ----------------- helpers -----------------
    def _log(self, texto):
        self.txt_log.configure(state="normal")
        self.txt_log.insert("end", limpiar_ansi(str(texto)) + "\n")
        self.txt_log.see("end")
        self.txt_log.configure(state="disabled")

    def _ocupar(self, ocupado, estado):
        self.ocupado = ocupado
        est = "disabled" if ocupado else "normal"
        self.btn_buscar.config(state=est)
        self.btn_descargar.config(state=est)
        self.btn_original.config(state=est)
        self.lbl_estado.config(text=estado)

    def _elegir_destino(self):
        d = filedialog.askdirectory(initialdir=self.var_destino.get() or os.path.expanduser("~"))
        if d:
            self.var_destino.set(d)

    def _abrir_destino(self):
        d = self.var_destino.get().strip()
        if os.path.isdir(d):
            abrir_ruta(d)
        else:
            messagebox.showinfo(APP, "La carpeta todavía no existe.")

    def _ayuda(self):
        """Muestra el README («cómo se usa») en una ventana con el estilo de la
        edición. El archivo va empaquetado dentro del ejecutable."""
        ruta = _ruta_recurso(MARCA["readme"])
        if not ruta:
            messagebox.showinfo(APP, "No encontré el archivo de ayuda.")
            return
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                texto = f.read()
        except OSError:
            try:
                abrir_ruta(ruta)
            except Exception:
                messagebox.showinfo(APP, "No pude abrir el archivo de ayuda.")
            return
        v = tk.Toplevel(self.root)
        v.title("Cómo se usa · " + APP + " v" + VERSION)
        _poner_icono(v)
        v.configure(bg=TEMA["bg"])
        v.geometry("780x640")
        v.minsize(520, 380)
        marco = ttk.Frame(v, padding=(10, 10, 10, 6))
        marco.pack(fill="both", expand=True)
        barra = ttk.Scrollbar(marco, orient="vertical")
        txt = tk.Text(
            marco, wrap="word", font=_fuente_mono(), bg=TEMA["panel"], fg=TEMA["fg"],
            relief="flat", highlightthickness=1, highlightbackground=TEMA["line"],
            padx=14, pady=10, spacing1=1, spacing3=2, yscrollcommand=barra.set,
        )
        barra.configure(command=txt.yview)
        barra.pack(side="right", fill="y")
        txt.pack(side="left", fill="both", expand=True)
        txt.insert("1.0", texto)
        txt.configure(state="disabled")
        ttk.Button(v, text="Cerrar", command=v.destroy).pack(pady=(0, 10))
        v.transient(self.root)

    def _abrir_gratis(self):
        """Abre en el navegador la página oficial de descarga gratuita de los
        temas «name your price» (GRATIS) marcados. La bajada la confirmás vos
        eligiendo FLAC; después, con «Importar…», entra a la carpeta destino.

        Nunca baja nada por su cuenta: Bandcamp protege esas descargas con
        reCAPTCHA, así que el clic final lo da una persona en el navegador."""
        p = self.actual
        if not p:
            return
        marcados = [iid for iid in p.tabla.get_children()
                    if p.tabla.set(iid, "marca") == "☑"]
        objetivo = [iid for iid in marcados if iid in p.gratis]
        if not objetivo:
            if any(iid in p.gratis for iid in p.tabla.get_children()):
                messagebox.showinfo(
                    APP,
                    "Marcá en la columna ✓ los temas «GRATIS» que quieras bajar\n"
                    "y volvé a tocar «Bajar gratis».",
                )
            else:
                messagebox.showinfo(APP, "No hay temas «GRATIS» (name your price) en la lista.")
            return
        if len(objetivo) > 12:
            messagebox.showinfo(APP, "Son muchos para abrir de una. Se abren los primeros 12.")
            objetivo = objetivo[:12]
        self._log("\n=== Abriendo %d página(s) de descarga gratuita (Bandcamp) ===" % len(objetivo))
        for iid in objetivo:
            self._log("  gratis · %s" % ((p.items.get(iid) or {}).get("titulo") or ""))
            threading.Thread(target=self._abrir_gratis_una, args=(p, iid), daemon=True).start()
        self._log("  En la página elegí FLAC y confirmá la descarga ($0).")
        self._log("  Cuando termine, tocá «Importar…» y elegí lo que bajaste.")

    def _abrir_gratis_una(self, p, iid):
        """Regenera la página de descarga (la firma caduca) y la abre."""
        url = (p.items.get(iid) or {}).get("webpage")
        if not url:
            return
        info = bandcamp_info(url, forzar=True)
        dest = (info or {}).get("free_page") or url
        try:
            abrir_ruta(dest)
        except Exception as e:
            self.cola.put(("log", "  no pude abrir el navegador: %s" % e))
    def _importar(self):
        """Copia a la carpeta destino lo que bajaste con el navegador (audio
        suelto o un .zip de Bandcamp; el zip se descomprime)."""
        destino = self.var_destino.get().strip()
        if not destino:
            messagebox.showinfo(APP, "Elegí una carpeta destino primero.")
            return
        try:
            os.makedirs(destino, exist_ok=True)
        except OSError as e:
            messagebox.showerror(APP, "No pude usar la carpeta destino:\n%s" % e)
            return
        inicial = os.path.join(os.path.expanduser("~"), "Downloads")
        if not os.path.isdir(inicial):
            inicial = os.path.expanduser("~")
        rutas = filedialog.askopenfilenames(
            title="Elegí lo que bajaste",
            initialdir=inicial,
            filetypes=[
                ("Audio y ZIP", "*.flac *.wav *.aiff *.aif *.alac *.m4a *.mp3 *.ogg *.zip"),
                ("Todos", "*.*"),
            ],
        )
        if not rutas:
            return
        n = 0
        for ruta in rutas:
            base = os.path.basename(ruta)
            try:
                if ruta.lower().endswith(".zip"):
                    with zipfile.ZipFile(ruta) as z:
                        z.extractall(destino)
                else:
                    shutil.copy2(ruta, destino)
                n += 1
                self._log("  importado: %s" % base)
            except Exception as e:
                self._log("  no pude importar %s: %s" % (base, e))
        self._log("=== Importados %d archivo(s) a %s ===" % (n, destino))

    def _avisar_ffmpeg(self):
        if self.ffdir:
            self._log("ffmpeg: OK  (%s)" % self.ffdir)
        else:
            self._log("ffmpeg: no encontrado. Igual podés descargar en «Mejor calidad»,")
            self._log("pero para MP3/M4A/WAV instalá ffmpeg:  winget install Gyan.FFmpeg")

    def _cerrar(self):
        try:
            self.ex_analisis.shutdown(wait=False, cancel_futures=True)
            self.ex_gratis.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass
        guardar_config({"destino": self.var_destino.get(), "formato": self.var_formato.get()})
        self.root.destroy()


def aplicar_tema(root):
    """Colorea la ventana según la edición. Usa el tema «clam» porque es el que
    permite recolorear los widgets ttk (fondo, filas, encabezados, etc.)."""
    t = TEMA
    root.configure(bg=t["bg"])
    est = ttk.Style(root)
    try:
        est.theme_use("clam")
    except Exception:
        pass
    fuente = t["fuente"]
    est.configure(".", background=t["bg"], foreground=t["fg"], font=fuente)
    est.configure("TFrame", background=t["bg"])
    est.configure("TLabel", background=t["bg"], foreground=t["fg"], font=fuente)
    est.configure("TCheckbutton", background=t["bg"], foreground=t["fg"], font=fuente)
    est.map("TCheckbutton", background=[("active", t["bg"])], foreground=[("disabled", t["mute"])])
    est.configure("TButton", background=t["panel"], foreground=t["fg"], bordercolor=t["line"],
                  lightcolor=t["panel"], darkcolor=t["panel"], font=fuente, relief="flat")
    est.map("TButton",
            background=[("active", t["line2"]), ("pressed", t["sel"]), ("disabled", t["bar"])],
            foreground=[("disabled", t["mute"])])
    est.configure("Pri.TButton", background=t["accent"], foreground=t["onc"],
                  bordercolor=t["accent"], lightcolor=t["accent"], darkcolor=t["accent"],
                  font=(fuente[0], fuente[1], "bold"), padding=(8, 3), relief="flat")
    est.map("Pri.TButton",
            background=[("active", t["accent"]), ("pressed", t["accent"]), ("disabled", t["bar"])],
            foreground=[("disabled", t["mute"])])
    est.configure("TEntry", fieldbackground=t["panel"], foreground=t["fg"],
                  bordercolor=t["line"], insertcolor=t["fg"], font=fuente)
    est.configure("TSpinbox", fieldbackground=t["panel"], background=t["panel"],
                  foreground=t["fg"], arrowcolor=t["fg"], bordercolor=t["line"], font=fuente)
    est.configure("TCombobox", fieldbackground=t["panel"], background=t["panel"],
                  foreground=t["fg"], arrowcolor=t["fg"], bordercolor=t["line"], font=fuente)
    est.map("TCombobox", fieldbackground=[("readonly", t["panel"])],
            foreground=[("readonly", t["fg"])])
    est.configure("Treeview", background=t["panel"], fieldbackground=t["panel"],
                  foreground=t["fg"], bordercolor=t["line"], font=fuente, rowheight=21)
    est.configure("Treeview.Heading", background=t["th"], foreground=t["head"],
                  bordercolor=t["line"], font=fuente, relief="flat")
    est.map("Treeview.Heading", background=[("active", t["line2"])])
    est.map("Treeview", background=[("selected", t["sel"])], foreground=[("selected", t["selfg"])])
    # En la columna #0 va el cuadradito/el botón como imagen. Sacando el
    # «indicador» (la flechita de expandir) el ícono queda pegado a la izquierda.
    try:
        est.layout("Treeview.Item", [
            ("Treeitem.padding", {"sticky": "nswe", "children": [
                ("Treeitem.image", {"side": "left", "sticky": ""}),
                ("Treeitem.text", {"side": "left", "sticky": ""}),
            ]}),
        ])
    except Exception:
        pass
    est.configure("TProgressbar", background=t["accent"], troughcolor=t["panel"],
                  bordercolor=t["line"], lightcolor=t["accent"], darkcolor=t["accent"])
    est.configure("TNotebook", background=t["bg"], bordercolor=t["line"], tabmargins=(2, 4, 2, 0))
    est.configure("TNotebook.Tab", background=t["panel"], foreground=t["fg"],
                  bordercolor=t["line"], lightcolor=t["panel"], darkcolor=t["panel"],
                  padding=(14, 6), font=fuente)
    est.map("TNotebook.Tab",
            background=[("selected", t["sel"]), ("active", t["line2"])],
            foreground=[("selected", t["selfg"])])
    for orient in ("Vertical", "Horizontal"):
        est.configure(orient + ".TScrollbar", background=t["line2"], troughcolor=t["bg"],
                      bordercolor=t["line"], arrowcolor=t["fg"], relief="flat")
        est.map(orient + ".TScrollbar", background=[("active", t["sel"])])


def main():
    root = tk.Tk()
    root.title(APP)
    aplicar_tema(root)
    Recuperador(root)
    root.mainloop()


if __name__ == "__main__":
    main()
