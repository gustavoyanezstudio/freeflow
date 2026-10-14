╔══════════════════════════════════════════════╗
║                                              ║
║      ____               ______               ║
║     / __/_______  ___  / __/ /___ _      __  ║
║    / /_/ ___/ _ \/ _ \/ /_/ / __ \ | /| / /  ║
║   / __/ /  /  __/  __/ __/ / /_/ / |/ |/ /   ║
║  /_/ /_/   \___/\___/_/ /_/\____/|__/|__/    ║
║                                              ║
║                                              ║
╚══════════════════════════════════════════════╝

  freeflow - descargador de audio / audio downloader

  Portable: no hay que instalar nada. Hay versión para Windows de 64 bits y
  para Mac (Apple Silicon e Intel).
  Portable: nothing to install. Builds for Windows 64-bit and Mac (Apple
  Silicon and Intel).


================================================================================
  ESPAÑOL
================================================================================


QUÉ ES
------
  freeflow es un programita de escritorio para buscar, elegir y bajar
  audio y sets. Es simple, portable y no se mete con nada que tenga
  precio.


LO QUE TRAE
-----------
  - Cuatro fuentes en una: SoundCloud, YouTube, Mixcloud y Bandcamp.
  - Varias búsquedas a la vez, cada una en su propia pestaña.
  - Análisis de fondo: va rellenando formato, calidad y peso de cada resultado
    mientras tú sigues mirando (lo puedes parar con "Detener análisis").
  - Mientras busca, va mostrando una estimación al instante del peso de cada
    resultado.
  - Marcas con el cuadradito y ves el peso total de lo que llevas elegido.
  - Modo por defecto pensado para no recomprimir ni inflar el audio (ver más
    abajo), más la opción "Descargar original" para bajar en FLAC/WAV.
  - Bandcamp gratis ("name your price") con un botón directo a la página
    oficial.
  - Todo queda en tu computador; no se sube nada a ninguna parte.


CÓMO SE USA
-----------
  1. Abre el programa (doble clic en el .exe o en la .app).
  2. Escribe uno o varios términos, uno por línea, en el campo de búsqueda.
  3. Elige las fuentes y cuántos resultados por término (por defecto 70, hasta
     200).
  4. Haz clic en Buscar (o en el logo de la pluma del botón, que también
     busca).
  5. Elige lo que quieras bajar marcando el cuadradito de la izquierda de cada
     fila (o "Marcar todos").
  6. Elige la carpeta destino y el formato, y haz clic en "Descargar
     seleccionados".


PESTAÑAS
--------
  Cada búsqueda abre su propia pestaña, así puedes tener varias corriendo a la
  vez y volver a una anterior sin perder nada. "Cerrar búsqueda" cierra la
  pestaña actual (y si esa búsqueda todavía estaba corriendo, la detiene).


FORMATOS Y CALIDAD
------------------
  El programa baja la mejor calidad que entregue la fuente y NO infla nada.
  Cada plataforma tiene su techo:

    - SoundCloud : hasta AAC ~160 kbps (es el techo de la plataforma).
    - YouTube    : Opus ~130 kbps.
    - Mixcloud   : MP3/AAC de streaming (depende de quien lo subió).
    - Bandcamp   : stream MP3 128; si la descarga está habilitada, hay FLAC/WAV.

  Pasar un audio de 160 kbps a "MP3 320" no mejora el sonido: solo agranda el
  archivo (una hora pasa de unos 64 MB a unos 130 MB). Por eso el modo por
  defecto baja el stream tal cual, sin recomprimir.

  Está la opción "320 + tag de origen (para canciones)", que deja anotado en
  el nombre del archivo de dónde vino el audio (por ejemplo, "(origen 128
  kbps)"), para que sepas siempre qué es lo que tienes.

  Si el/la artista habilitó el archivo original (FLAC, WAV, AIFF o ALAC), usa
  "Descargar original": baja esa versión sin recomprimir y no pisa el MP3
  (cambia la extensión).


BANDCAMP GRATIS ("NAME YOUR PRICE")
-----------------------------------
  Cuando una pista o un disco de Bandcamp se puede conseguir gratis (precio
  mínimo $0), la fila queda destacada con "GRATIS" y, al lado del cuadradito,
  le aparece un botón verde con una flecha (solo en esas filas).

  Ese botón abre la página oficial de descarga para que completes $0 y elijas
  el formato, ojalá FLAC. La bajada la confirmas tú en el navegador.

  Nunca se toca nada que tenga precio.


