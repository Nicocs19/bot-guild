# ============================================================
#  CONFIGURACIÓN DE HOGGER — editá este archivo tranquilo
#  (cambiá textos, emojis o roles; después reiniciá el bot)
# ============================================================

NOMBRE_GUILD = "The H's"
PIE = "The H's · World of Warcraft Forever"

# Color de los mensajes (dorado clásico de WoW). Formato 0xRRGGBB.
COLOR = 0xC9A227

# ------------------------------------------------------------
#  PANEL DE ROLES
#  Fila de botones: rol en combate. Abajo, 4 menús desplegables.
#  Cada opción es ("Nombre del rol", "emoji", color o None, "descripción")
#  Color: 0xRRGGBB, o None para dejarlo sin color.
#  Si un rol no existe, Hogger lo crea con /organizar-roles o /panel-roles.
# ------------------------------------------------------------
TITULO_PANEL = "⚔️ Elegí tu destino en The H's"
TEXTO_PANEL = (
    "Armá tu ficha de aventurero. Tocá los botones y usá los menús de abajo.\n"
    "En los menús marcá **todo lo que quieras**: lo que no marques, se te saca.\n"
    "Con 🧹 **Limpiar** te sacás todos estos roles y empezás de cero."
)

ROLES_COMBATE = [
    ("Tanque", "🛡️", 0x3498DB, "El muro que aguanta todo"),
    ("Healer", "💚", 0x1ABC9C, "El que mantiene vivos a los mancos"),
    ("DPS", "⚔️", 0xE67E22, "Pura destrucción"),
]

MENUS = [
    {
        "titulo": "🧙 Tu clase",
        "placeholder": "🧙 Elegí tu clase (pinta tu nombre del color de la clase)",
        "maximo": 1,
        "opciones": [  # colores oficiales de clase de WoW
            ("Guerrero", "🪓", 0xC69B6D, ""),
            ("Paladín", "🔨", 0xF48CBA, ""),
            ("Cazador", "🏹", 0xAAD372, ""),
            ("Pícaro", "🗡️", 0xFFF468, ""),
            ("Sacerdote", "✨", 0xFFFFFF, ""),
            ("Chamán", "⚡", 0x0070DD, ""),
            ("Mago", "🔮", 0x3FC7EB, ""),
            ("Brujo", "💀", 0x8788EE, ""),
            ("Druida", "🐻", 0xFF7C0A, ""),
        ],
    },
    {
        "titulo": "🗺️ Qué te gusta jugar",
        "placeholder": "🗺️ ¿Qué te gusta jugar? (podés marcar varios)",
        "maximo": 5,
        "opciones": [
            ("PvE", "🐉", None, "Mazmorras y bandas"),
            ("PvP", "🩸", None, "Campos de batalla y emboscadas"),
            ("Economía", "💰", None, "Subasta y farmeo de oro"),
            ("Leveleo en grupo", "🏃", None, "Subir de nivel acompañado"),
            ("Taberna", "🍺", None, "Charla, joda y voice"),
        ],
    },
    {
        "titulo": "⚒️ Profesiones",
        "placeholder": "⚒️ Tus profesiones (marcá tus dos principales)",
        "maximo": 4,
        "opciones": [
            ("Minería", "⛏️", None, "Recolección"),
            ("Herboristería", "🌿", None, "Recolección"),
            ("Desuello", "🔪", None, "Recolección"),
            ("Herrería", "⚒️", None, "Fabricación"),
            ("Ingeniería", "🔧", None, "Fabricación"),
            ("Alquimia", "⚗️", None, "Fabricación"),
            ("Sastrería", "🧵", None, "Fabricación"),
            ("Peletería", "🦌", None, "Fabricación"),
            ("Encantamiento", "🪄", None, "Fabricación"),
        ],
    },
    {
        "titulo": "🔔 Avisos",
        "placeholder": "🔔 ¿Qué avisos querés recibir? (podés marcar varios)",
        "maximo": 5,
        "opciones": [
            ("Eventos de la guild", "📢", None, "Te etiquetamos en eventos"),
            ("Llamado a bandas", "🏰", None, "Cuando se arma una banda"),
            ("Sorteos", "🎁", None, "Oro, monturas y premios"),
            ("En vivo", "🔴", None, "Cuando alguien está en stream"),
            ("Videos nuevos", "🎬", None, "Cuando sale un video"),
        ],
    },
]

# Los roles de avisos se pueden mencionar con @
ROLES_MENCIONABLES = ["Eventos de la guild", "Llamado a bandas", "Sorteos", "En vivo", "Videos nuevos"]

# ------------------------------------------------------------
#  ORDEN COMPLETO DE ROLES (de arriba hacia abajo) para /organizar-roles
#  Los de staff se dan a mano. color None = no tocar el color que ya tiene.
#  RENOMBRAR: roles viejos que se renombran (se conservan los miembros).
# ------------------------------------------------------------
ROLES_STAFF_ARRIBA = [
    ("GM", None),
    ("Oficial", None),
    ("Core", None),
    ("Creador de contenido", 0x9146FF),
    ("Veterano", None),
]
ROL_MIEMBRO = ("H", None)  # todos los miembros de la guild
ROLES_STAFF_ABAJO = [
    ("Recluta", 0x95A5A6),
]
RENOMBRAR = {"Tank": "Tanque", "pve": "PvE", "pvp": "PvP"}

