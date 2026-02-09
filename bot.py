import discord
from discord.ext import commands
import random
import os
import gspread
import traceback
from google.oauth2.service_account import Credentials
from datetime import datetime

# ========= CONFIG =========
print("ANNOUNCE_CHANNEL_ID =", repr(os.getenv("ANNOUNCE_CHANNEL_ID")))
TOKEN = os.getenv("DISCORD_TOKEN")
CANAL_GORRO_ID = int(os.getenv("CHANNEL_ID"))
CANAL_ANUNCIO_ID = int(os.getenv("ANNOUNCE_CHANNEL_ID"))

# Google Sheets Config
SHEET_NAME = "Cortes Prythian" 
CREDENTIALS_FILE = "credentials.json"

DEBUG_BALANCE = True

CORTES = {
    "amanecer": {
        "role_id": 1459983740653535334,
        "titulo": "🌅 Corte del Amanecer",
        "descripcion": "Luz cálida y ambiente etéreo.",
        "imagen": "amanecer.png"
    },
    "dia": {
        "role_id": 1459983708466577736,
        "titulo": "☀️ Corte del Día",
        "descripcion": "Estética luminosa.",
        "imagen": "dia.png"
    },
    "verano": {
        "role_id": 1459983874447905066,
        "titulo": "🔥 Corte del Verano",
        "descripcion": "Ambiente relajado y marino.",
        "imagen": "verano.png"
    },
    "otono": {
        "role_id": 1459983917175017642,
        "titulo": "🍂 Corte del Otoño",
        "descripcion": "Sensación cálida y salvaje.",
        "imagen": "otono.png"
    },
    "invierno": {
        "role_id": 1459983780797481020,
        "titulo": "❄️ Corte del Invierno",
        "descripcion": "Ambiente frío y fortificado.",
        "imagen": "invierno.png"
    },
    "primavera": {
        "role_id": 1459983943146410176,
        "titulo": "🌸 Corte de la Primavera",
        "descripcion": "Sensación de renovación.",
        "imagen": "primavera.png"
    },
    "noche": {
        "role_id": 1459983478480310435,
        "titulo": "🌙 Corte de la Noche",
        "descripcion": "Elegancia nocturna.",
        "imagen": "noche.png"
    }
}

ROLES_OPTIONS = [
    "CONSTRUCTOR",
    "DECORADOR",
    "FARMER",
    "GUERRERO",
    "INGENIERO",
    "LOGISTICA",
    "MERCADER"
]

# ==========================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# -------- GOOGLE SHEETS --------

def get_gspread_client():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    # 1. Intentar cargar desde variable de entorno (Railway / Prod)
    env_creds = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if env_creds:
        try:
            import json
            creds_dict = json.loads(env_creds)
            creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
            return gspread.authorize(creds)
        except Exception as e:
             print(f"❌ Error cargando credenciales desde ENV: {e}")
             traceback.print_exc()

    # 2. Intentar cargar desde archivo local (Dev)
    if os.path.exists(CREDENTIALS_FILE):
        try:
            creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scope)
            return gspread.authorize(creds)
        except Exception as e:
            print(f"❌ Error cargando archivo local de credenciales: {e}")
            traceback.print_exc()
    
    print("⚠️ CREDENCIALES NO ENCONTRADAS (Ni en ENV ni en archivo). Saltando integración Sheets.")
    return None

def add_member_to_sheet(discord_name, minecraft_name, corte, roles):
    try:
        client = get_gspread_client()
        if not client:
            return

        sheet = client.open(SHEET_NAME).sheet1
        # Obtener todos los registros de la columna "USUARIO" (columna C, índice 3)
        # Ojo: gspread usa indices base 1.
        col_values = sheet.col_values(3) 

        insert_index = -1
        
        # Buscar "MrBonesterYT" o "Corabysl" para insertar antes de ellos
        targets = ["MrBonesterYT", "Corabysl"]
        
        for i, val in enumerate(col_values):
            if val in targets:
                insert_index = i + 1 # +1 porque gspread es 1-based
                break
        
        if insert_index == -1:
            # Si no se encuentran, insertar después del último dato
            insert_index = len(col_values) + 1

        # Preparar fila
        # Cols: [Permisos?, DISCORD, USUARIO, CORTE, RANGO, ROL, ROL2, ROL3, HAT, ...]
        # A=1, B=2, C=3, D=4, E=5, F=6, G=7, H=8, I=9
        
        row_data = [
            "FALSE",          # A: Permisos? (Check box unchecked)
            discord_name,     # B: DISCORD
            minecraft_name,   # C: USUARIO
            corte.upper(),    # D: CORTE
            "MIEMBRO",        # E: RANGO
            roles[0] if len(roles) > 0 else "", # F: ROL
            roles[1] if len(roles) > 1 else "", # G: ROL2 (oculto/extra)
            roles[2] if len(roles) > 2 else "", # H: ROL3 (oculto/extra)
            "",               # I: HAT
            ""                # J: Extra?
        ]

        print(f"📝 Insertando en fila {insert_index}: {row_data}")
        sheet.insert_row(row_data, insert_index)
        print("✅ Google Sheet actualizado correctamente.")

    except Exception as e:
        print(f"❌ Error actualizando Google Sheet: {e}")
        traceback.print_exc()

