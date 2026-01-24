import discord
from discord.ext import commands
import random
import os

# ========= CONFIG =========
TOKEN = os.getenv("DISCORD_TOKEN")

CANAL_GORRO_ID = os.getenv("CHANNEL_ID")
# SOLO este canal puede usar el gorro

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
            "Arquitectura limpia y abierta, con sensación de luz constante y rayos de sol.\n\n"
            "Estética luminosa, sin vegetación ni agua protagonista."
        ),
        "imagen": "dia.png"
    },

    "verano": {
        "role_id": 1459983874447905066,
        "titulo": "🔥 Corte del Verano",
        "descripcion": (
            "Estética costera con arena clara, arenisca y tonos azul agua desaturados.\n\n"
            "Pueblo construido en la costa, con el mar al fondo, no atravesando la ciudad.\n\n"
            "Ambiente relajado, luminoso y marino."
        ),
        "imagen": "verano.png"
    },

    "otono": {
        "role_id": 1459983917175017642,
        "titulo": "🍂 Corte del Otoño",
        "descripcion": (
            "Bosque denso con tonos naranjas, rojos y marrones.\n\n"
            "Casas de piedra, madera oscura y detalles rústicos, integradas entre los árboles.\n\n"
            "Sin lagos ni ríos, sensación cálida y salvaje."
        ),
        "imagen": "otono.png"
    },

    "invierno": {
        "role_id": 1459983780797481020,
        "titulo": "❄️ Corte del Invierno",
        "descripcion": (
            "Paisaje cubierto de nieve y hielo, con tonos blancos, grises y azules.\n\n"
            "Construcciones sólidas de piedra y cuarzo, sin vegetación ni agua visible.\n\n"
            "Ambiente frío, limpio y fortificado."
        ),
        "imagen": "invierno.png"
    },
    "primavera": {
        "role_id": 1459983943146410176,
        "titulo": "🌸 Corte de la Primavera",
        "descripcion": (
            "Colores verdes vivos, rosados y blancos.\n\n"
            "Construcciones rodeadas de vegetación, flores y madera clara.\n\n"
            "Ambiente natural, florecido y luminoso, con sensación de renovación."
        ),
        "imagen": "primavera.png"
    }    
    #,"noche": {
    #    "role_id": 1459983478480310435,
    #    "titulo": "🌙 Corte de la Noche",
    #    "descripcion": (
    #        "Arquitectura elegante con tonos morado, azul oscuro y negro, combinados con blanco luminoso.\n\n"
    #        "Uso de cuarzo, madera oscura, pizarra y luces suaves que simulan estrellas.\n\n"
    #        "Ambiente nocturno, refinado y bien iluminado."
    #    ),
    #    "imagen": "noche.png"
    #},
}

# ==========================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # solo si usas roles / miembros

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

    nombre_imagen = data["imagen"]

    embed.set_image(url=f"attachment://{nombre_imagen}")
    embed.set_footer(text="El destino ha sido decidido.")

    archivo = discord.File(nombre_imagen, filename=nombre_imagen)
    return embed, archivo


# -------- BOTÓN DISMISS --------

class DismissButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="❌ Dismiss",
            style=discord.ButtonStyle.secondary
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await interaction.delete_original_response()

class DismissView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(DismissButton())

# -------- BOTÓN GORRO --------

class GorroButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="🎩 Descubrir mi corte",
            style=discord.ButtonStyle.primary
        )

    async def callback(self, interaction: discord.Interaction):
        # 🔒 SOLO UN CANAL
        if interaction.channel.id != CANAL_GORRO_ID:
            await interaction.response.send_message(
                "❌ Este ritual solo puede realizarse en el canal designado.",
                ephemeral=True
            )
            return

        member = interaction.user

        if tiene_corte(member):
            await interaction.response.send_message(
                "❌ Ya perteneces a una corte. El destino no se repite.",
                ephemeral=True
            )
            return

        corte = random.choice(list(CORTES.keys()))
        rol = interaction.guild.get_role(CORTES[corte]["role_id"])

        await member.add_roles(rol)

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

    canal = bot.get_channel(CANAL_GORRO_ID)
    if canal is None:
        print("❌ No se pudo encontrar el canal del gorro")
        return

    # 🔥 BORRAR MENSAJES ANTERIORES DEL BOT
    async for message in canal.history(limit=50):
        if message.author == bot.user:
            # Opcional: solo borrar los que tengan el título correcto
            if message.embeds:
                embed = message.embeds[0]
                if embed.title and "Gorro Seleccionador" in embed.title:
                    await message.delete()
                    print("🗑️ Mensaje anterior del gorro eliminado")

    # 🆕 CREAR MENSAJE NUEVO
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

    await canal.send(
        embed=embed,
        file=archivo,
        view=GorroView()
    )
    print("✨ Mensaje del gorro creado automáticamente")

bot.run(TOKEN)
