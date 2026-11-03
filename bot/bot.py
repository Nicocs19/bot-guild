# ============================================================
#  HOGGER — el bot propio de The H's
#  No hace falta tocar este archivo. Los textos están en config.py
# ============================================================
import asyncio
import json
import os
import random
import time
from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv

import config

try:
    import tarjeta  # necesita Pillow; si falta, la bienvenida sale sin imagen
except ImportError:
    tarjeta = None
    print("⚠️ Falta Pillow: la bienvenida va a salir sin tarjeta. Corré instalar.bat para arreglarlo.")

CARPETA = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(CARPETA, ".env"))


def leer_ajustes():
    """Busca el token y el ID del server en .env (o en archivos que Windows haya renombrado)."""
    vals = {}
    for nombre in (".env", ".env.txt", "env.txt", "env.example.txt"):
        ruta = os.path.join(CARPETA, nombre)
        if not os.path.exists(ruta):
            continue
        with open(ruta, encoding="utf-8-sig", errors="ignore") as f:
            for linea in f:
                if "=" not in linea or linea.strip().startswith("#"):
                    continue
                k, v = linea.split("=", 1)
                k, v = k.strip().upper(), v.strip().strip('"').strip("'").strip()
                if v and not v.upper().startswith("PEGA") and k not in vals:
                    vals[k] = v
    return vals


def token_valido(t):
    return len(t) > 50 and t.count(".") >= 2


_aj = leer_ajustes()
TOKEN = (_aj.get("DISCORD_TOKEN") or os.getenv("DISCORD_TOKEN") or "").strip()
GUILD_ID = (_aj.get("GUILD_ID") or os.getenv("GUILD_ID") or "").strip()
ARCHIVO_DATOS = os.path.join(CARPETA, "datos.json")


# ---------------- datos guardados (bandas, sorteos, ajustes) ----------------
def cargar_datos():
    try:
        with open(ARCHIVO_DATOS, "r", encoding="utf-8") as f:
            d = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        d = {}
    d.setdefault("ajustes", {})
    d.setdefault("bandas", {})
    d.setdefault("sorteos", {})
    d.setdefault("encuestas", {})
    d.setdefault("raids", {})
    return d


def guardar_datos():
    tmp = ARCHIVO_DATOS + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    os.replace(tmp, ARCHIVO_DATOS)


datos = cargar_datos()


def embed_base(titulo, descripcion=None):
    e = discord.Embed(title=titulo, description=descripcion, color=config.COLOR)
    e.set_footer(text=config.PIE)
    return e


async def responder(it: discord.Interaction, texto: str):
    """Mensaje privado (solo lo ve quien tocó el botón o usó el comando)."""
    if it.response.is_done():
        await it.followup.send(texto, ephemeral=True)
    else:
        await it.response.send_message(texto, ephemeral=True)


# ============================================================
#  ÍCONOS DE WOW (emojis propios del bot, se suben solos la primera vez)
# ============================================================
CARPETA_ICONOS = os.path.join(CARPETA, "recursos", "iconos")
EMO = {}  # nombre -> "<:nombre:id>"
ICONO_CLASE = {"Guerrero": "cls_guerrero", "Paladín": "cls_paladin", "Cazador": "cls_cazador", "Pícaro": "cls_picaro",
               "Sacerdote": "cls_sacerdote", "Chamán": "cls_chaman", "Mago": "cls_mago", "Brujo": "cls_brujo",
               "Druida": "cls_druida"}
ICONO_SPEC = {
    ("Guerrero", "Protección"): "gue_proteccion", ("Guerrero", "Armas"): "gue_armas", ("Guerrero", "Furia"): "gue_furia",
    ("Paladín", "Protección"): "pal_proteccion", ("Paladín", "Sagrado"): "pal_sagrado", ("Paladín", "Reprensión"): "pal_reprension",
    ("Cazador", "Bestias"): "caz_bestias", ("Cazador", "Puntería"): "caz_punteria", ("Cazador", "Supervivencia"): "caz_supervivencia",
    ("Pícaro", "Asesinato"): "pic_asesinato", ("Pícaro", "Combate"): "pic_combate", ("Pícaro", "Sutileza"): "pic_sutileza",
    ("Sacerdote", "Sagrado"): "sac_sagrado", ("Sacerdote", "Disciplina"): "sac_disciplina", ("Sacerdote", "Sombras"): "sac_sombras",
    ("Chamán", "Restauración"): "cha_restauracion", ("Chamán", "Elemental"): "cha_elemental", ("Chamán", "Mejora"): "cha_mejora",
    ("Mago", "Escarcha"): "mag_escarcha", ("Mago", "Fuego"): "mag_fuego", ("Mago", "Arcano"): "mag_arcano",
    ("Brujo", "Aflicción"): "bru_afliccion", ("Brujo", "Demonología"): "bru_demonologia", ("Brujo", "Destrucción"): "bru_destruccion",
    ("Druida", "Feral (oso)"): "dru_oso", ("Druida", "Restauración"): "dru_restauracion", ("Druida", "Feral (gato)"): "dru_gato",
    ("Druida", "Equilibrio"): "dru_equilibrio",
}


def emo(nombre, respaldo=""):
    return EMO.get(nombre, respaldo)


def emo_parcial(nombre, respaldo=None):
    return discord.PartialEmoji.from_str(EMO[nombre]) if nombre in EMO else respaldo


async def sincronizar_iconos(cliente):
    """Sube a la app de Discord los íconos de recursos/iconos que falten (una sola vez)."""
    if not os.path.isdir(CARPETA_ICONOS):
        return
    try:
        existentes = {e.name: e for e in await cliente.fetch_application_emojis()}
        for archivo in sorted(os.listdir(CARPETA_ICONOS)):
            nombre = os.path.splitext(archivo)[0]
            if nombre not in existentes:
                with open(os.path.join(CARPETA_ICONOS, archivo), "rb") as f:
                    existentes[nombre] = await cliente.create_application_emoji(name=nombre, image=f.read())
                print("Ícono subido:", nombre)
        for n, e in existentes.items():
            EMO[n] = str(e)
    except Exception as e:
        print("No pude cargar los íconos de WoW (uso emojis comunes):", repr(e))


# ============================================================
#  PANEL DE ROLES (botones + menús desplegables)
# ============================================================
def roles_del_panel():
    """Todos los roles que la gente se puede poner sola: (nombre, emoji, color, desc)."""
    yield from config.ROLES_COMBATE
    for m in config.MENUS:
        yield from m["opciones"]


def todos_los_roles():
    for nombre, emoji, _, desc in roles_del_panel():
        yield nombre, emoji, desc


def orden_completo():
    """Orden de arriba hacia abajo de todos los roles que maneja Hogger: (nombre, color)."""
    orden = list(config.ROLES_STAFF_ARRIBA)
    orden += [(n, c) for n, _, c, _ in config.MENUS[0]["opciones"]]  # clases (con color)
    orden.append(config.ROL_MIEMBRO)
    orden += list(config.ROLES_STAFF_ABAJO)
    orden += [(n, c) for n, _, c, _ in config.ROLES_COMBATE]
    for m in config.MENUS[1:]:
        orden += [(n, c) for n, _, c, _ in m["opciones"]]
    return orden