# Cuando se arma una banda con /banda, Hogger etiqueta a este rol
ROL_AVISO_BANDAS = "Llamado a bandas"
# Cuando se arma un sorteo con /sorteo, Hogger etiqueta a este rol
ROL_AVISO_SORTEOS = "Sorteos"

# ------------------------------------------------------------
#  BIENVENIDA
#  {usuario} = mención del nuevo, {canal_roles} = canal del panel
# ------------------------------------------------------------
TITULO_BIENVENIDA = "¡Llegó carne fresca a The H's!"
TEXTO_BIENVENIDA = (
    "Bienvenido/a {usuario}, ya sos parte de la hermandad.\n\n"
    "👉 Pasá por {canal_roles} y elegí tu rol, lo que te gusta jugar y tu profesión.\n"
    "📜 Leé #reglas y presentate en el chat.\n\n"
    "Nos vemos en Azeroth. ¡Por la Alianza!"
)

# Rol que se le da automáticamente a todo el que entra ("" = ninguno)
# (en tu server, todos tienen el rol "H")
ROL_AUTOMATICO = "H"

# ------------------------------------------------------------
#  RAID SIGN-UP (/raid) — inscripción por clase y spec
#  Tu hora: según tu PC estás en UTC-4. Si no, cambiá este número.
# ------------------------------------------------------------
HUSO_HORARIO = -4
RECORDATORIO_MINUTOS = 30  # aviso a los anotados antes de la raid (0 = no avisar)

# Clase: (emoji, color, [ (spec, rol) ])   rol = "tanque" | "healer" | "dps"
CLASES_RAID = {
    "Guerrero": ("🪓", 0xC69B6D, [("Protección", "tanque"), ("Armas", "dps"), ("Furia", "dps")]),
    "Paladín": ("🔨", 0xF48CBA, [("Protección", "tanque"), ("Sagrado", "healer"), ("Reprensión", "dps")]),
    "Cazador": ("🏹", 0xAAD372, [("Bestias", "dps"), ("Puntería", "dps"), ("Supervivencia", "dps")]),
    "Pícaro": ("🗡️", 0xFFF468, [("Asesinato", "dps"), ("Combate", "dps"), ("Sutileza", "dps")]),
    "Sacerdote": ("✨", 0xFFFFFF, [("Sagrado", "healer"), ("Disciplina", "healer"), ("Sombras", "dps")]),
    "Chamán": ("⚡", 0x0070DD, [("Restauración", "healer"), ("Elemental", "dps"), ("Mejora", "dps")]),
    "Mago": ("🔮", 0x3FC7EB, [("Escarcha", "dps"), ("Fuego", "dps"), ("Arcano", "dps")]),
    "Brujo": ("💀", 0x8788EE, [("Aflicción", "dps"), ("Demonología", "dps"), ("Destrucción", "dps")]),
    "Druida": ("🐻", 0xFF7C0A, [("Feral (oso)", "tanque"), ("Restauración", "healer"), ("Feral (gato)", "dps"), ("Equilibrio", "dps")]),
}

# Tarjeta de bienvenida (imagen). Fondo: recursos/fondo_bienvenida.jpg
TARJETA_TITULO = "Llegó otro H a la taberna"
TARJETA_SUBTITULO = "Miembro Nº {numero} · ¡Por la Alianza!"

# ------------------------------------------------------------
#  MENSAJE PRIVADO A LOS GANADORES DE SORTEOS
# ------------------------------------------------------------
SORTEO_MP_TEXTO = (
    "¡Felicitaciones, {usuario}! 🎉\n\n"
    "Ganaste **{premio}** en el sorteo de The H's.\n\n"
    "Para reclamarlo, escribile por privado a **{contacto}** en las próximas 48 horas. "
    "Si no reclamás, se vuelve a sortear.\n\n"
    "¡Gracias por ser parte de la hermandad! ⚔️"
)
SORTEO_CONTACTO = "Mr. H"

# ------------------------------------------------------------
#  EL CEREBRO (órdenes por voz desde la PC de Nicolas)
#  Canal privado donde El Cerebro deja las órdenes. Hogger lo crea solo si
#  tiene el permiso "Gestionar canales"; si no, crealo a mano como privado.
# ------------------------------------------------------------
CANAL_CEREBRO = "cerebro"
# Canal por defecto de cada tipo de orden (si la orden no dice otro)
CANALES_CEREBRO = {
    "anuncio": "anuncios-guild",
    "mensaje": "general",
    "raid": "raids-signup",
    "banda": "raids-signup",
    "sorteo": "anuncios-guild",
    "encuesta": "general",
}
