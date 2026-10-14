# -*- coding: utf-8 -*-
"""Genera varias propuestas de logo (pluma) para comparar. Sólo desarrollo."""
import math
import os

from PIL import Image, ImageDraw

S = 1024
OUT = "variantes_logo"
os.makedirs(OUT, exist_ok=True)


def mezcla(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def fondo(forma, arriba, abajo, radio=0.22):
    grad = Image.new("RGB", (S, S))
    gd = ImageDraw.Draw(grad)
    for y in range(S):
        gd.line([(0, y), (S, y)], fill=mezcla(arriba, abajo, y / (S - 1)))
    mascara = Image.new("L", (S, S), 0)
    md = ImageDraw.Draw(mascara)
    if forma == "circulo":
        md.ellipse([0, 0, S - 1, S - 1], fill=255)
    else:
        md.rounded_rectangle([0, 0, S - 1, S - 1], radius=int(S * radio), fill=255)
    base = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    base.paste(grad, (0, 0), mascara)
    return base


def pluma(relleno, raquis, barba, solo_trazo=False):
    capa = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)

    p0 = (0.30 * S, 0.85 * S)
    p1 = (0.84 * S, 0.14 * S)
    ax, ay = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(ax, ay)
    ux, uy = ax / L, ay / L
    nx, ny = -uy, ux
    t_ini, ancho = 0.22, 0.170 * S

    def centro(t):
        return (p0[0] + ax * t, p0[1] + ay * t)

    def semi(t):
        if t < t_ini:
            return 0.0
        s = (t - t_ini) / (1 - t_ini)
        return ancho * (math.sin(math.pi * s) ** 0.8)

    pasos = 240
    contorno = []
    for i in range(pasos + 1):
        t = t_ini + (1 - t_ini) * i / pasos
        cx, cy = centro(t)
        h = semi(t)
        contorno.append((cx + nx * h, cy + ny * h))
    for i in range(pasos + 1):
        t = 1 - (1 - t_ini) * i / pasos
        cx, cy = centro(t)
        h = semi(t)
        contorno.append((cx - nx * h, cy - ny * h))

    if solo_trazo:
        d.line(contorno + [contorno[0]], fill=relleno, width=int(S * 0.018), joint="curve")
    else:
        d.polygon(contorno, fill=relleno)
        # Barbas suaves.
        for i in range(1, 14):
            t = t_ini + (1 - t_ini) * i / 14
            cx, cy = centro(t)
            h = semi(t)
            for signo in (1, -1):
                x0 = cx + signo * nx * h * 0.10 + ux * 0.015 * S
                y0 = cy + signo * ny * h * 0.10 + uy * 0.015 * S
                x1 = cx + signo * nx * h * 0.94 + ux * 0.045 * S
                y1 = cy + signo * ny * h * 0.94 + uy * 0.045 * S
                d.line([(x0, y0), (x1, y1)], fill=barba, width=int(S * 0.006))

    # Cañón (raquis).
    d.line([p0, p1], fill=raquis, width=int(S * 0.015))
    if not solo_trazo:
        d.ellipse(
            [p0[0] - 0.019 * S, p0[1] - 0.019 * S, p0[0] + 0.019 * S, p0[1] + 0.019 * S],
            fill=raquis,
        )
    return capa


VARIANTES = {
    "1": dict(nombre="Teal (propuesta base)", forma="cuadro", arriba=(20, 168, 134),
              abajo=(6, 58, 55), relleno=(246, 244, 237), raquis=(214, 178, 116),
              barba=(228, 221, 205)),
    "2": dict(nombre="Noche (azul profundo)", forma="cuadro", arriba=(40, 52, 98),
              abajo=(11, 15, 34), relleno=(240, 242, 248), raquis=(150, 170, 230),
              barba=(200, 210, 235)),
    "3": dict(nombre="Dorada", forma="cuadro", arriba=(58, 44, 18),
              abajo=(18, 13, 7), relleno=(231, 177, 73), raquis=(120, 84, 26),
              barba=(206, 150, 52)),
    "4": dict(nombre="Círculo teal", forma="circulo", arriba=(20, 168, 134),
              abajo=(6, 58, 55), relleno=(246, 244, 237), raquis=(214, 178, 116),
              barba=(228, 221, 205)),
    "5": dict(nombre="Trazo neón (solo línea)", forma="cuadro", arriba=(12, 30, 28),
              abajo=(5, 15, 15), relleno=(110, 231, 199), raquis=(110, 231, 199),
              barba=(110, 231, 199), solo_trazo=True),
    "6": dict(nombre="Clara (fondo crema)", forma="cuadro", arriba=(247, 245, 238),
              abajo=(223, 230, 226), relleno=(15, 108, 88), raquis=(198, 150, 74),
              barba=(36, 142, 118)),
}


def main():
    for clave, v in VARIANTES.items():
        base = fondo(v["forma"], v["arriba"], v["abajo"])
        capa = pluma(v["relleno"], v["raquis"], v["barba"], v.get("solo_trazo", False))
        out = Image.alpha_composite(base, capa).resize((512, 512), Image.LANCZOS)
        out.save(os.path.join(OUT, "pluma_%s.png" % clave))
    print("generadas %d variantes en %s/" % (len(VARIANTES), OUT))


if __name__ == "__main__":
    main()