IMPORTAR LO QUE BAJASTE
-----------------------
  Si bajaste algo con el navegador (por ejemplo un FLAC de Bandcamp, o el
  .zip completo de un disco), usa "Importar…" para traerlo a tu carpeta
  destino. Si es un .zip, además lo descomprime.


DÓNDE QUEDAN LOS ARCHIVOS
-------------------------
  En la carpeta que elijas. Por defecto, una carpeta propia dentro de Música
  ("Freeflow Downloads"). Los archivos se guardan como "Subido por - Título [id].ext".


REQUISITOS
----------
  - Windows de 64 bits o Mac (Apple Silicon e Intel).
  - Conexión a internet.
  - Nada más: el programa ya trae todo lo que necesita adentro.

  ¿En un Mac? Elige el archivo según el equipo:

    - El .dmg que NO dice "legacy": Apple Silicon (M1 o más nuevo) o Intel
      moderno. En Apple Silicon pide macOS 12 o más.
    - El -legacy.dmg: Mac Intel más antiguos (desde macOS 10.13, High
      Sierra / Catalina). En Apple Silicon también corre, con Rosetta 2.

  Si no sabes cuál te toca, usa el -legacy: corre en todos los Mac desde 10.13.


PREGUNTAS FRECUENTES
--------------------
  - "¿Por qué no puedo bajar en FLAC/WAV de SoundCloud o YouTube?"
    Porque esas plataformas solo entregan audio con pérdida. El original sin
    pérdida no existe ahí, y fabricarlo no mejora el sonido.

  - "¿Se escucha mejor en 320 que en 160?"
    No. Subir los kbps no agrega información que no estaba. Suena igual, pero
    ocupa el doble (o más).

  - "¿Se puede bajar de YouTube?"
    Sí. En algunos casos YouTube pide un "runtime de JavaScript" para ofrecer
    ciertos formatos; si algún día falla, se instala uno (por ejemplo deno) y
    listo. SoundCloud, Mixcloud y Bandcamp no tienen ese problema.

  - "¿Esto evade pagos?"
    No. Solo se ofrece lo gratuito y lo que la fuente entrega públicamente.
    Nada que tenga precio se toca.

  - "¿Sirve para bajar discografías enteras?"
    Sí, pero con cabeza: baja de a poco y apoya a quien corresponda. No es un
    bot de raspado masivo.


APOYA A LOS/AS ARTISTAS
-----------------------
  Esto es para buscar, escuchar y compartir. Si algo te gusta, apóyalos:
  compra en Bandcamp, sigue a quien lo subió, anda a sus toques, comparte. La
  música es de quienes la hacen.

  Este programa no te da música "gratis" para que no pagues: te ayuda a
  llegar a ella. Si puedes pagar, paga.


ES DE TODOS
-----------
  Este programa no es de nadie y es de todos. No lo vendas: cópialo y
  compártelo, respetando siempre a los/as artistas.


================================================================================
  ENGLISH
================================================================================


WHAT IT IS
----------
  freeflow is a small desktop app to search, pick and download audio
  and sets. It's simple, portable, and it never touches anything with
  a price.


WHAT IT BRINGS
--------------
  - Four sources in one: SoundCloud, YouTube, Mixcloud and Bandcamp.
  - Several searches at once, each in its own tab.
  - Background analysis: it fills in the format, quality and size of every
    result while you keep browsing (stop it anytime with "Stop analysis").
  - While searching, it shows an instant estimate of each result's size.
  - Tick the checkbox and see the total size of what you've picked.
  - A default mode built not to re-encode or inflate the audio (see below),
    plus the "Download original" option to grab FLAC/WAV.
  - Free Bandcamp ("name your price") with a direct button to the official
    page.
  - Everything stays on your computer; nothing is uploaded anywhere.


HOW TO USE
----------
  1. Open the program (double-click the .exe or the .app).
  2. Type one or more terms, one per line, in the search box.
  3. Pick the sources and how many results per term (70 by default, up to
     200).
  4. Hit Search (or the quill logo on the button, which also searches).
  5. Pick what you want to download by ticking the checkbox on the left of
     each row (or "Mark all").
  6. Choose the destination folder and the format, then "Download selected".


