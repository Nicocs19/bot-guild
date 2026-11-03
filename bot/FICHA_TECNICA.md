# Hogger, el bot de Discord de The H's: ficha técnica

Para conectar el bot con otros proyectos (por ejemplo, el "cerebro" de automatizaciones).

## Qué es
- Bot propio de Discord en **Python 3 + discord.py 2.x** que reemplaza a MEE6.
- Usa la app de Discord **"Hogger el H"**. Antes era el bot personalizado de MEE6; se reseteó el token el 3/11/2026.
- Corre en la PC de Nicolas (Windows, RTX 4080, 64 GB RAM): `iniciar.bat` abre una consola que reinicia el bot solo si se cae.
- Costo: $0. Solo está en línea mientras la PC esté prendida.

## Archivos (carpeta `bot/`)
| Archivo | Para qué |
|---|---|
| `bot.py` | El bot (comandos, botones, tareas). |
| `config.py` | Textos, colores, roles del panel, orden de roles, bienvenida. Es lo que se edita normalmente. |
| `control.py` | Línea de comandos para hacer cosas sin abrir Discord (anuncios, roles). Pensado para automatizaciones. |
| `.env` | `DISCORD_TOKEN` y `GUILD_ID`. **Secreto, nunca sale de la PC.** Se crea solo la primera vez que arranca el bot. |
| `datos.json` | Estado: bandas, sorteos, encuestas, canales elegidos. |
| `instalar.bat` / `iniciar.bat` | Instalación (venv + dependencias) y arranque. |

## Comandos en Discord (solo oficiales con "Gestionar servidor")
- `/organizar-roles`: crea, renombra, colorea y ordena todos los roles según `config.py`.
- `/panel-roles`: panel con botones (Tanque, Healer, DPS, Limpiar) y 4 menús (clase, estilo de juego, profesiones, avisos).
- `/bienvenida canal`: canal de bienvenida. Además da el rol automático "H".
- `/anuncio canal tipo mencionar`: abre una ventanita para escribir. Tipos: Aviso, Evento, Importante, Parche.
- `/banda`: inscripción con cupos de Tanque, Healer y DPS, más suplentes. Se cierra con clic derecho → Apps → Cerrar banda.
- `/sorteo`: botón Participar; el ganador sale solo al terminar.
- `/raid nombre fecha cupo`: inscripción estilo Raid-Helper por clase y spec (5 a 40 jugadores, banca, Tarde/Tentativo/No puedo, recordatorio 30 min antes). Fecha `15/11 21:00`, hora local UTC-4 (`HUSO_HORARIO` en config). Specs en `CLASES_RAID`.
- `/encuesta`: hasta 5 opciones con resultados en vivo y cierre automático.
- `/ayuda`.

## Para automatizar desde afuera: `control.py`
Se corre en la PC, dentro de la carpeta del bot, con el venv activo (`.venv\Scripts\python control.py ...`):
```
control.py canales
control.py roles
control.py anuncio --canal anuncios-guild --titulo "Título" --texto "..." [--mencionar "Eventos de la guild"] [--imagen URL]
control.py anuncio --canal anuncios-guild --titulo "Título" --archivo texto.txt
control.py mensaje --canal general --texto "..."
control.py crear-rol "Nombre" [--color FFAA00] [--mencionable]
control.py editar-rol "Nombre" [--nombre-nuevo X] [--color FFAA00] [--mencionable si|no]
control.py borrar-rol "Nombre"
```
Solo usa la API REST de Discord (no abre una segunda sesión), así que puede correr al mismo tiempo que el bot.

## Buzón de El Cerebro (órdenes automáticas)
El Cerebro (en la PC) publica órdenes en el canal privado `#cerebro` usando el token de Hogger, así que el autor es el propio Hogger. Hogger solo obedece mensajes suyos en ese canal que empiezan con `🧠 orden`, los ejecuta con las mismas funciones que los comandos y responde al mensaje con `✅` o `❌` y un JSON con el resultado (`link`, `id`).
No abre puertos ni necesita el intent de contenido de mensajes: un bot siempre puede leer sus propios mensajes.

Formato de la orden:
````
🧠 orden
```json
{"accion": "raid", "nombre": "Molten Core", "fecha": "2026-11-07 21:00", "cupo": 20, "nota": "Traer resistencias"}
```
````
Acciones y campos (los canales por defecto están en `CANALES_CEREBRO` de `config.py`):
| Acción | Campos |
|---|---|
| `anuncio` | `titulo`, `texto`, `tipo` (aviso, evento, importante, parche), `mencionar` (rol o everyone), `canal`, `imagen` (link) |
| `mensaje` | `texto`, `mencionar`, `canal` |
| `raid` | `nombre`, `fecha` (`AAAA-MM-DD HH:MM` hora de la guild), `cupo` (5 a 40), `nota`, `avisar`, `canal` |
| `banda` | `nombre`, `cuando`, `tanques`, `healers`, `dps`, `nota`, `avisar`, `canal` |
| `sorteo` | `premio`, `horas` (0.05 a 720), `ganadores` (1 a 20), `descripcion`, `avisar`, `imagen`, `canal` |
| `encuesta` | `pregunta`, `opciones` (lista de 2 a 5), `horas`, `mencionar`, `canal` |
| `cerrar` | `tipo` (raid o banda) + `id` (o `"ultimo"`), o `link`; `cerrar: false` la reabre |
| `borrar` | `link`, o `tipo` + `id` (o `"ultimo"`). Solo borra mensajes de Hogger |
| `estado` | Devuelve canales, roles mencionables y raids próximas |

Si Hogger no tiene el permiso **Gestionar canales**, `#cerebro` no se crea solo: crealo como canal privado y dale acceso al rol de Hogger.

## Estructura del server (3/11/2026)
- Canales: bienvenidas, reglas, elige-tus-roles, en-vivo, videos-nuevos, anuncios-guild, RAID (voz), general, clips-y-memes, subidas-de-nivel, raids-signup, builds-y-guias, más canales de voz.
- Roles, de arriba hacia abajo: Hogger el H, GM, Oficial, Core, Creador de contenido, Veterano, las 9 clases (con colores oficiales), H, Recluta, Tanque, Healer, DPS, PvE, PvP, Economía, Leveleo en grupo, Taberna, las 9 profesiones, y los avisos (Eventos de la guild, Llamado a bandas, Sorteos, En vivo, Videos nuevos).

## Ideas para conectar más adelante
- Sincronizar inscripciones con la hoja de registro de Google Sheets (personaje, rol, profesiones).
- Recordatorio automático antes de cada banda.
- Avisar en #en-vivo cuando alguien empieza un stream.
- Hosting 24/7 gratis (por ejemplo Oracle Cloud Always Free) si hace falta que esté siempre prendido.
- **Auto-actualización (recomendado para el "cerebro"):** subir la carpeta del bot a un repo de GitHub (sin `.env` ni `datos.json`) y que `iniciar.bat` haga `git pull` antes de arrancar. Así los cambios llegan solos a la PC.
- `control.py anuncio` ya genera una cabecera con imagen automáticamente (`tarjeta.crear_cabecera`), acepta `--imagen-archivo`, `--campo`, `--boton-link` y `--editar LINK` (reemplaza un anuncio sin volver a notificar).
- **Permisos:** para que Claude corra `control.py` sin bloqueos desde la PC, hay que permitir ese comando en la configuración de Claude Code (el modo auto frenó una vez una "escritura externa"). Mantener un paso de aprobación ("dale") antes de publicar.