# -------- UTIL --------

def tiene_corte(member: discord.Member):
    return any(
        role.id == data["role_id"]
        for role in member.roles
        for data in CORTES.values()
    )

def contar_miembros_por_corte(guild: discord.Guild):
    conteo = {}
    for key, data in CORTES.items():
        rol = guild.get_role(data["role_id"])
        conteo[key] = len(rol.members) if rol else 0
    return conteo

def log_balance_cortes(guild, corte_asignado=None, motivo=""):
    if not DEBUG_BALANCE:
        return

    conteo = contar_miembros_por_corte(guild)
    if corte_asignado:
        conteo[corte_asignado] += 1
    max_miembros = max(conteo.values(), default=0)

    print("\n📊 ===== BALANCE DE CORTES =====")
    if motivo:
        print(f"📝 Motivo: {motivo}")

    pesos = {}
    for corte, cantidad in conteo.items():
        peso = max(1, (max_miembros - cantidad + 1) ** 2)
        pesos[corte] = peso
        print(f"• {corte.upper():10} | miembros: {cantidad:2} | peso: {peso}")

    total = sum(pesos.values())
    print("📈 ===== PROBABILIDADES =====")
    for corte, peso in pesos.items():
        porcentaje = (peso / total) * 100 if total else 0
        print(f"→ {corte.upper():10}: {porcentaje:6.2f}%")
    print("================================\n")

def elegir_corte_balanceada(guild: discord.Guild):
    conteo = contar_miembros_por_corte(guild)
    max_miembros = max(conteo.values(), default=0)
    
    cortes = []
    pesos = []

    print(f"\n🎲 Calculando probabilidades para '{guild.name}' ({guild.member_count} miembros detectados)")
    
    cortes_maximos = [c for c, n in conteo.items() if n == max_miembros]
    num_cortes = len(conteo)
    num_maximos = len(cortes_maximos)

    excluir_maximos = (1 <= num_maximos <= 3) and (num_maximos < num_cortes)

    if excluir_maximos:
        print(f"🚫 Excluyendo {num_maximos} corte(s) por tener máximo de miembros ({max_miembros}): {', '.join(cortes_maximos)}")
    else:
        print(f"⚠️ No se excluye nadie (Máximos empatados: {num_maximos}/{num_cortes})")

    for corte, cantidad in conteo.items():
        if excluir_maximos and corte in cortes_maximos:
            print(f"   ► {corte:10} | Cant: {cantidad:3} | Peso:    0 (EXCLUIDO)")
            continue

        peso = max(1, (max_miembros - cantidad + 1) ** 2)
        cortes.append(corte)
        pesos.append(peso)
        print(f"   ► {corte:10} | Cant: {cantidad:3} | Peso: {peso:4}")

    if not cortes:
        print("⚠️ ALERTA: Lista de cortes vacía tras filtrado. Usando modo fallback.")
        cortes = list(conteo.keys())
        pesos = [1] * len(cortes)

    eleccion = random.choices(cortes, weights=pesos, k=1)[0]
    print(f"✨ Resultado: {eleccion}\n")
    return eleccion

def crear_embed_corte(key, minecraft_name=""):
    data = CORTES[key]
    titulo = data["titulo"]
    if minecraft_name:
        titulo += f" | {minecraft_name}"

    embed = discord.Embed(
        title=titulo,
        description=data["descripcion"],
        color=0x6a4c93
    )
    embed.set_image(url=f"attachment://{data['imagen']}")
    embed.set_footer(text="El destino ha sido decidido. ¡Selecciona tus roles abajo!")

    archivo = discord.File(data["imagen"], filename=data["imagen"])
    return embed, archivo

# -------- UI MODAL & SELECT --------

