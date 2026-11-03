# ============================================================
#  CONTROL REMOTO DE HOGGER
#  Lo usa Claude desde tu PC para hacer cosas en el Discord sin que
#  vos toques nada. Usa el mismo token del archivo .env (nunca sale de tu PC).
#
#  Ejemplos:
#    python control.py canales
#    python control.py roles
#    python control.py anuncio --canal anuncios-guild --titulo "Hola" --texto "..." [--mencionar "Eventos de la guild"] [--imagen URL]
#    python control.py anuncio --canal anuncios-guild --titulo "Hola" --archivo texto.txt
#         [--tipo sorteo] [--campo "🏆 Premio|3 semanas"] [--boton-texto "Ir al sorteo" --boton-link LINK]
#         [--imagen-archivo banner.png] [--sin-cabecera] [--editar LINK_DEL_ANUNCIO]
#    python control.py mensaje --canal general --texto "..."
#    python control.py crear-rol "Nombre" [--color FFAA00] [--mencionable]
#    python control.py editar-rol "Nombre" [--nombre-nuevo X] [--color FFAA00] [--mencionable si|no]
#    python control.py borrar-rol "Nombre"
# ============================================================
import argparse
import asyncio
import os
import sys

import discord
from dotenv import load_dotenv

import config

CARPETA = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(CARPETA, ".env"))
TOKEN = (os.getenv("DISCORD_TOKEN") or "").strip()
GUILD_ID = int((os.getenv("GUILD_ID") or "0").strip() or 0)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def buscar_canal(canales, nombre):
    nombre = nombre.lstrip("#").lower()
    for c in canales:
        if isinstance(c, discord.TextChannel) and (c.name.lower() == nombre or str(c.id) == nombre):
            return c
    sys.exit(f"No encontré el canal '{nombre}'. Usá: python control.py canales")


def buscar_rol(guild, nombre):
    for r in guild.roles:
        if r.name.lower() == nombre.lower() or str(r.id) == nombre:
            return r
    return None


def color(hexa):
    return discord.Colour(int(hexa.lstrip("#"), 16))


TIPOS = {  # icono, color, etiqueta
    "aviso": ("📢", config.COLOR, "Aviso"),
    "evento": ("🎉", 0x2ECC71, "Evento"),
    "importante": ("⚠️", 0xE74C3C, "Importante"),
    "parche": ("📜", 0x3498DB, "Parche / Novedades"),
    "sorteo": ("🎁", 0xF1C40F, "Sorteo"),
}


def armar_anuncio(a, texto):
    icono, col, etiqueta = TIPOS.get(a.tipo, TIPOS["aviso"])
    e = discord.Embed(title=f"{icono} {a.titulo}", description=texto, color=col)
    e.set_footer(text=f"{etiqueta} · {config.PIE}")
    for campo in a.campo or []:
        nombre, _, valor = campo.partition("|")
        e.add_field(name=nombre.strip(), value=valor.strip() or "\u200b", inline=True)
    archivo = None
    if a.imagen_archivo:
        ext = os.path.splitext(a.imagen_archivo)[1].lower() or ".png"
        archivo = discord.File(a.imagen_archivo, filename="banner" + ext)
    elif a.imagen:
        e.set_image(url=a.imagen)
    elif not a.sin_cabecera:
        try:
            import tarjeta
            archivo = discord.File(tarjeta.crear_cabecera(a.titulo, etiqueta), filename="banner.png")
        except Exception as err:
            print("No pude crear la cabecera:", repr(err))
    if archivo:
        e.set_image(url=f"attachment://{archivo.filename}")
    vista = None
    if a.boton_link:
        vista = discord.ui.View()
        vista.add_item(discord.ui.Button(label=a.boton_texto or "Ir", url=a.boton_link, emoji="👉"))
    return e, archivo, vista


