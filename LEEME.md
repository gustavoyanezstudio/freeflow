# freeflow / secretflow

Descargador de escritorio para **buscar, elegir y descargar** audios y sets en
**SoundCloud**, **YouTube**, **Mixcloud** y **Bandcamp**, en la mejor calidad
disponible y convirtiendo video a audio cuando haga falta.

> **Portable, sin instalar nada.** Cada ejecutable ya trae TODO adentro (Python,
> yt-dlp y **ffmpeg**). Se lo podés mandar a otra persona y funciona igual.
> Hay versión para **Windows de 64 bits** (`.exe`) y para **Mac** (`.app`/`.dmg`,
> Apple Silicon e Intel). En cualquiera de los dos casos necesita internet.

## Dos ediciones

| Edición | Para | Aspecto | Términos al abrir |
|---|---|---|---|
| **`freeflow.exe`** / **`freeflow.app`** | Compartir | «Menta suave» (claro) | Vacío, con el texto guía *«Busca aquí…»* |
| **`secretflow.exe`** / **`secretflow.app`** | Interno (Tectónica Radio) | «Terminal verde» (oscuro) | `tectonica radio`, `tectonica radio set`, `tectonicaradio` |

Cada edición guarda sus descargas por defecto en una carpeta propia bajo
**`Música`** (`Freeflow Downloads` / `Secretflow Downloads`), y recuerda aparte
su última carpeta y su formato.

## Cómo se usa

1. Doble clic en **`freeflow.exe`** (Windows) o **`freeflow.app`** (Mac); lo mismo
   con `secretflow`.
2. Escribí uno o varios **términos** (uno por línea) en el campo *«Busca aquí…»*.
3. Elegí fuentes (**SoundCloud**, **YouTube**, **Mixcloud** y/o **Bandcamp**) y
   cuántos **resultados por término** (por defecto **70**, hasta **200**).
4. Dale a **Buscar** (o al logo de la pluma, que también busca). Los resultados
   aparecen en la pestaña de esa búsqueda. Un analizador de fondo va llenando
   **formato**, **calidad** y **peso** de cada resultado (podés cortarlo con
   **Detener análisis**).
5. Hacé clic en el **cuadradito ✓** de la izquierda para marcar lo que querés
   descargar (o usá «Marcar todos»). Abajo a la derecha ves el **peso total** de
   lo seleccionado.
6. Elegí **carpeta destino** y **formato**, y dale a **Descargar seleccionados**.

Arriba a la derecha está el botón **«¿Cómo se usa?»**, que abre esta misma ayuda
resumida sin salir del programa.

### Pestañas

Cada búsqueda abre su propia **pestaña**, así podés tener varias a la vez y
volver a una anterior sin perder los resultados. **Cerrar búsqueda** cierra la
pestaña actual (y, si esa búsqueda todavía estaba corriendo, la detiene). Podés
lanzar varias búsquedas en paralelo, una por pestaña.

### Descargar original

El botón **Descargar original** baja el archivo **tal cual viene, sin recomprimir
y sin tope de 320** (WAV/FLAC si existen, o la mejor versión disponible). Sirve
para quedarte con la mejor versión **además del MP3**: descargá primero en MP3 y
después tocá «Descargar original» (o al revés); como cambia la extensión, no se
pisan. Si no hay una versión mayor que la del stream, avisa en el registro y baja
igual la mejor disponible.

Todo corre en tu equipo; los archivos quedan en la carpeta que elijas, con el
nombre `Subido por - Título [id].ext`.

## Bandcamp «name your price» (gratis)

Cuando una pista o álbum de Bandcamp se puede conseguir **gratis** (precio
mínimo $0, el clásico *name your price*), la fila queda marcada en color con
**`GRATIS · …`** y, al lado del cuadradito, le aparece un **botón verde con una
flecha** (y **sólo** en esas filas). Ese botón abre la **página oficial de
descarga** para que completes el $0 y elijas el formato, idealmente **FLAC**.

- Sólo se ofrece en ítems **gratis**. **Nunca** se toca nada que tenga precio.
- La bajada la confirmás vos en el navegador (Bandcamp protege esas descargas con
  reCAPTCHA); el programa no la automatiza ni evade esa protección.
- Cuando termina de bajar, tocá **`Importar…`** y elegí el archivo: lo copia a la
  carpeta destino y, si es un `.zip`, lo descomprime.

## Formatos

Por defecto, el programa baja **la mejor calidad disponible hasta 320 kbps y
sin recomprimir**. Ojo con lo que da cada fuente:

- **SoundCloud** ofrece como máximo **AAC 160 kbps** (o MP3 128). No hay más
  para el streaming; es el techo de la plataforma.
- **YouTube** entrega su mejor audio (normalmente **Opus ~130 kbps**).
- **Mixcloud** entrega **MP3/AAC** de streaming (la calidad depende del upload).
- **Bandcamp** entrega el stream **MP3 128**; si el sello habilitó la descarga
  del original, puede haber WAV/FLAC.

| Formato | Qué hace |
|---|---|
| Mejor calidad (hasta 320 kbps, sin recomprimir) | Baja el mejor audio **sin recomprimir** (por defecto) |
| 320 + tag de origen (para canciones) | Convierte a MP3 320 y deja el códec/origen en el nombre |
| MP3 320 kbps | Convierte a MP3 |
| M4A / AAC | Convierte a M4A |
| WAV (sin comprimir) | Convierte a WAV |
| Video MP4 (mejor calidad) | Baja el video |
| **Descargar original** (botón) | Baja el archivo tal cual (WAV/FLAC/…), sin recomprimir |

