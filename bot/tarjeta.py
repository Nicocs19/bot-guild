# Tarjeta de bienvenida (imagen) con foto de fondo, avatar y nombre.
# Cambiá el fondo reemplazando recursos/fondo_bienvenida.jpg (cualquier imagen apaisada).
import io
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

CARPETA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recursos")
ANCHO, ALTO = 1100, 420
DORADO = (232, 196, 104)
BLANCO = (255, 255, 255)
GRIS = (215, 205, 185)


def _fuente(tam, peso=700):
    for ruta in (os.path.join(CARPETA, "Cinzel.ttf"), "C:/Windows/Fonts/georgiab.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"):
        try:
            f = ImageFont.truetype(ruta, tam)
            try:
                f.set_variation_by_axes([peso])
            except Exception:
                pass
            return f
        except OSError:
            continue
    return ImageFont.load_default()


def _ajustar(draw, texto, tam, ancho_max, peso=700):
    while tam > 18:
        f = _fuente(tam, peso)
        if draw.textlength(texto, font=f) <= ancho_max:
            return f
        tam -= 2
    return _fuente(tam, peso)


def _centrado(draw, y, texto, fuente, color, sombra=True):
    w = draw.textlength(texto, font=fuente)
    x = (ANCHO - w) / 2
    if sombra:
        draw.text((x + 2, y + 3), texto, font=fuente, fill=(0, 0, 0, 200))
    draw.text((x, y), texto, font=fuente, fill=color)