async def cambiar_roles(it: discord.Interaction, poner, sacar):
    g = it.guild
    poner = [r for r in (discord.utils.get(g.roles, name=n) for n in poner) if r and r not in it.user.roles]
    sacar = [r for r in (discord.utils.get(g.roles, name=n) for n in sacar) if r and r in it.user.roles]
    try:
        if sacar:
            await it.user.remove_roles(*sacar, reason="Panel de roles")
        if poner:
            await it.user.add_roles(*poner, reason="Panel de roles")
    except discord.Forbidden:
        await responder(it, "No tengo permiso para dar esos roles. Un oficial tiene que subir el rol de Hogger arriba de todo.")
        return None
    return poner, sacar


def resumen(poner, sacar):
    partes = []
    if poner:
        partes.append("Te puse: " + ", ".join(r.mention for r in poner))
    if sacar:
        partes.append("Te saqué: " + ", ".join(r.mention for r in sacar))
    return "\n".join(partes) or "No cambió nada, ya tenías eso."


class BotonRol(discord.ui.Button):
    def __init__(self, nombre, emoji):
        super().__init__(label=nombre, emoji=emoji or None, style=discord.ButtonStyle.secondary,
                         custom_id=f"rol:{nombre}"[:100], row=0)
        self.nombre_rol = nombre

    async def callback(self, it: discord.Interaction):
        rol = discord.utils.get(it.guild.roles, name=self.nombre_rol)
        if rol is None:
            return await responder(it, "Ese rol no existe todavía. Avisale a un oficial.")
        r = await cambiar_roles(it, [] if rol in it.user.roles else [rol.name], [rol.name] if rol in it.user.roles else [])
        if r:
            await responder(it, resumen(*r))


