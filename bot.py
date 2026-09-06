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
            intents=intents
        )

    async def setup_hook(self):
        # Veritabanını hazırla
        await setup_database()

        # Ekonomi sistemini yükle
        await self.load_extension("economy")

        # Slash komutlarını Discord'a gönder
        synced = await self.tree.sync()
        print(f"{len(synced)} slash komutu yüklendi.")


bot = Since2015Bot()


@bot.event
async def on_ready():
    print("=" * 40)
    print("🔥 SINCE 2015 OWO BOT AKTİF")
    print(f"🤖 Bot: {bot.user}")
    print(f"🏠 Sunucu: {len(bot.guilds)}")
    print(f"⚡ Ping: {round(bot.latency * 1000)}ms")
    print("=" * 40)


@bot.command()
async def ping(ctx):
    await ctx.send(
        f"🏓 Pong! `{round(bot.latency * 1000)}ms`"
    )


if not TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN bulunamadı! Hosting paneline token ekle."
    )

bot.run(TOKEN)
