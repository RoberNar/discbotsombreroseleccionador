import discord
from discord.ext import commands
import random
import os

# ========= CONFIG =========
TOKEN = os.getenv("DISCORD_TOKEN")
CANAL_GORRO_ID = int(os.getenv("CHANNEL_ID"))

DEBUG_BALANCE = True

CORTES = {
    "amanecer": {
        "role_id": 1459983740653535334,
        "titulo": "🌅 Corte del Amanecer",
        "descripcion": (
            "Paleta suave de naranjas claros, rosados y violetas.\n\n"
            "Edificaciones altas, terrazas y estructuras elevadas que recuerdan a estar cerca de las nubes.\n\n"
            "Luz cálida y ambiente etéreo, como un amanecer permanente."
        ),
        "imagen": "amanecer.png"
    },
    "dia": {
        "role_id": 1459983708466577736,
        "titulo": "☀️ Corte del Día",
        "descripcion": (
            "Construcciones claras y cálidas en cuarzo, amarillos y dorados.\n\n"
            "Arquitectura limpia y abierta, con sensación de luz constante.\n\n"
            "Estética luminosa."
        ),
        "imagen": "dia.png"
    },
    "verano": {
        "role_id": 1459983874447905066,
        "titulo": "🔥 Corte del Verano",
        "descripcion": (
            "Estética costera con arena clara y tonos azul agua.\n\n"
            "Ambiente relajado y marino."
        ),
        "imagen": "verano.png"
    },
    "otono": {
        "role_id": 1459983917175017642,
        "titulo": "🍂 Corte del Otoño",
        "descripcion": (
            "Bosque denso con tonos naranjas y rojos.\n\n"
            "Sensación cálida y salvaje."
        ),
        "imagen": "otono.png"
    },
    "invierno": {
        "role_id": 1459983780797481020,
        "titulo": "❄️ Corte del Invierno",
        "descripcion": (
            "Paisaje cubierto de nieve y hielo.\n\n"
            "Ambiente frío y fortificado."
        ),
        "imagen": "invierno.png"
    },
    "primavera": {
        "role_id": 1459983943146410176,
        "titulo": "🌸 Corte de la Primavera",
        "descripcion": (
            "Vegetación viva y flores.\n\n"
            "Sensación de renovación."
        ),
        "imagen": "primavera.png"
    },
    "noche": {
        "role_id": 1459983478480310435,
        "titulo": "🌙 Corte de la Noche",
        "descripcion": (
            "Arquitectura elegante con tonos morado, azul oscuro y negro, combinados con blanco luminoso.\n\n"
            "Uso de cuarzo, madera oscura, pizarra y luces suaves que simulan estrellas.\n\n"
            "Ambiente nocturno, refinado y bien iluminado."
        ),
        "imagen": "noche.png"
    }
}

# ==========================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# -------- UTIL --------

def tiene_corte(member: discord.Member):
    return any(
        role.id == data["role_id"]
        for role in member.roles
        for data in CORTES.values()
    )

def crear_embed_corte(key):
    data = CORTES[key]

    embed = discord.Embed(
        title=data["titulo"],
        description=data["descripcion"],
        color=0x6a4c93
    )

    embed.set_image(url=f"attachment://{data['imagen']}")
    embed.set_footer(text="El destino ha sido decidido.")

    archivo = discord.File(data["imagen"], filename=data["imagen"])
    return embed, archivo

def contar_miembros_por_corte(guild: discord.Guild):
    conteo = {}
    for key, data in CORTES.items():
        rol = guild.get_role(data["role_id"])
        conteo[key] = len(rol.members) if rol else 0
    return conteo

#def log_balance_cortes(guild: discord.Guild, motivo=""):
#    if not DEBUG_BALANCE:
#        return
#
#    conteo = contar_miembros_por_corte(guild)
#    max_miembros = max(conteo.values(), default=0)
#
#    cortes = []
#    pesos = []
#
#    print("\n📊 ===== BALANCE DE CORTES =====")
#    if motivo:
#        print(f"📝 Motivo: {motivo}")
#
#    for corte, cantidad in conteo.items():
#        peso = (max_miembros - cantidad) + 1
#        cortes.append(corte)
#        pesos.append(peso)
#        print(f"• {corte.upper():10} | miembros: {cantidad:2} | peso: {peso}")
#
#    total = sum(pesos)
#
#    print("📈 ===== PROBABILIDADES =====")
#    for corte, peso in zip(cortes, pesos):
#        porcentaje = (peso / total) * 100 if total > 0 else 0
#        print(f"→ {corte.upper():10}: {porcentaje:6.2f}%")
#
#    print("================================\n")

def elegir_corte_balanceada(guild: discord.Guild):
    conteo = contar_miembros_por_corte(guild)
    max_miembros = max(conteo.values(), default=0)

    cortes = []
    pesos = []

    for corte, cantidad in conteo.items():
        peso = (max_miembros - cantidad) + 1
        cortes.append(corte)
        pesos.append(peso)

    return random.choices(cortes, weights=pesos, k=1)[0]

# -------- UI --------

class DismissButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="❌ Dismiss", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await interaction.delete_original_response()

class DismissView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(DismissButton())

class GorroButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="🎩 Descubrir mi corte",
            style=discord.ButtonStyle.primary
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.channel.id != CANAL_GORRO_ID:
            await interaction.response.send_message(
                "❌ Este ritual solo puede realizarse en el canal designado.",
                ephemeral=True
            )
            return

        member = interaction.user

        if tiene_corte(member):
            await interaction.response.send_message(
                "❌ Ya perteneces a una corte.",
                ephemeral=True
            )
            return

        corte = elegir_corte_balanceada(interaction.guild)
        rol = interaction.guild.get_role(CORTES[corte]["role_id"])

        await member.add_roles(rol)

        log_balance_cortes(
            interaction.guild,
            motivo=f"{member.display_name} asignado a {corte}"
        )

        embed, archivo = crear_embed_corte(corte)

        await interaction.response.send_message(
            embed=embed,
            file=archivo,
            view=DismissView(),
            ephemeral=True
        )

class GorroView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(GorroButton())

# -------- READY --------

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")

    for guild in bot.guilds:
        # ⬇️ DESCARGA REAL DE MIEMBROS (NO SOLO CACHE PASIVO)
        members = [m async for m in guild.fetch_members(limit=None)]
        print(f"👥 Miembros cargados: {len(members)}")

        log_balance_cortes(guild, motivo="Inicio del bot")

    canal = bot.get_channel(CANAL_GORRO_ID)
    if canal is None:
        print("❌ No se encontró el canal")
        return

    embed = discord.Embed(
        title="🎩 El Sombrero Seleccionador",
        description=(
            "Presiona el botón para descubrir a qué corte perteneces.\n"
            "⚠️ Esta decisión es permanente."
        ),
        color=0x2b2d42
    )

    archivo = discord.File("gorro.png", filename="gorro.png")
    embed.set_image(url="attachment://gorro.png")

    await canal.send(embed=embed, file=archivo, view=GorroView())
    print("✨ Mensaje del gorro creado")

bot.run(TOKEN)