def crear_tarjeta(avatar_bytes: bytes, nombre: str, titulo: str, subtitulo: str) -> io.BytesIO:
    # Fondo: recorte tipo "cover", desenfoque suave y oscurecido
    fondo = Image.open(os.path.join(CARPETA, "fondo_bienvenida.jpg")).convert("RGB")
    escala = max(ANCHO / fondo.width, ALTO / fondo.height)
    fondo = fondo.resize((int(fondo.width * escala) + 1, int(fondo.height * escala) + 1))
    x0, y0 = (fondo.width - ANCHO) // 2, (fondo.height - ALTO) // 2
    img = fondo.crop((x0, y0, x0 + ANCHO, y0 + ALTO)).filter(ImageFilter.GaussianBlur(2)).convert("RGBA")
    velo = Image.new("RGBA", (ANCHO, ALTO), (10, 8, 6, 0))
    vd = ImageDraw.Draw(velo)
    for y in range(ALTO):  # degradé: más oscuro abajo
        vd.line([(0, y), (ANCHO, y)], fill=(10, 8, 6, int(90 + 110 * y / ALTO)))
    img = Image.alpha_composite(img, velo)

    # Marco dorado fino
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((14, 14, ANCHO - 14, ALTO - 14), radius=22, outline=DORADO + (230,), width=3)
    d.rounded_rectangle((22, 22, ANCHO - 22, ALTO - 22), radius=18, outline=DORADO + (90,), width=1)

    # Avatar redondo con anillo dorado y brillo
    tam = 170
    av = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA").resize((tam, tam))
    mascara = Image.new("L", (tam, tam), 0)
    ImageDraw.Draw(mascara).ellipse((0, 0, tam, tam), fill=255)
    cx, cy = ANCHO // 2, 40 + tam // 2
    brillo = Image.new("RGBA", (ANCHO, ALTO), (0, 0, 0, 0))
    ImageDraw.Draw(brillo).ellipse((cx - tam // 2 - 26, cy - tam // 2 - 26, cx + tam // 2 + 26, cy + tam // 2 + 26),
                                   fill=DORADO + (110,))
    img = Image.alpha_composite(img, brillo.filter(ImageFilter.GaussianBlur(18)))
    d = ImageDraw.Draw(img)
    d.ellipse((cx - tam // 2 - 7, cy - tam // 2 - 7, cx + tam // 2 + 7, cy + tam // 2 + 7), fill=(20, 16, 10), outline=DORADO, width=5)
    img.paste(av, (cx - tam // 2, cy - tam // 2), mascara)

    # Textos
    d = ImageDraw.Draw(img)
    _centrado(d, 238, titulo.upper(), _fuente(24, 700), DORADO)
    _centrado(d, 270, nombre, _ajustar(d, nombre, 58, ANCHO - 140, 800), BLANCO)
    _centrado(d, 350, subtitulo, _fuente(24, 600), GRIS)

    salida = io.BytesIO()
    img.convert("RGB").save(salida, "PNG", optimize=True)
    salida.seek(0)
    return salida


def crear_cabecera(titulo: str, etiqueta: str = "", fondo: str = "fondo_anuncio.jpg") -> io.BytesIO:
    """Banner 1200x420 para anuncios: fondo de WoW, marco dorado, logo y título grande."""
    W, H = 1200, 420
    img = Image.open(os.path.join(CARPETA, fondo)).convert("RGB")
    escala = max(W / img.width, H / img.height)
    img = img.resize((int(img.width * escala) + 1, int(img.height * escala) + 1))
    x0, y0 = (img.width - W) // 2, (img.height - H) // 2
    img = img.crop((x0, y0, x0 + W, y0 + H)).convert("RGBA")
    velo = Image.new("RGBA", (W, H))
    vd = ImageDraw.Draw(velo)
    for y in range(H):
        vd.line([(0, y), (W, y)], fill=(8, 6, 4, int(70 + 130 * y / H)))
    img = Image.alpha_composite(img, velo)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((14, 14, W - 14, H - 14), radius=22, outline=DORADO + (230,), width=3)
    d.rounded_rectangle((22, 22, W - 22, H - 22), radius=18, outline=DORADO + (90,), width=1)
    # logo redondo arriba al centro
    ruta_logo = os.path.join(CARPETA, "logo.jpg")
    if os.path.exists(ruta_logo):
        t = 120
        logo = Image.open(ruta_logo).convert("RGBA").resize((t, t))
        m = Image.new("L", (t, t), 0)
        ImageDraw.Draw(m).ellipse((0, 0, t, t), fill=255)
        cx = W // 2
        glow = Image.new("RGBA", (W, H))
        ImageDraw.Draw(glow).ellipse((cx - t // 2 - 20, 40 - 20, cx + t // 2 + 20, 40 + t + 20), fill=DORADO + (100,))
        img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(16)))
        d = ImageDraw.Draw(img)
        d.ellipse((cx - t // 2 - 5, 35, cx + t // 2 + 5, 45 + t), outline=DORADO, width=4)
        img.paste(logo, (cx - t // 2, 40), m)
    d = ImageDraw.Draw(img)
    if etiqueta:
        _centrado_w(d, W, 190, f"— {etiqueta.upper()} —", _fuente(26, 700), DORADO)
    # título en hasta 2 líneas
    palabras, lineas, actual = titulo.split(), [], ""
    f = _fuente(64, 800)
    for p in palabras:
        prueba = (actual + " " + p).strip()
        if d.textlength(prueba, font=f) > W - 160 and actual:
            lineas.append(actual)
            actual = p
        else:
            actual = prueba
    lineas.append(actual)
    lineas = lineas[:2]
    y = 235 if len(lineas) == 1 else 225
    tam = 64 if len(lineas) == 1 else 52
    for linea in lineas:
        fl = _ajustar(d, linea, tam, W - 120, 800)
        _centrado_w(d, W, y, linea, fl, BLANCO)
        y += tam + 12
    salida = io.BytesIO()
    img.convert("RGB").save(salida, "PNG", optimize=True)
    salida.seek(0)
    return salida


def _centrado_w(draw, W, y, texto, fuente, color):
    w = draw.textlength(texto, font=fuente)
    x = (W - w) / 2
    draw.text((x + 2, y + 3), texto, font=fuente, fill=(0, 0, 0, 200))
    draw.text((x, y), texto, font=fuente, fill=color)