TABS
----
  Each search opens its own tab, so you can run several at once and go back to
  an earlier one without losing anything. "Close search" closes the current
  tab (and stops it if that search was still running).


FORMATS AND QUALITY
-------------------
  The app downloads the best quality the source gives and does NOT inflate
  anything. Every platform has its ceiling:

    - SoundCloud : up to AAC ~160 kbps (the platform's ceiling).
    - YouTube    : Opus ~130 kbps.
    - Mixcloud   : streaming MP3/AAC (depends on the uploader).
    - Bandcamp   : MP3 128 stream; if downloads are enabled, FLAC/WAV.

  Turning a 160 kbps audio into "MP3 320" doesn't improve the sound, it just
  makes the file bigger (an hour goes from about 64 MB to about 130 MB). That's
  why the default mode keeps the stream as-is, with no re-encoding.

  There's a "320 + source tag (for songs)" option, which notes in the file name
  where the audio came from (for example, "(source 128 kbps)"), so you always
  know what you have.

  If the artist enabled the original file (FLAC, WAV, AIFF or ALAC), use
  "Download original": it gets that version with no re-encoding and doesn't
  overwrite the MP3 (the extension changes).


FREE BANDCAMP ("NAME YOUR PRICE")
---------------------------------
  When a Bandcamp track or album can be had for free (minimum price $0), the
  row is highlighted with "GRATIS" and, next to the checkbox, a small green
  arrow button appears (only on those rows).

  That button opens the official download page so you can complete $0 and
  choose the format, ideally FLAC. You confirm the download yourself in the
  browser.

  Nothing with a price is ever touched.


IMPORT WHAT YOU DOWNLOADED
--------------------------
  If you downloaded something with your browser (say a FLAC from Bandcamp, or
  a whole album's .zip), use "Import…" to bring it into your destination
  folder. If it's a .zip, it also unpacks it.


WHERE THE FILES GO
------------------
  In the folder you choose. By default, its own folder under Music
  ("Freeflow Downloads"). Files are saved as "Uploaded by - Title [id].ext".


REQUIREMENTS
------------
  - Windows 64-bit or Mac (Apple Silicon and Intel).
  - An internet connection.
  - Nothing else: the program already brings everything it needs inside.

  On a Mac? Download the file that matches your machine:

    - The .dmg that does NOT say "legacy": Apple Silicon (M1 or newer) or
      modern Intel. On Apple Silicon it needs macOS 12 or later.
    - The -legacy.dmg: older Intel Macs (from macOS 10.13, High Sierra /
      Catalina). On Apple Silicon it also runs, via Rosetta 2.

  If you're not sure, use the -legacy one: it runs on every Mac from 10.13.


FREQUENTLY ASKED QUESTIONS
--------------------------
  - "Why can't I get FLAC/WAV from SoundCloud or YouTube?"
    Because those platforms only deliver lossy audio. The lossless original
    doesn't exist there, and faking it wouldn't improve the sound.

  - "Does 320 sound better than 160?"
    No. Raising the bitrate doesn't add information that wasn't there. It
    sounds the same but takes twice the space (or more).

  - "Can I download from YouTube?"
    Yes. In some cases YouTube asks for a "JavaScript runtime" to offer certain
    formats; if it ever fails, you install one (for example deno) and that's
    it. SoundCloud, Mixcloud and Bandcamp don't have that problem.

  - "Does this bypass payments?"
    No. Only free items and what the source delivers publicly are offered.
    Nothing with a price is ever touched.

  - "Can it download whole discographies?"
    Yes, but use your head: download a little at a time and support whoever is
    due. It's not a mass-scraping bot.


SUPPORT THE ARTISTS
-------------------
  This is for searching, listening and sharing. If you like something, support
  them: buy on Bandcamp, follow the uploader, go to their shows, share it.
  Music belongs to the people who make it.

  This isn't about dodging payment: it's about reaching the music. If you can
  pay, pay.


IT BELONGS TO EVERYONE
----------------------
  This program isn't anyone's, it's everyone's. Don't sell it: copy it and
  share it, always respecting the artists.
