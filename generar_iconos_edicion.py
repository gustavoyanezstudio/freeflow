# -*- coding: utf-8 -*-
"""Genera los íconos de cada edición a partir de la pluma elegida.

  freeflow   -> variantes_logo/pluma_1.png  (Teal)
  secretflow -> variantes_logo/pluma_2.png  (Noche)

Produce, por edición:
  <ed>.png       (256x256, ventana / docs)
  <ed>_btn.png   (24x24, botón de buscar)
  <ed>.ico       (multi-tamaño, barra de tareas de Windows)

Sólo se usa al desarrollar; no forma parte del ejecutable.
"""
import os

from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
FUENTES = {
    "freeflow": "variantes_logo/pluma_1.png",
    "secretflow": "variantes_logo/pluma_2.png",
}
TAMANOS = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]


def generar(ed, origen):
    img = Image.open(os.path.join(AQUI, origen)).convert("RGBA")
    grande = img.resize((256, 256), Image.LANCZOS)
    grande.save(os.path.join(AQUI, ed + ".png"))
    img.resize((24, 24), Image.LANCZOS).save(os.path.join(AQUI, ed + "_btn.png"))
    grande.save(os.path.join(AQUI, ed + ".ico"), sizes=TAMANOS)
    print("listo:", ed, "->", ed + ".png / " + ed + "_btn.png / " + ed + ".ico")


if __name__ == "__main__":
    for ed, origen in FUENTES.items():
        generar(ed, origen)
