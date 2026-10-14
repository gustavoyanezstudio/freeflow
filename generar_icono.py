# -*- coding: utf-8 -*-
"""Genera el ícono de freeflow (una pluma) como PNG e ICO de varios tamaños.

Sólo se usa al desarrollar; no forma parte del ejecutable.
"""
import math

from PIL import Image, ImageDraw

S = 1024


def mezcla(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def fondo():
    """Cuadrado redondeado con gradiente vertical verde-teal."""
    grad = Image.new("RGB", (S, S))
    gd = ImageDraw.Draw(grad)
    arriba = (20, 168, 134)
    abajo = (6, 58, 55)
    for y in range(S):
        gd.line([(0, y), (S, y)], fill=mezcla(arriba, abajo, y / (S - 1)))
    mascara = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mascara).rounded_rectangle(
        [0, 0, S - 1, S - 1], radius=int(S * 0.22), fill=255
    )
    base = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    base.paste(grad, (0, 0), mascara)
    return base


def pluma():
    """Una pluma blanca con cañón dorado, inclinada en diagonal."""
    capa = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)

    p0 = (0.30 * S, 0.85 * S)   # base del cañón
    p1 = (0.84 * S, 0.14 * S)   # punta
    ax, ay = p1[0] - p0[0], p1[1] - p0[1]
    largo = math.hypot(ax, ay)
    ux, uy = ax / largo, ay / largo   # eje
    nx, ny = -uy, ux                  # normal

    t_ini = 0.22
    ancho = 0.170 * S

    def centro(t):
        return (p0[0] + ax * t, p0[1] + ay * t)

    def semi(t):
        if t < t_ini:
            return 0.0
        s = (t - t_ini) / (1 - t_ini)
        return ancho * (math.sin(math.pi * s) ** 0.8)

    # Hoja (ida y vuelta por cada lado).
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
    d.polygon(contorno, fill=(246, 244, 237, 255))

    # Barbas: líneas suaves hacia los costados, inclinadas hacia la punta.
    for i in range(1, 16):
        t = t_ini + (1 - t_ini) * i / 16
        cx, cy = centro(t)
        h = semi(t)
        for signo in (1, -1):
            x0 = cx + signo * nx * h * 0.08 + ux * 0.015 * S
            y0 = cy + signo * ny * h * 0.08 + uy * 0.015 * S
            x1 = cx + signo * nx * h * 0.95 + ux * 0.045 * S
            y1 = cy + signo * ny * h * 0.95 + uy * 0.045 * S
            d.line([(x0, y0), (x1, y1)], fill=(228, 221, 205, 255), width=int(S * 0.006))

    # Cañón (raquis) dorado.
    d.line([p0, p1], fill=(214, 178, 116, 255), width=int(S * 0.015))
    d.ellipse(
        [p0[0] - 0.02 * S, p0[1] - 0.02 * S, p0[0] + 0.02 * S, p0[1] + 0.02 * S],
        fill=(214, 178, 116, 255),
    )
    return capa


def main():
    base = Image.alpha_composite(fondo(), pluma())
    base.save("freeflow.png")
    base.save(
        "freeflow.ico",
        sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)],
    )
    print("listo: freeflow.png / freeflow.ico")


if __name__ == "__main__":
    main()