async def main(a):
    client = discord.Client(intents=discord.Intents.none())
    await client.login(TOKEN)
    try:
        guild = await client.fetch_guild(GUILD_ID)
        if a.accion == "canales":
            for c in await guild.fetch_channels():
                if isinstance(c, discord.TextChannel):
                    print(f"#{c.name}  ({c.category.name if c.category else '-'})")
        elif a.accion == "roles":
            for r in sorted(guild.roles, key=lambda r: r.position, reverse=True):
                print(f"{r.position:>3}  {r.name}  color=#{r.colour.value:06X}  mencionable={r.mentionable}")
        elif a.accion in ("anuncio", "mensaje"):
            canal = buscar_canal(await guild.fetch_channels(), a.canal)
            texto = a.texto or ""
            if a.archivo:
                with open(a.archivo, encoding="utf-8") as f:
                    texto = f.read()
            mencion = None
            if a.mencionar:
                mencion = "@everyone" if a.mencionar.lower() in ("everyone", "@everyone") else (
                    buscar_rol(guild, a.mencionar).mention if buscar_rol(guild, a.mencionar) else None)
            permitido = discord.AllowedMentions(everyone=True, roles=True)
            if a.accion == "anuncio":
                e, archivo, vista = armar_anuncio(a, texto)
                extra = {"view": vista} if vista else {}
                if a.editar:
                    # editar un anuncio ya publicado (no vuelve a notificar a nadie)
                    _, cid, mid = a.editar.rstrip("/").split("/")[-3:]
                    canal = await client.fetch_channel(int(cid))
                    m = await canal.fetch_message(int(mid))
                    await m.edit(embed=e, attachments=[archivo] if archivo else [], **extra)
                    print("Editado:", m.jump_url)
                    return
                m = await canal.send(content=mencion, embed=e, allowed_mentions=permitido,
                                     **({"file": archivo} if archivo else {}), **extra)
            else:
                m = await canal.send(content=((mencion + " ") if mencion else "") + texto, allowed_mentions=permitido)
            print("Publicado:", m.jump_url)
        elif a.accion == "crear-rol":
            r = await guild.create_role(name=a.nombre, colour=color(a.color) if a.color else discord.Colour.default(),
                                        mentionable=a.mencionable, reason="Claude vía Hogger")
            print("Rol creado:", r.name)
        elif a.accion == "editar-rol":
            r = buscar_rol(guild, a.nombre) or sys.exit("No existe ese rol.")
            cambios = {}
            if a.nombre_nuevo:
                cambios["name"] = a.nombre_nuevo
            if a.color:
                cambios["colour"] = color(a.color)
            if a.mencionable:
                cambios["mentionable"] = a.mencionable == "si"
            await r.edit(reason="Claude vía Hogger", **cambios)
            print("Rol editado:", a.nombre, cambios)
        elif a.accion == "borrar-rol":
            r = buscar_rol(guild, a.nombre) or sys.exit("No existe ese rol.")
            await r.delete(reason="Claude vía Hogger")
            print("Rol borrado:", a.nombre)
    finally:
        await client.close()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest="accion", required=True)
    sp.add_parser("canales")
    sp.add_parser("roles")
    for n in ("anuncio", "mensaje"):
        x = sp.add_parser(n)
        x.add_argument("--canal", required=True)
        x.add_argument("--texto")
        x.add_argument("--archivo")
        x.add_argument("--mencionar")
        if n == "anuncio":
            x.add_argument("--titulo", required=True)
            x.add_argument("--imagen", help="link a una imagen")
            x.add_argument("--imagen-archivo", help="imagen de la PC para el banner")
            x.add_argument("--sin-cabecera", action="store_true", help="no generar el banner automático")
            x.add_argument("--tipo", default="aviso", choices=["aviso", "evento", "importante", "parche", "sorteo"])
            x.add_argument("--campo", action="append", help="'Nombre|Valor' (se puede repetir)")
            x.add_argument("--boton-texto")
            x.add_argument("--boton-link", help="link del botón (ej: link del mensaje del sorteo)")
            x.add_argument("--editar", help="link de un anuncio ya publicado para reemplazarlo sin notificar")
    x = sp.add_parser("crear-rol"); x.add_argument("nombre"); x.add_argument("--color"); x.add_argument("--mencionable", action="store_true")
    x = sp.add_parser("editar-rol"); x.add_argument("nombre"); x.add_argument("--nombre-nuevo"); x.add_argument("--color"); x.add_argument("--mencionable", choices=["si", "no"])
    x = sp.add_parser("borrar-rol"); x.add_argument("nombre")
    args = p.parse_args()
    if not TOKEN or not GUILD_ID:
        sys.exit("Falta DISCORD_TOKEN o GUILD_ID en el archivo .env")
    asyncio.run(main(args))