(ffmpeg ya viene dentro del `.exe`, así que todas las conversiones funcionan sin
instalar nada.)

> **Calidad real:** convertir a MP3 320 un audio que venía a 160 **no mejora
> nada**, sólo agranda el archivo (una hora pasa de ~64 MB a ~130 MB). Por eso
> el modo por defecto baja el stream tal cual. Si el/la artista habilitó la
> **descarga del archivo original** en SoundCloud, se puede conseguir esa versión
> (WAV o 320 real).
>
> **Regla automática:** el programa mira qué hay. Si la mejor fuente ya viene a
> 320 kbps o menos, la guarda **tal cual**. Si encuentra un original sin pérdida
> (WAV/FLAC) o algo por encima de 320, lo baja y lo **convierte a MP3 320**.
> El botón **Descargar original** es la excepción a esa regla: guarda el archivo
> sin recomprimir y sin tope, para conservar la mejor versión.

## Búsqueda

- Elegís **cuántos resultados por término** (por defecto **70**, máximo **200**).
- **SoundCloud** y **YouTube**: búsqueda nativa de yt-dlp.
- **Mixcloud**: API pública de Mixcloud (sin clave).
- **Bandcamp**: API interna de búsqueda de Bandcamp. Su buscador web está detrás
  de un "desafío" JavaScript, pero esta API responde siempre; devuelve pistas y
  álbumes (los álbumes se marcan como `[ÁLBUM]`).

## Requisitos

- **Ninguno instalado**: el ejecutable ya trae **ffmpeg** adentro (además de Python
  y yt-dlp). Para las conversiones no hace falta instalar nada.
- Si querés usar un ffmpeg externo, igual lo busca junto al `.exe`, en una carpeta
  `ffmpeg\` al lado, o en el PATH.
- Conexión a internet. **Windows de 64 bits** o **Mac** (Apple Silicon e Intel).

## Archivos

- `recuperador.py` — el programa (GUI + motor). La edición se detecta por el
  nombre del ejecutable; en desarrollo se puede forzar con la variable de entorno
  `FREEFLOW_EDICION` (`freeflow` o `secretflow`).
- `bin\ffmpeg.exe` — el ffmpeg que se incrusta al compilar (build "essentials").
- `dist\freeflow.exe` — edición para compartir (~55 MB).
- `dist\secretflow.exe` — edición interna (~55 MB).
- `dist\README_freeflow.txt` y `dist\README_secretflow.txt` — la ayuda de cada
  edición, que se entrega junto a su ejecutable (la misma que abre el botón
  **«¿Cómo se usa?»** dentro del programa).
- `Freeflow.spec` / `secretflow.spec` — recetas de compilación para Windows.
- `freeflow_macos.spec` / `secretflow_macos.spec` — recetas para macOS.
- `build_macos.sh` — compila las dos ediciones para Mac y arma los `.dmg`.
- `.github\workflows\build-macos.yml` — compila los `.dmg` en la nube (GitHub
  Actions) sin necesidad de tener un Mac.
- `freeflow.ico` / `secretflow.ico` (y `.png`, `_btn.png`) — íconos de cada edición.
- `.venv\` — entorno con `yt-dlp` y `pyinstaller`.

## Recompilar los .exe

Desde esta carpeta, una edición por vez:

    .venv\Scripts\python.exe -m PyInstaller --noconfirm --clean Freeflow.spec
    .venv\Scripts\python.exe -m PyInstaller --noconfirm --clean secretflow.spec

Cada `.spec` ya incluye el `--collect-all yt_dlp`, el `--add-binary` de ffmpeg,
el ícono y los recursos de esa edición. El resultado queda en `dist\`.

Si te falta `bin\ffmpeg.exe`, bajalo con `pip install imageio-ffmpeg` y copiá el
binario que indica
`python -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"`.

## Compilar para Mac (`.dmg`)

**PyInstaller no compila para macOS desde Windows**: la `.app`/`.dmg` tiene que
armarse **en un Mac**. Están las dos vías:

**a) En un Mac, con un comando.** Desde esta carpeta:

    bash build_macos.sh

Necesita macOS con las herramientas de línea de comandos (`sips`, `iconutil`,
`hdiutil`, que ya vienen con el sistema) y Python 3. El script instala lo que
falta, incrusta un `ffmpeg` de Mac, genera los `.icns`, compila las dos ediciones
y deja **`dist/freeflow.dmg`** y **`dist/secretflow.dmg`**.

**b) En la nube (GitHub Actions), sin tener Mac.** El workflow
`.github/workflows/build-macos.yml` compila los mismos `.dmg` en un runner macOS
de GitHub. Se corre solo (Pestaña **Actions** → **Build macOS DMG** → *Run
workflow*) y los `.dmg` quedan para descargar en **Artifacts**. Hace falta tener
el proyecto en un repositorio de GitHub.

Las apps se generan **universal2** (corren en Apple Silicon y en Intel) y **sin
firmar**: como no hay cuenta Apple de por medio, la primera vez macOS muestra el
aviso de *«desarrollador no identificado»* → se abre con **clic derecho → Abrir**
(una sola vez). Si en algún momento se quiere repartir a gente no técnica, se
puede firmar/notarizar con una cuenta Apple Developer (US$99/año).

## Nota sobre YouTube

yt-dlp avisa que, sin un "runtime de JavaScript", YouTube puede no ofrecer algunos
formatos. Para bajar de YouTube funciona igual en la mayoría de los casos; si algún
día falla, se instala un runtime (por ejemplo `deno`) y listo. **SoundCloud**, que
es la fuente principal de la radio, no tiene ese problema.
