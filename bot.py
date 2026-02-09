import discord
from discord.ext import commands
import random
import os

# ========= CONFIG =========
print("ANNOUNCE_CHANNEL_ID =", repr(os.getenv("ANNOUNCE_CHANNEL_ID")))
TOKEN = os.getenv("DISCORD_TOKEN")
CANAL_GORRO_ID = int(os.getenv("CHANNEL_ID"))
CANAL_ANUNCIO_ID = int(os.getenv("ANNOUNCE_CHANNEL_ID"))

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

# ==========================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

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
    # Forzar recuento actualizado
    conteo = contar_miembros_por_corte(guild)
    max_miembros = max(conteo.values(), default=0)
    
    cortes = []
    pesos = []

    print(f"\n🎲 Calculando probabilidades para '{guild.name}' ({guild.member_count} miembros detectados)")
    
    # Identificar cortes con max miembros
    cortes_maximos = [c for c, n in conteo.items() if n == max_miembros]
    num_cortes = len(conteo)
    num_maximos = len(cortes_maximos)

    # Lógica de exclusión:
    # Si hay entre 1 y 3 cortes con el máximo, y NO son todos los cortes
    excluir_maximos = (1 <= num_maximos <= 3) and (num_maximos < num_cortes)

    if excluir_maximos:
        print(f"🚫 Excluyendo {num_maximos} corte(s) por tener máximo de miembros ({max_miembros}): {', '.join(cortes_maximos)}")
    else:
        print(f"⚠️ No se excluye nadie (Máximos empatados: {num_maximos}/{num_cortes})")

    # Recalcular max para los restantes si hubo exclusión (opcional, pero mantiene la fórmula consistente)
    # Si excluimos los max, el "nuevo max" es el siguiente más alto.
    # Pero la fórmula (max - actual + 1)^2 funciona igual si usamos el max global.
    # Usaremos el MAX GLOBAL para mantener la escala de pesos.

    for corte, cantidad in conteo.items():
        if excluir_maximos and corte in cortes_maximos:
            print(f"   ► {corte:10} | Cant: {cantidad:3} | Peso:    0 (EXCLUIDO)")
            continue

        # Fórmula: (max - actual + 1)^2
        peso = max(1, (max_miembros - cantidad + 1) ** 2)
        cortes.append(corte)
        pesos.append(peso)
        print(f"   ► {corte:10} | Cant: {cantidad:3} | Peso: {peso:4}")

    if not cortes:
        # Fallback de emergencia si algo falla y la lista queda vacía
        print("⚠️ ALERTA: Lista de cortes vacía tras filtrado. Usando modo fallback (todos igual probabilidad).")
        cortes = list(conteo.keys())
        pesos = [1] * len(cortes)

    eleccion = random.choices(cortes, weights=pesos, k=1)[0]
    print(f"✨ Resultado: {eleccion}\n")
    return eleccion

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

# -------- UI --------

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

        member = interaction.user

        if tiene_corte(member):
            await interaction.response.send_message(
                "❌ Ya perteneces a una corte.",
                ephemeral=True
            )
            return

        # Asegurar caché de miembros para conteo preciso
        if not interaction.guild.chunked:
            await interaction.guild.chunk(cache=True)
            
        corte = elegir_corte_balanceada(interaction.guild)
        rol = interaction.guild.get_role(CORTES[corte]["role_id"])
        await member.add_roles(rol)

        log_balance_cortes(
            interaction.guild,
            corte_asignado=corte,
            motivo=f"{member.display_name} asignado a {corte}"
        )

        # 🎉 MENSAJE PÚBLICO
        canal_anuncio = interaction.guild.get_channel(CANAL_ANUNCIO_ID)
        if canal_anuncio:
            await canal_anuncio.send(
                f"🎩✨ **¡El Sombrero Seleccionador ha hablado!** ✨🎩\n\n"
                f"👤 {member.mention} ha sido elegido para la **{CORTES[corte]['titulo']}**\n"
                f"🌟 ¡Que el destino guíe tu camino!"
            )

        embed, archivo = crear_embed_corte(corte)

        await interaction.response.send_message(
            embed=embed,
            file=archivo,
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
        members = [m async for m in guild.fetch_members(limit=None)]
        print(f"👥 Miembros cargados: {len(members)}")

    canal = bot.get_channel(CANAL_GORRO_ID)
    if not canal:
        print("❌ Canal no encontrado")
        return

    embed = discord.Embed(
        title="🎩 El Sombrero Seleccionador",
        description="Presiona el botón para descubrir tu corte.\n⚠️ Decisión permanente.",
        color=0x2b2d42
    )

    archivo = discord.File("gorro.png", filename="gorro.png")
    embed.set_image(url="attachment://gorro.png")

    await canal.send(embed=embed, file=archivo, view=GorroView())
    print("✨ Mensaje del gorro creado")

bot.run(TOKEN)