class RoleSelect(discord.ui.Select):
    def __init__(self, minecraft_name, corte_asignado, member_name):
        self.minecraft_name = minecraft_name
        self.corte_asignado = corte_asignado
        self.member_name = member_name
        
        options = [
            discord.SelectOption(label=role, value=role) for role in ROLES_OPTIONS
        ]
        super().__init__(
            placeholder="Selecciona hasta 3 roles...",
            min_values=0,
            max_values=3,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        roles_selected = self.values
        
        await interaction.response.send_message(
            f"✅ **Registro Completado**\n"
            f"👤 Usuario: `{self.minecraft_name}`\n"
            f"🏰 Corte: **{self.corte_asignado.upper()}**\n"
            f"🛠️ Roles: {', '.join(roles_selected) if roles_selected else 'Ninguno'}",
            ephemeral=True
        )
        
        # Guardar en Google Sheets (Async/Blocking warning, idealmente usar thread/async lib pero gspread es sync)
        # Para evitar bloquear el bot mucho tiempo, lo ideal es ejecutar esto en un executor, 
        # pero por simplicidad aquí lo llamamos directo (es rápido usualmente).
        print(f"Guardando datos para {self.minecraft_name}...")
        add_member_to_sheet(self.member_name, self.minecraft_name, self.corte_asignado, roles_selected)

class RoleSelectView(discord.ui.View):
    def __init__(self, minecraft_name, corte_asignado, member_name):
        super().__init__(timeout=None)
        self.add_item(RoleSelect(minecraft_name, corte_asignado, member_name))

class RegistroModal(discord.ui.Modal, title="Registro de Miembro"):
    minecraft_name = discord.ui.TextInput(
        label="Nombre de Usuario de Minecraft",
        placeholder="Ej: Steve123",
        required=True,
        max_length=50
    )

    async def on_submit(self, interaction: discord.Interaction):
        member = interaction.user
        mc_name = self.minecraft_name.value
        
        # 1. Asignar Corte
        if not interaction.guild.chunked:
            await interaction.guild.chunk(cache=True)
            
        corte = elegir_corte_balanceada(interaction.guild)
        rol = interaction.guild.get_role(CORTES[corte]["role_id"])
        
        try:
            await member.add_roles(rol)
        except Exception as e:
            print(f"❌ Error asignando rol de discord: {e}")

        log_balance_cortes(
            interaction.guild,
            corte_asignado=corte,
            motivo=f"{member.display_name} ({mc_name}) asignado a {corte}"
        )

        # 2. Anuncio Público
        canal_anuncio = interaction.guild.get_channel(CANAL_ANUNCIO_ID)
        if canal_anuncio:
            await canal_anuncio.send(
                f"🎩✨ **¡El Sombrero Seleccionador ha hablado!** ✨🎩\n\n"
                f"👤 {member.mention} (`{mc_name}`) ha sido elegido para la **{CORTES[corte]['titulo']}**\n"
                f"🌟 ¡Que el destino guíe tu camino!"
            )

        # 3. Respuesta privada con Embed + Select Menu
        embed, archivo = crear_embed_corte(corte, mc_name)
        view = RoleSelectView(mc_name, corte, member.name)
        
        await interaction.response.send_message(
            embed=embed, 
            file=archivo, 
            view=view, 
            ephemeral=True
        )

class GorroButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="🎩 Descubrir mi corte", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        if interaction.channel.id != CANAL_GORRO_ID:
            await interaction.response.send_message(
                "❌ Este ritual solo puede realizarse aquí.",
                ephemeral=True
            )
            return

        if tiene_corte(interaction.user):
            await interaction.response.send_message(
                "❌ Ya perteneces a una corte.",
                ephemeral=True
            )
            return

        # En lugar de asignar directo, abrir Modal
        await interaction.response.send_modal(RegistroModal())

class GorroView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(GorroButton())

# -------- READY --------

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")

    for guild in bot.guilds:
        members = [m async for m in guild.fetch_members(limit=None)]
        print(f"👥 Miembros cargados: {len(members)}")

    canal = bot.get_channel(CANAL_GORRO_ID)
    if not canal:
        print("❌ Canal no encontrado")
        return

    # Opcional: Borrar mensajes viejos del bot para limpiar (con cuidado)
    # await canal.purge(limit=5) 

    embed = discord.Embed(
        title="🎩 El Sombrero Seleccionador",
        description="Presiona el botón para descubrir tu corte.\n⚠️ Decisión permanente.\n📝 Se te pedirá tu nombre de Minecraft.",
        color=0x2b2d42
    )

    archivo = discord.File("gorro.png", filename="gorro.png")
    embed.set_image(url="attachment://gorro.png")

    await canal.send(embed=embed, file=archivo, view=GorroView())
    print("✨ Mensaje del gorro creado")

bot.run(TOKEN)