class BotonLimpiar(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Limpiar", emoji="🧹", style=discord.ButtonStyle.danger, custom_id="rol:limpiar", row=0)

    async def callback(self, it: discord.Interaction):
        r = await cambiar_roles(it, [], [n for n, _, _ in todos_los_roles()])
        if r:
            await responder(it, resumen(*r))


class MenuRoles(discord.ui.Select):
    def __init__(self, i, menu):
        opciones = [discord.SelectOption(label=n, emoji=emo_parcial(ICONO_CLASE.get(n, ""), e or None), description=(d or None))
                    for n, e, _, d in menu["opciones"]]
        super().__init__(placeholder=menu["placeholder"][:150], min_values=0,
                         max_values=min(menu["maximo"], len(opciones)), options=opciones,
                         custom_id=f"menu:{i}", row=i + 1)
        self.nombres = [n for n, _, _, _ in menu["opciones"]]

    async def callback(self, it: discord.Interaction):
        elegidos = list(self.values)
        r = await cambiar_roles(it, elegidos, [n for n in self.nombres if n not in elegidos])
        if r:
            await responder(it, resumen(*r))


class VistaRoles(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        for nombre, emoji, _, _ in config.ROLES_COMBATE[:4]:
            self.add_item(BotonRol(nombre, emoji))
        self.add_item(BotonLimpiar())
        for i, m in enumerate(config.MENUS[:4]):
            self.add_item(MenuRoles(i, m))


def embed_panel_roles():
    e = embed_base(config.TITULO_PANEL, config.TEXTO_PANEL)
    e.add_field(name="🛡️ Rol en combate (botones)", value="\n".join(
        f"{em} **{n}**" + (f", {d.lower()}" if d else "") for n, em, _, d in config.ROLES_COMBATE), inline=False)
    for m in config.MENUS:
        e.add_field(name=m["titulo"], value=" · ".join(f"{emo(ICONO_CLASE.get(n, ''), em)} {n}" for n, em, _, _ in m["opciones"]), inline=False)
    return e


async def asegurar_roles(guild: discord.Guild):
    """Crea roles que falten y renombra los viejos. Devuelve (creados, renombrados)."""
    creados, renombrados = [], []
    for viejo, nuevo in config.RENOMBRAR.items():
        r = discord.utils.get(guild.roles, name=viejo)
        if r and not discord.utils.get(guild.roles, name=nuevo):
            await r.edit(name=nuevo, reason="Organización de roles de Hogger")
            renombrados.append(f"{viejo} → {nuevo}")
    for nombre, color in orden_completo():
        if discord.utils.get(guild.roles, name=nombre) is None:
            await guild.create_role(name=nombre, colour=discord.Colour(color) if color is not None else discord.Colour.default(),
                                    mentionable=nombre in config.ROLES_MENCIONABLES, reason="Organización de roles de Hogger")
            creados.append(nombre)
    return creados, renombrados


# ============================================================
#  BANDAS / EVENTOS (anotarse con botones)
# ============================================================
PUESTOS = {
    "tanque": ("💪", "Tanques"),
    "healer": ("💚", "Healers"),
    "dps": ("⚔️", "DPS"),
}


def embed_banda(b):
    total = sum(len(b["anotados"][p]) for p in PUESTOS)
    cupo = sum(b["cupos"][p] for p in PUESTOS)
    e = embed_base(f"🏰 {b['nombre']}", f"🕘 **Cuándo:** {b['cuando']}\n" + (f"\n{b['nota']}\n" if b.get("nota") else "")
                   + f"\nTocá un botón para anotarte. **{total}/{cupo}** anotados.")
    for p, (emoji, titulo) in PUESTOS.items():
        lista = b["anotados"][p]
        valor = "\n".join(f"<@{u}>" for u in lista) or "—"
        e.add_field(name=f"{emoji} {titulo} ({len(lista)}/{b['cupos'][p]})", value=valor, inline=True)
    if b["suplentes"]:
        e.add_field(name="🪑 Suplentes", value="\n".join(f"<@{u}> ({PUESTOS[p][1]})" for u, p in b["suplentes"]), inline=False)
    if b.get("cerrada"):
        e.title += "  (CERRADA)"
    return e


class VistaBanda(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def anotar(self, it: discord.Interaction, puesto):
        b = datos["bandas"].get(str(it.message.id))
        if b is None:
            return await responder(it, "Esta banda ya no existe.")
        if b.get("cerrada"):
            return await responder(it, "Las inscripciones de esta banda están cerradas.")
        uid = it.user.id
        for p in PUESTOS:
            if uid in b["anotados"][p]:
                b["anotados"][p].remove(uid)
        b["suplentes"] = [s for s in b["suplentes"] if s[0] != uid]
        aviso = None
        if puesto == "baja":
            aviso = "Te bajé de la banda."
        elif len(b["anotados"][puesto]) < b["cupos"][puesto]:
            b["anotados"][puesto].append(uid)
        else:
            b["suplentes"].append([uid, puesto])
            aviso = f"Los cupos de {PUESTOS[puesto][1]} están llenos, te anoté como suplente."
        guardar_datos()
        await it.response.edit_message(embed=embed_banda(b), view=self)
        if aviso:
            await it.followup.send(aviso, ephemeral=True)

    @discord.ui.button(label="Tanque", emoji="💪", style=discord.ButtonStyle.primary, custom_id="banda:tanque")
    async def b_tanque(self, it, _):
        await self.anotar(it, "tanque")

    @discord.ui.button(label="Healer", emoji="💚", style=discord.ButtonStyle.success, custom_id="banda:healer")
    async def b_healer(self, it, _):
        await self.anotar(it, "healer")

    @discord.ui.button(label="DPS", emoji="⚔️", style=discord.ButtonStyle.danger, custom_id="banda:dps")
    async def b_dps(self, it, _):
        await self.anotar(it, "dps")

    @discord.ui.button(label="Me bajo", emoji="❌", style=discord.ButtonStyle.secondary, custom_id="banda:baja")
    async def b_baja(self, it, _):
        await self.anotar(it, "baja")


# ============================================================
#  SORTEOS
# ============================================================
def embed_sorteo(s, terminado=False, ganadores=None):
    if terminado:
        txt = ("🏆 **Ganadores:** " + ", ".join(f"<@{u}>" for u in ganadores) + "\n📩 Les escribí por privado.") if ganadores else "Nadie participó 😢"
        e = embed_base(f"🎁 SORTEO TERMINADO · {s['premio']}", txt + f"\n\n👥 Participaron **{len(s['participantes'])}**.")
        e.colour = discord.Colour(0x2B2D31)
    else:
        e = embed_base(f"🎁 GRAN SORTEO · {s['premio']}",
                       (s.get("descripcion") or "¡La hermandad reparte botín! Tocá **Participar** para entrar.") + "\n\u200b")
        e.add_field(name="🏆 Premio", value=s["premio"], inline=True)
        e.add_field(name="👑 Ganadores", value=str(s["ganadores"]), inline=True)
        e.add_field(name="👥 Participantes", value=str(len(s["participantes"])), inline=True)
        e.add_field(name="⏰ Termina", value=f"<t:{int(s['fin'])}:F>\n(<t:{int(s['fin'])}:R>)", inline=False)
        e.add_field(name="📜 Cómo funciona", value="Al terminar elijo ganadores al azar, sin repetir, y les escribo por privado.", inline=False)
    if s.get("imagen"):
        e.set_image(url=s["imagen"])
    return e


class VistaSorteo(discord.ui.View):
    def __init__(self, n=None):
        super().__init__(timeout=None)
        if n is not None:
            self.participar.label = f"Participar ({n})"

    @discord.ui.button(label="Participar", emoji="🎁", style=discord.ButtonStyle.success, custom_id="sorteo:participar")
    async def participar(self, it: discord.Interaction, _):
        s = datos["sorteos"].get(str(it.message.id))
        if s is None or s.get("terminado"):
            return await responder(it, "Este sorteo ya terminó.")
        uid = it.user.id
        if uid in s["participantes"]:
            s["participantes"].remove(uid)
            aviso = "Saliste del sorteo."
        else:
            s["participantes"].append(uid)
            aviso = "¡Estás adentro! Suerte 🍀"
        guardar_datos()
        if s.get("conservar_embed"):
            await it.response.edit_message(view=VistaSorteo(len(s["participantes"])))
        else:
            await it.response.edit_message(embed=embed_sorteo(s), view=VistaSorteo(len(s["participantes"])))
        await it.followup.send(aviso, ephemeral=True)


async def avisar_ganadores(ganadores, s, canal):
    fallaron = []
    for u in ganadores:
        try:
            usuario = await bot.fetch_user(u)
            e = embed_base("🏆 ¡Ganaste un sorteo!", config.SORTEO_MP_TEXTO.format(
                usuario=usuario.display_name, premio=s["premio"], contacto=config.SORTEO_CONTACTO))
            await usuario.send(embed=e)
        except discord.HTTPException:
            fallaron.append(u)
    if fallaron:
        await canal.send(" ".join(f"<@{u}>" for u in fallaron)
                         + f" no te pude escribir por privado (los tenés cerrados). Hablale a **{config.SORTEO_CONTACTO}** para reclamar tu premio.")


async def terminar_sorteo(msg_id: str, s: dict):
    s["terminado"] = True
    guardar_datos()
    canal = bot.get_channel(s["canal"])
    if canal is None:
        return
    gente = s["participantes"]
    ganadores = random.sample(gente, min(s["ganadores"], len(gente))) if gente else []
    try:
        msg = await canal.fetch_message(int(msg_id))
        if s.get("conservar_embed"):
            await msg.edit(view=None)
        else:
            await msg.edit(embed=embed_sorteo(s, True, ganadores), view=None)
    except discord.HTTPException:
        msg = None
    if ganadores and s.get("conservar_embed") and msg:
        await msg.reply(f"🎉 ¡Sorteo terminado! Entre **{len(gente)}** participantes, los ganadores de **{s['premio']}** son: "
                        + ", ".join(f"<@{u}>" for u in ganadores) + ". ¡Felicitaciones! Les escribí por privado 📩")
    elif ganadores:
        await canal.send(
            f"🎉 ¡Felicitaciones {', '.join(f'<@{u}>' for u in ganadores)}! Ganaste **{s['premio']}**. Te escribí por privado.",
        )
    if ganadores:
        await avisar_ganadores(ganadores, s, canal)


@tasks.loop(seconds=20)
async def revisar_sorteos():
    ahora = time.time()
    for msg_id, s in list(datos["sorteos"].items()):
        if not s.get("terminado") and s["fin"] <= ahora:
            await terminar_sorteo(msg_id, s)
    await recordar_raids()
    for msg_id, q in list(datos["encuestas"].items()):
        if not q.get("terminada") and q["fin"] <= ahora:
            await cerrar_encuesta(msg_id, q)


@revisar_sorteos.before_loop
async def _esperar():
    await bot.wait_until_ready()


# ============================================================
#  ENCUESTAS (botones con resultados en vivo)
# ============================================================
NUMEROS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]


def embed_encuesta(q, terminada=False):
    votos = q["votos"]
    total = len(votos)
    lineas = []
    for i, op in enumerate(q["opciones"]):
        n = sum(1 for v in votos.values() if v == i)
        pct = round(100 * n / total) if total else 0
        barra = "▰" * round(pct / 10) + "▱" * (10 - round(pct / 10))
        lineas.append(f"{NUMEROS[i]} **{op}**\n{barra} {pct}% ({n})")
    pie = f"👥 {total} votos · " + ("Encuesta cerrada" if terminada else f"Cierra <t:{int(q['fin'])}:R>")
    e = embed_base(f"📊 {q['pregunta']}" + ("  (CERRADA)" if terminada else ""), "\n\n".join(lineas) + f"\n\n{pie}")
    return e


class BotonVoto(discord.ui.Button):
    def __init__(self, i, etiqueta=None):
        super().__init__(label=(etiqueta or f"Opción {i + 1}")[:80], emoji=NUMEROS[i],
                         style=discord.ButtonStyle.secondary, custom_id=f"encuesta:{i}")
        self.i = i

    async def callback(self, it: discord.Interaction):
        q = datos["encuestas"].get(str(it.message.id))
        if q is None or q.get("terminada"):
            return await responder(it, "Esta encuesta ya cerró.")
        uid = str(it.user.id)
        if q["votos"].get(uid) == self.i:
            del q["votos"][uid]
            aviso = "Saqué tu voto."
        else:
            q["votos"][uid] = self.i
            aviso = f"Votaste: **{q['opciones'][self.i]}** (podés cambiarlo cuando quieras)"
        guardar_datos()
        await it.response.edit_message(embed=embed_encuesta(q))
        await it.followup.send(aviso, ephemeral=True)


class VistaEncuesta(discord.ui.View):
    def __init__(self, opciones=None):
        super().__init__(timeout=None)
        for i, op in enumerate(opciones or [None] * 5):
            self.add_item(BotonVoto(i, op))


async def cerrar_encuesta(msg_id, q):
    q["terminada"] = True
    guardar_datos()
    canal = bot.get_channel(q["canal"])
    if canal is None:
        return
    try:
        msg = await canal.fetch_message(int(msg_id))
        await msg.edit(embed=embed_encuesta(q, True), view=None)
    except discord.HTTPException:
        pass


# ============================================================
#  RAID SIGN-UP (estilo Raid-Helper, por clase y spec)
# ============================================================
EMOJI_ROL = {"tanque": "🛡️", "healer": "💚", "dps": "⚔️"}


def icono_rol(rol):
    return emo(f"rol_{rol}", EMOJI_ROL[rol])
ESTADOS = {"tarde": "⏰ Llega tarde", "tentativo": "❔ Tentativo", "ausente": "❌ No puede"}


def parsear_fecha(texto):
    """'15/11 21:00' o '15/11/2026 21:00' (hora local de la guild) -> timestamp UTC."""
    texto = texto.strip().replace("-", "/").replace("hs", "").replace("h", "").strip()
    tz = timezone(timedelta(hours=config.HUSO_HORARIO))
    ahora = datetime.now(tz)
    for fmt in ("%d/%m/%Y %H:%M", "%d/%m %H:%M", "%d/%m/%y %H:%M", "%d/%m/%Y %H", "%d/%m %H", "%d/%m/%y %H"):
        try:
            d = datetime.strptime(texto, fmt)
        except ValueError:
            continue
        if "%Y" not in fmt and "%y" not in fmt:
            d = d.replace(year=ahora.year)
            if d.replace(tzinfo=tz) < ahora - timedelta(days=1):
                d = d.replace(year=ahora.year + 1)
        return d.replace(tzinfo=tz).timestamp()
    return None


def embed_raid(r):
    anot = r["anotados"]  # uid -> {nombre, clase, spec, rol, orden}
    confirmados = [a for a in anot.values() if a.get("estado") is None]
    confirmados.sort(key=lambda a: a["orden"])
    titulares, banca = confirmados[:r["cupo"]], confirmados[r["cupo"]:]
    n = {k: sum(1 for a in titulares if a["rol"] == k) for k in EMOJI_ROL}
    desc = (f"🗓️ <t:{int(r['inicio'])}:F> · <t:{int(r['inicio'])}:R>\n"
            + (f"\n{r['nota']}\n" if r.get("nota") else "")
            + f"\n👥 **{len(titulares)}/{r['cupo']}**   {icono_rol('tanque')} **{n['tanque']}**   {icono_rol('healer')} **{n['healer']}**   {icono_rol('dps')} **{n['dps']}**"
            + ("\n\n🔒 **Inscripciones cerradas**" if r.get("cerrada") else "\n\nTocá **Anotarme** y elegí clase y spec."))
    e = embed_base(f"🏰 {r['nombre']}", desc)
    numero = {a["uid"]: i + 1 for i, a in enumerate(titulares)}
    for clase, (emoji, _, _) in config.CLASES_RAID.items():
        de_clase = [a for a in titulares if a["clase"] == clase]
        if de_clase:
            valor = "\n".join(f"`{numero[a['uid']]:>2}` {emo(ICONO_SPEC.get((clase, a['spec']), ''), EMOJI_ROL[a['rol']])} **{a['nombre']}** · {a['spec']}"
                              for a in de_clase)
            e.add_field(name=f"{emo(ICONO_CLASE[clase], emoji)} {clase} ({len(de_clase)})", value=valor[:1024], inline=True)
    if banca:
        e.add_field(name=f"🪑 Banca ({len(banca)})", value="\n".join(f"{a['nombre']} · {a['clase']} {a['spec']}" for a in banca)[:1024], inline=False)
    for est, etiqueta in ESTADOS.items():
        gente = [a["nombre"] for a in anot.values() if a.get("estado") == est]
        if gente:
            e.add_field(name=f"{etiqueta} ({len(gente)})", value=", ".join(gente)[:1024], inline=False)
    return e


async def actualizar_raid(msg_id):
    r = datos["raids"].get(str(msg_id))
    canal = bot.get_channel(r["canal"]) if r else None
    if canal:
        try:
            msg = await canal.fetch_message(int(msg_id))
            await msg.edit(embed=embed_raid(r), view=VistaRaid())
        except discord.HTTPException:
            pass


class MenuSpec(discord.ui.Select):
    def __init__(self, msg_id, clase):
        emoji, _, specs = config.CLASES_RAID[clase]
        super().__init__(placeholder=f"{emoji} ¿Qué spec vas a jugar?", options=[
            discord.SelectOption(label=sp, value=f"{sp}|{rol}", emoji=emo_parcial(ICONO_SPEC.get((clase, sp), ""), EMOJI_ROL[rol]),
                                 description=rol.capitalize())
            for sp, rol in specs])
        self.msg_id, self.clase = msg_id, clase

    async def callback(self, it: discord.Interaction):
        r = datos["raids"].get(str(self.msg_id))
        if r is None or r.get("cerrada"):
            return await it.response.edit_message(content="Esta raid ya no acepta inscripciones.", view=None)
        spec, rol = self.values[0].split("|")
        uid = str(it.user.id)
        previo = r["anotados"].get(uid)
        r["contador"] = r.get("contador", 0) + 1
        r["anotados"][uid] = {"uid": uid, "nombre": it.user.display_name[:24], "clase": self.clase, "spec": spec, "rol": rol,
                              "orden": previo["orden"] if previo and previo.get("estado") is None else r["contador"], "estado": None}
        guardar_datos()
        await it.response.edit_message(content=f"✅ Anotado como {emo(ICONO_SPEC.get((self.clase, spec), ''))} **{self.clase} {spec}** {icono_rol(rol)}. ¡Nos vemos en la raid!", view=None)
        await actualizar_raid(self.msg_id)


class MenuClase(discord.ui.Select):
    def __init__(self, msg_id):
        super().__init__(placeholder="🧙 Elegí tu clase", options=[
            discord.SelectOption(label=c, emoji=emo_parcial(ICONO_CLASE.get(c, ""), e)) for c, (e, _, _) in config.CLASES_RAID.items()])
        self.msg_id = msg_id

    async def callback(self, it: discord.Interaction):
        v = discord.ui.View(timeout=300)
        v.add_item(MenuSpec(self.msg_id, self.values[0]))
        await it.response.edit_message(content=f"**{self.values[0]}**, perfecto. Ahora tu spec:", view=v)


class VistaRaid(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def _raid(self, it):
        r = datos["raids"].get(str(it.message.id))
        if r is None:
            await responder(it, "Esta raid ya no existe.")
        elif r.get("cerrada"):
            await responder(it, "Las inscripciones de esta raid están cerradas.")
            return None
        return r

    async def _estado(self, it, estado):
        r = await self._raid(it)
        if r is None:
            return
        uid = str(it.user.id)
        if estado is None:
            r["anotados"].pop(uid, None)
            aviso = "Te bajé de la raid."
        else:
            a = r["anotados"].get(uid) or {"uid": uid, "clase": "-", "spec": "-", "rol": "dps", "orden": 0}
            a.update({"nombre": it.user.display_name[:24], "estado": estado})
            r["anotados"][uid] = a
            aviso = f"Listo, quedaste como: {ESTADOS[estado]}"
        guardar_datos()
        await it.response.edit_message(embed=embed_raid(r), view=self)
        await it.followup.send(aviso, ephemeral=True)

    @discord.ui.button(label="Anotarme", emoji="✍️", style=discord.ButtonStyle.success, custom_id="raid:anotar")
    async def anotar(self, it: discord.Interaction, _):
        if await self._raid(it) is None:
            return
        v = discord.ui.View(timeout=300)
        v.add_item(MenuClase(it.message.id))
        await it.response.send_message("¿Con qué clase vas?", view=v, ephemeral=True)

    @discord.ui.button(label="Tarde", emoji="⏰", style=discord.ButtonStyle.secondary, custom_id="raid:tarde")
    async def tarde(self, it, _):
        await self._estado(it, "tarde")

    @discord.ui.button(label="Tentativo", emoji="❔", style=discord.ButtonStyle.secondary, custom_id="raid:tentativo")
    async def tentativo(self, it, _):
        await self._estado(it, "tentativo")

    @discord.ui.button(label="No puedo", emoji="❌", style=discord.ButtonStyle.secondary, custom_id="raid:ausente")
    async def ausente(self, it, _):
        await self._estado(it, "ausente")

    @discord.ui.button(label="Me bajo", emoji="🗑️", style=discord.ButtonStyle.danger, custom_id="raid:baja")
    async def baja(self, it, _):
        await self._estado(it, None)


async def recordar_raids():
    if not config.RECORDATORIO_MINUTOS:
        return
    ahora = time.time()
    for msg_id, r in list(datos["raids"].items()):
        if r.get("recordada") or r["inicio"] < ahora - 3600:
            continue
        if r["inicio"] - ahora <= config.RECORDATORIO_MINUTOS * 60:
            r["recordada"] = True
            guardar_datos()
            canal = bot.get_channel(r["canal"])
            gente = [f"<@{u}>" for u, a in r["anotados"].items() if a.get("estado") in (None, "tarde", "tentativo")]
            if canal and gente:
                await canal.send(f"⏰ **{r['nombre']}** arranca <t:{int(r['inicio'])}:R>. ¡A loguear y a la piedra de encuentro!\n" + " ".join(gente))


# ============================================================
#  ANUNCIOS (ventanita para escribir)
# ============================================================
TIPOS_ANUNCIO = {  # icono, color, etiqueta
    "aviso": ("📢", config.COLOR, "Aviso"),
    "evento": ("🎉", 0x2ECC71, "Evento"),
    "importante": ("⚠️", 0xE74C3C, "Importante"),
    "parche": ("📜", 0x3498DB, "Parche / Novedades"),
}


class VentanaAnuncio(discord.ui.Modal, title="Nuevo anuncio de Hogger"):
    titulo = discord.ui.TextInput(label="Título", max_length=256)
    texto = discord.ui.TextInput(label="Mensaje", style=discord.TextStyle.paragraph, max_length=4000)
    imagen = discord.ui.TextInput(label="Link de una imagen (opcional)", required=False, max_length=500)

    def __init__(self, canal, mencion, tipo="aviso"):
        super().__init__()
        self.canal = canal
        self.mencion = mencion
        self.tipo = TIPOS_ANUNCIO.get(tipo, TIPOS_ANUNCIO["aviso"])

    async def on_submit(self, it: discord.Interaction):
        icono, color, etiqueta = self.tipo
        e = embed_base(f"{icono} {self.titulo.value}", self.texto.value)
        e.colour = discord.Colour(color)
        e.set_footer(text=f"{etiqueta} · {config.PIE}")
        archivo = None
        if self.imagen.value.strip().startswith("http"):
            e.set_image(url=self.imagen.value.strip())
        elif tarjeta is not None:
            try:
                archivo = discord.File(tarjeta.crear_cabecera(self.titulo.value, etiqueta), filename="banner.png")
                e.set_image(url="attachment://banner.png")
            except Exception as err:
                print("No pude crear la cabecera:", repr(err))
        e.set_author(name=it.user.display_name, icon_url=it.user.display_avatar.url)
        await self.canal.send(
            content=self.mencion.mention if self.mencion else None,
            embed=e,
            allowed_mentions=discord.AllowedMentions(everyone=True, roles=True),
            **({"file": archivo} if archivo else {}),
        )
        await responder(it, f"Anuncio publicado en {self.canal.mention} ✅")


# ============================================================
#  EL BOT
# ============================================================
intents = discord.Intents.default()
intents.members = True  # para la bienvenida (activalo en el portal de Discord)


class Hogger(commands.Bot):
    async def setup_hook(self):
        await sincronizar_iconos(self)
        self.add_view(VistaRoles())
        self.add_view(VistaBanda())
        self.add_view(VistaSorteo())
        self.add_view(VistaEncuesta())
        self.add_view(VistaRaid())
        if GUILD_ID.isdigit():
            g = discord.Object(int(GUILD_ID))
            self.tree.copy_global_to(guild=g)
            await self.tree.sync(guild=g)
            # Borra los comandos viejos que dejó MEE6 en esta app (/clear, /give-xp, etc.)
            self.tree.clear_commands(guild=None)
            await self.tree.sync()
            print("Comandos de Hogger cargados en el server y comandos viejos de MEE6 borrados.")
        else:
            await self.tree.sync()
        revisar_sorteos.start()


bot = Hogger(command_prefix="!hogger ", intents=intents, help_command=None)
solo_oficiales = app_commands.default_permissions(manage_guild=True)


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name=f"cuidando a {config.NOMBRE_GUILD}"))
    print(f"✅ Hogger está en línea como {bot.user}. Dejá esta ventana abierta.")


def embed_bienvenida(member: discord.Member):
    canal_roles = datos["ajustes"].get("canal_roles")
    texto = config.TEXTO_BIENVENIDA.format(
        usuario=member.mention,
        canal_roles=f"<#{canal_roles}>" if canal_roles else "el canal de roles",
    )
    e = embed_base(config.TITULO_BIENVENIDA, texto)
    e.set_thumbnail(url=member.display_avatar.url)
    return e


async def mensaje_bienvenida(member: discord.Member):
    """Devuelve (texto, archivo con la tarjeta, embed) para la bienvenida."""
    canal_roles = datos["ajustes"].get("canal_roles")
    roles_txt = f"<#{canal_roles}>" if canal_roles else "el canal de roles"
    texto = f"⚔️ ¡Bienvenido/a {member.mention}! Pasá por {roles_txt} y armá tu ficha de aventurero."
    try:
        if tarjeta is None:
            raise RuntimeError("falta Pillow")
        av = await member.display_avatar.replace(size=256, static_format="png").read()
        img = tarjeta.crear_tarjeta(av, member.display_name, config.TARJETA_TITULO,
                                    config.TARJETA_SUBTITULO.format(numero=member.guild.member_count))
        return texto, discord.File(img, filename="bienvenida.png"), None
    except Exception as e:  # si falla la imagen, mando el mensaje lindo de texto
        print("No pude hacer la tarjeta:", repr(e))
        return member.mention, None, embed_bienvenida(member)


@bot.event
async def on_member_join(member: discord.Member):
    if config.ROL_AUTOMATICO:
        rol = discord.utils.get(member.guild.roles, name=config.ROL_AUTOMATICO)
        if rol:
            try:
                await member.add_roles(rol, reason="Rol automático")
            except discord.Forbidden:
                pass
    canal = bot.get_channel(datos["ajustes"].get("canal_bienvenida") or 0)
    if canal:
        texto, archivo, embed = await mensaje_bienvenida(member)
        await canal.send(content=texto, file=archivo, embed=embed) if archivo else await canal.send(content=texto, embed=embed)


# ---------------- comandos ----------------
@bot.tree.command(name="panel-roles", description="Publica el panel de roles con botones (crea los roles que falten)")
@solo_oficiales
@app_commands.guild_only()
@app_commands.describe(canal="Dónde publicar el panel (si no elegís, va acá)")
async def panel_roles(it: discord.Interaction, canal: discord.TextChannel = None):
    canal = canal or it.channel
    await it.response.defer(ephemeral=True)
    creados, _ = await asegurar_roles(it.guild)
    await canal.send(embed=embed_panel_roles(), view=VistaRoles())
    datos["ajustes"]["canal_roles"] = canal.id
    guardar_datos()
    extra = f"\nCreé estos roles que faltaban: {', '.join(creados)}" if creados else ""
    await it.followup.send(f"Panel publicado en {canal.mention} ✅{extra}", ephemeral=True)


@bot.tree.command(name="organizar-roles", description="Ordena todos los roles, les pone colores y crea los que falten")
@solo_oficiales
@app_commands.guild_only()
async def organizar_roles(it: discord.Interaction):
    await it.response.defer(ephemeral=True)
    g = it.guild
    creados, renombrados = await asegurar_roles(g)
    await asyncio.sleep(3)  # esperar a que Discord confirme los roles nuevos
    tope = g.me.top_role
    cambios_color = 0
    for nombre, color in orden_completo():
        r = discord.utils.get(g.roles, name=nombre)
        if r is None or r >= tope:
            continue
        datos_rol = {}
        if color is not None and r.colour.value != color:
            datos_rol["colour"] = discord.Colour(color)
        quiere = nombre in config.ROLES_MENCIONABLES
        if quiere and not r.mentionable:
            datos_rol["mentionable"] = True
        if datos_rol:
            await r.edit(reason="Organización de roles de Hogger", **datos_rol)
            cambios_color += 1
    # Orden: los de Hogger arriba (en el orden de config), el resto debajo como estaban
    nuestros = [discord.utils.get(g.roles, name=n) for n, _ in orden_completo()]
    nuestros = [r for r in nuestros if r and r < tope]
    otros = [r for r in sorted(g.roles, key=lambda r: r.position, reverse=True)
             if r < tope and not r.is_default() and r not in nuestros]
    lista = nuestros + otros
    posiciones = {r: tope.position - 1 - i for i, r in enumerate(lista) if tope.position - 1 - i >= 1}
    try:
        await g.edit_role_positions(positions=posiciones, reason="Organización de roles de Hogger")
        orden_ok = "✅ Roles ordenados."
    except discord.HTTPException as e:
        orden_ok = f"⚠️ No pude ordenarlos ({e.text if hasattr(e, 'text') else e})."
    bloqueados = [n for n, _ in orden_completo() if (r := discord.utils.get(g.roles, name=n)) and r >= tope]
    msg = [orden_ok]
    if renombrados:
        msg.append("Renombré: " + ", ".join(renombrados))
    if creados:
        msg.append("Creé: " + ", ".join(creados))
    if cambios_color:
        msg.append(f"Actualicé color o mención de {cambios_color} roles.")
    if bloqueados:
        msg.append("No pude tocar (están arriba de Hogger): " + ", ".join(bloqueados)
                   + ". Subí el rol de Hogger arriba de todo y repetí el comando.")
    await it.followup.send("\n".join(msg), ephemeral=True)


@bot.tree.command(name="bienvenida", description="Elegí el canal donde Hogger saluda a los nuevos")
@solo_oficiales
@app_commands.guild_only()
async def bienvenida(it: discord.Interaction, canal: discord.TextChannel):
    datos["ajustes"]["canal_bienvenida"] = canal.id
    guardar_datos()
    await it.response.defer(ephemeral=True)
    texto, archivo, embed = await mensaje_bienvenida(it.user)
    aviso = f"Listo, voy a dar la bienvenida en {canal.mention}. Así se ve:\n\n{texto}"
    if archivo:
        await it.followup.send(aviso, file=archivo, ephemeral=True)
    else:
        await it.followup.send(aviso, embed=embed, ephemeral=True)


@bot.tree.command(name="anuncio", description="Publica un anuncio lindo con el estilo de la guild")
@solo_oficiales
@app_commands.guild_only()
@app_commands.describe(canal="Dónde publicarlo", tipo="Estilo del anuncio", mencionar="A quién etiquetar (opcional, ej: Eventos de la guild)")
@app_commands.choices(tipo=[
    app_commands.Choice(name="📢 Aviso", value="aviso"),
    app_commands.Choice(name="🎉 Evento", value="evento"),
    app_commands.Choice(name="⚠️ Importante", value="importante"),
    app_commands.Choice(name="📜 Parche / Novedades", value="parche"),
])
async def anuncio(it: discord.Interaction, canal: discord.TextChannel, tipo: app_commands.Choice[str] = None,
                  mencionar: discord.Role = None):
    await it.response.send_modal(VentanaAnuncio(canal, mencionar, tipo.value if tipo else "aviso"))


@bot.tree.command(name="banda", description="Arma una banda o evento para que la gente se anote")
@solo_oficiales
@app_commands.guild_only()
@app_commands.describe(
    nombre="Ej: Caverna de los Lamentos",
    cuando="Ej: Viernes 21:00 (hora Argentina)",
    tanques="Cupos de tanque", healers="Cupos de healer", dps="Cupos de DPS",
    nota="Algo extra (opcional): requisitos, punto de encuentro...",
    avisar="¿Etiquetar al rol de bandas?",
)
async def banda(it: discord.Interaction, nombre: str, cuando: str,
                tanques: app_commands.Range[int, 0, 40] = 1, healers: app_commands.Range[int, 0, 40] = 1,
                dps: app_commands.Range[int, 0, 40] = 3, nota: str = "", avisar: bool = True,
                canal: discord.TextChannel = None):
    canal = canal or it.channel
    b = {"nombre": nombre, "cuando": cuando, "nota": nota,
         "cupos": {"tanque": tanques, "healer": healers, "dps": dps},
         "anotados": {"tanque": [], "healer": [], "dps": []}, "suplentes": [], "canal": canal.id}
    rol = discord.utils.get(it.guild.roles, name=config.ROL_AVISO_BANDAS) if avisar else None
    msg = await canal.send(content=rol.mention if rol else None, embed=embed_banda(b), view=VistaBanda(),
                           allowed_mentions=discord.AllowedMentions(roles=True))
    datos["bandas"][str(msg.id)] = b
    guardar_datos()
    await responder(it, f"Banda publicada en {canal.mention} ✅ Para cerrar inscripciones: clic derecho al mensaje → Apps → Cerrar banda.")


@bot.tree.context_menu(name="Cerrar banda")
@solo_oficiales
@app_commands.guild_only()
async def cerrar_banda(it: discord.Interaction, mensaje: discord.Message):
    b = datos["bandas"].get(str(mensaje.id))
    if b is None:
        return await responder(it, "Ese mensaje no es una banda de Hogger.")
    b["cerrada"] = not b.get("cerrada")
    guardar_datos()
    await mensaje.edit(embed=embed_banda(b), view=VistaBanda())
    await responder(it, "Banda cerrada 🔒" if b["cerrada"] else "Banda reabierta 🔓")


@bot.tree.command(name="sorteo", description="Arma un sorteo con botón para participar")
@solo_oficiales
@app_commands.guild_only()
@app_commands.describe(premio="Ej: 1 semana de juego", horas="Cuánto dura (24 = un día, 0.5 = media hora)", ganadores="Cuántos ganan",
                       descripcion="Texto extra (opcional)", imagen="Subí una imagen para el sorteo (opcional)",
                       avisar="¿Etiquetar al rol de sorteos?")
async def sorteo(it: discord.Interaction, premio: str, horas: app_commands.Range[float, 0.05, 720.0],
                 ganadores: app_commands.Range[int, 1, 20] = 1, descripcion: str = "", imagen: discord.Attachment = None,
                 avisar: bool = True, canal: discord.TextChannel = None):
    canal = canal or it.channel
    await it.response.defer(ephemeral=True)
    s = {"premio": premio, "fin": time.time() + horas * 3600, "ganadores": ganadores, "participantes": [], "canal": canal.id,
         "descripcion": descripcion.replace("\\n", "\n")}
    archivo = None
    if imagen and (imagen.content_type or "").startswith("image"):
        archivo = await imagen.to_file(filename="sorteo" + os.path.splitext(imagen.filename)[1].lower())
        s["imagen"] = f"attachment://{archivo.filename}"
    rol = discord.utils.get(it.guild.roles, name=config.ROL_AVISO_SORTEOS) if avisar else None
    extra = {"file": archivo} if archivo else {}
    msg = await canal.send(content=rol.mention if rol else None, embed=embed_sorteo(s), view=VistaSorteo(0),
                           allowed_mentions=discord.AllowedMentions(roles=True), **extra)
    datos["sorteos"][str(msg.id)] = s
    guardar_datos()
    await responder(it, f"Sorteo publicado en {canal.mention} ✅")


@bot.tree.command(name="encuesta", description="Arma una encuesta con botones y resultados en vivo")
@solo_oficiales
@app_commands.guild_only()
@app_commands.describe(pregunta="Ej: ¿Qué día hacemos la banda?",
                       opciones="Hasta 5, separadas con / (ej: Viernes / Sábado / Domingo)",
                       horas="Cuánto dura (24 = un día)", mencionar="A quién etiquetar (opcional)")
async def encuesta(it: discord.Interaction, pregunta: str, opciones: str,
                   horas: app_commands.Range[int, 1, 720] = 24, mencionar: discord.Role = None,
                   canal: discord.TextChannel = None):
    ops = [o.strip() for o in opciones.replace("|", "/").replace(";", "/").split("/") if o.strip()][:5]
    if len(ops) < 2:
        return await responder(it, "Necesito al menos 2 opciones separadas con / (ej: Sí / No).")
    canal = canal or it.channel
    q = {"pregunta": pregunta, "opciones": ops, "votos": {}, "fin": time.time() + horas * 3600, "canal": canal.id}
    msg = await canal.send(content=mencionar.mention if mencionar else None, embed=embed_encuesta(q),
                           view=VistaEncuesta(ops), allowed_mentions=discord.AllowedMentions(everyone=True, roles=True))
    datos["encuestas"][str(msg.id)] = q
    guardar_datos()
    await responder(it, f"Encuesta publicada en {canal.mention} ✅")


@bot.tree.command(name="raid", description="Inscripción de raid por clase y spec (estilo Raid-Helper)")
@solo_oficiales
@app_commands.guild_only()
@app_commands.describe(nombre="Ej: Monte Hyjal", fecha="Día y hora: 15/11 21:00", cupo="Máximo de jugadores (después van a la banca)",
                       nota="Requisitos, punto de encuentro, etc. (opcional)", avisar="¿Etiquetar al rol Llamado a bandas?")
async def raid(it: discord.Interaction, nombre: str, fecha: str, cupo: app_commands.Range[int, 5, 40] = 20,
               nota: str = "", avisar: bool = True, canal: discord.TextChannel = None):
    inicio = parsear_fecha(fecha)
    if inicio is None:
        return await responder(it, "No entendí la fecha. Escribila así: `15/11 21:00`")
    canal = canal or it.channel
    r = {"nombre": nombre, "inicio": inicio, "cupo": cupo, "nota": nota, "anotados": {}, "canal": canal.id, "contador": 0}
    rol = discord.utils.get(it.guild.roles, name=config.ROL_AVISO_BANDAS) if avisar else None
    msg = await canal.send(content=rol.mention if rol else None, embed=embed_raid(r), view=VistaRaid(),
                           allowed_mentions=discord.AllowedMentions(roles=True))
    datos["raids"][str(msg.id)] = r
    guardar_datos()
    await responder(it, f"Raid publicada en {canal.mention} ✅ Para cerrarla: clic derecho al mensaje → Apps → Cerrar raid.")


@bot.tree.context_menu(name="Cerrar raid")
@solo_oficiales
@app_commands.guild_only()
async def cerrar_raid(it: discord.Interaction, mensaje: discord.Message):
    r = datos["raids"].get(str(mensaje.id))
    if r is None:
        return await responder(it, "Ese mensaje no es una raid de Hogger.")
    r["cerrada"] = not r.get("cerrada")
    guardar_datos()
    await mensaje.edit(embed=embed_raid(r), view=VistaRaid())
    await responder(it, "Raid cerrada 🔒" if r["cerrada"] else "Raid reabierta 🔓")


class VentanaRetomar(discord.ui.Modal, title="Reactivar sorteo"):
    premio = discord.ui.TextInput(label="Premio", max_length=200)
    ganadores = discord.ui.TextInput(label="Cuántos ganadores", default="1", max_length=2)
    horas = discord.ui.TextInput(label="Termina en cuántas horas", default="24", max_length=4)

    def __init__(self, mensaje):
        super().__init__()
        self.mensaje = mensaje
        if mensaje.embeds and mensaje.embeds[0].title:
            self.premio.default = mensaje.embeds[0].title.replace("⚔️", "").replace("SORTEO:", "").strip()[:200]

    async def on_submit(self, it: discord.Interaction):
        try:
            g, h = int(self.ganadores.value), float(self.horas.value.replace(",", "."))
        except ValueError:
            return await responder(it, "Ganadores y horas tienen que ser números.")
        s = {"premio": self.premio.value, "fin": time.time() + h * 3600, "ganadores": max(1, g),
             "participantes": [], "canal": self.mensaje.channel.id, "conservar_embed": True}
        datos["sorteos"][str(self.mensaje.id)] = s
        guardar_datos()
        await self.mensaje.edit(view=VistaSorteo(0))
        await responder(it, f"✅ Sorteo reactivado. Termina <t:{int(s['fin'])}:R> y elijo {g} ganador/es sin repetir. "
                            "Avisale a la gente que vuelva a tocar Participar.")


@bot.tree.context_menu(name="Reactivar sorteo")
@solo_oficiales
@app_commands.guild_only()
async def reactivar_sorteo(it: discord.Interaction, mensaje: discord.Message):
    """Toma un sorteo viejo publicado por este bot (ej. cuando era de MEE6) y le pone el botón de Hogger."""
    if mensaje.author.id != bot.user.id:
        return await responder(it, "Solo puedo reactivar mensajes que publicó Hogger.")
    await it.response.send_modal(VentanaRetomar(mensaje))


@bot.tree.context_menu(name="Sortear entre reacciones")
@solo_oficiales
@app_commands.guild_only()
async def sortear_reacciones(it: discord.Interaction, mensaje: discord.Message):
    """Para sorteos viejos (ej. de MEE6): elige un ganador entre los que reaccionaron al mensaje."""
    await it.response.defer(ephemeral=True)
    gente = {}
    for reaccion in mensaje.reactions:
        async for u in reaccion.users():
            if not u.bot:
                gente[u.id] = u
    if not gente:
        return await it.followup.send("Ese mensaje no tiene reacciones de personas.", ephemeral=True)
    ganador = random.choice(list(gente.values()))
    lista = ", ".join(u.display_name for u in gente.values())
    await mensaje.reply(f"🎉 ¡Sorteo terminado! Entre **{len(gente)}** participantes, el ganador es {ganador.mention}. ¡Felicitaciones!")
    await it.followup.send(f"Participantes ({len(gente)}): {lista}\nGanador: {ganador.display_name}", ephemeral=True)


@bot.tree.command(name="ayuda", description="Qué sabe hacer Hogger")
async def ayuda(it: discord.Interaction):
    e = embed_base("🐗 Comandos de Hogger")
    e.add_field(name="/organizar-roles", value="Ordena los roles, les pone colores y crea los que falten.", inline=False)
    e.add_field(name="/panel-roles", value="Publica el panel de roles con botones y menús.", inline=False)
    e.add_field(name="/bienvenida", value="Elige el canal donde saludo a los nuevos.", inline=False)
    e.add_field(name="/anuncio", value="Anuncio con estilo: Aviso, Evento, Importante o Parche.", inline=False)
    e.add_field(name="/banda", value="Arma una banda o evento con cupos de tanque, healer y DPS.", inline=False)
    e.add_field(name="/sorteo", value="Arma un sorteo; elijo ganador solo cuando termina.", inline=False)
    e.add_field(name="/raid", value="Inscripción por clase y spec, hasta 40, con banca y recordatorio.", inline=False)
    e.add_field(name="/encuesta", value="Pregunta con hasta 5 opciones y resultados en vivo.", inline=False)
    e.add_field(name="Clic derecho → Apps → Cerrar banda", value="Cierra o reabre las inscripciones.", inline=False)
    await it.response.send_message(embed=e, ephemeral=True)


@bot.tree.error
async def on_app_error(it: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        return await responder(it, "Ese comando es solo para oficiales.")
    print("Error:", repr(error))
    try:
        await responder(it, "Uy, algo falló. Fijate que Hogger tenga permisos en ese canal.")
    except discord.HTTPException:
        pass


def pedir_ajustes():
    global TOKEN, GUILD_ID
    print("=" * 60)
    print("  CONFIGURACION DE HOGGER (solo la primera vez)")
    print("=" * 60)
    while not token_valido(TOKEN):
        print("\nPega el TOKEN del bot y apreta Enter.")
        print("(Para pegar: clic derecho dentro de esta ventana, o Ctrl+V)")
        TOKEN = input("TOKEN: ").strip().strip('"').strip("'")
        if not token_valido(TOKEN):
            print("❌ Eso no parece un token. Es un texto largo con dos puntos en el medio. Proba de nuevo.")
    if not GUILD_ID.isdigit():
        print("\nAhora pega el ID del server (clic derecho al icono del server → Copiar ID del servidor).")
        print("Si no lo tenes, apreta Enter y listo.")
        GUILD_ID = input("ID DEL SERVER: ").strip()
        if not GUILD_ID.isdigit():
            GUILD_ID = ""
    with open(os.path.join(CARPETA, ".env"), "w", encoding="utf-8") as f:
        f.write(f"DISCORD_TOKEN={TOKEN}\nGUILD_ID={GUILD_ID}\n")
    print("\n✅ Guardado. La proxima vez arranca solo.\n")


if __name__ == "__main__":
    if not token_valido(TOKEN):
        pedir_ajustes()
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("\n❌ Discord dice que el token no sirve. Hace 'Reset Token' en el portal y pegalo de nuevo.")
        os.remove(os.path.join(CARPETA, ".env"))
        input("Apreta Enter para volver a intentar...")
