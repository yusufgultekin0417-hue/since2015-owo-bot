import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

from database import setup_database

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")


intents = discord.Intents.default()
intents.message_content = True
intents.members = True


class Since2015Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):
        print("📦 Veritabanı hazırlanıyor...")
        await setup_database()

        extensions = [
    "economy",
    "casino",
    "shop"
        ]
            
            


        for extension in extensions:
            try:
                await self.load_extension(extension)
                print(f"✅ {extension}.py yüklendi.")
            except Exception as error:
                print(f"❌ {extension}.py yüklenemedi:")
                print(error)

        try:
            synced = await self.tree.sync()
            print(f"✅ {len(synced)} slash komutu Discord'a yüklendi.")
        except Exception as error:
            print("❌ Slash komutları senkronize edilemedi:")
            print(error)


bot = Since2015Bot()


@bot.event
async def on_ready():
    print("")
    print("=" * 45)
    print("🔥 SINCE 2015 OWO BOT AKTİF")
    print("=" * 45)

    print(f"🤖 Bot: {bot.user}")
    print(f"🆔 Bot ID: {bot.user.id}")
    print(f"🏠 Sunucu sayısı: {len(bot.guilds)}")
    print(f"⚡ Ping: {round(bot.latency * 1000)} ms")

    print("=" * 45)

    try:
        await bot.change_presence(
            status=discord.Status.online,
            activity=discord.Game(
                name="Since 2015 • /cash"
            )
        )
    except Exception as error:
        print(f"Presence hatası: {error}")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return

    if isinstance(error, commands.MissingPermissions):
        await ctx.send(
            "❌ Bu komutu kullanmak için yetkin yok."
        )
        return

    print(f"Prefix komut hatası: {error}")


@bot.command()
async def ping(ctx):
    ping_ms = round(bot.latency * 1000)

    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Bot gecikmesi: **{ping_ms} ms**"
    )

    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(administrator=True)
async def sync(ctx):
    try:
        synced = await bot.tree.sync()

        await ctx.send(
            f"✅ **{len(synced)} slash komutu** yeniden yüklendi."
        )

    except Exception as error:
        await ctx.send(
            f"❌ Sync hatası:\n```{error}```"
        )


if not TOKEN:
    raise RuntimeError(
        "\n"
        "DISCORD_TOKEN bulunamadı!\n"
        "\n"
        "Hosting panelinde environment variable ekle:\n"
        "DISCORD_TOKEN = bot_tokenin\n"
        "\n"
        "Tokeni GitHub kodunun içine yazma."
    )


bot.run(TOKEN)
