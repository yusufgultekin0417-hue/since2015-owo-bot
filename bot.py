import os
import traceback

import discord
from discord.ext import commands
from dotenv import load_dotenv

from database import setup_database


load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")


intents = discord.Intents.default()

intents.guilds = True
intents.members = True
intents.messages = True
intents.message_content = True


class Since2015Bot(commands.Bot):

    def __init__(self):

        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None,
            case_insensitive=True
        )

    async def setup_hook(self):

        print("")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(" SINCE 2015 • BAŞLATILIYOR")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        print("📦 Database hazırlanıyor...")

        await setup_database()

        print("✅ Database hazır.")

        extensions = [
            "economy",
            "casino",
            "shop",
            "activity",
            "progression",
            "admin"
        ]

        for extension in extensions:

            try:

                await self.load_extension(
                    extension
                )

                print(
                    f"✅ {extension}.py yüklendi."
                )

            except Exception as error:

                print(
                    f"❌ {extension}.py yüklenemedi!"
                )

                print(error)

                traceback.print_exc()

        try:

            commands_synced = (
                await self.tree.sync()
            )

            print("")
            print(
                f"✅ {len(commands_synced)} "
                f"slash komutu Discord'a gönderildi."
            )

        except Exception as error:

            print(
                "❌ Slash sync hatası:"
            )

            print(error)


bot = Since2015Bot()


@bot.event
async def on_ready():

    print("")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🔥 SINCE 2015 OWO BOT ONLINE")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    print(
        f"🤖 Bot: {bot.user}"
    )

    print(
        f"🆔 ID: {bot.user.id}"
    )

    print(
        f"🏠 Sunucu: {len(bot.guilds)}"
    )

    print(
        f"👥 Kullanıcı cache: "
        f"{len(bot.users)}"
    )

    print(
        f"⚡ Ping: "
        f"{round(bot.latency * 1000)}ms"
    )

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("")

    try:

        await bot.change_presence(
            status=discord.Status.online,
            activity=discord.Activity(
                type=discord.ActivityType.playing,
                name="Since 2015 • /shop"
            )
        )

    except Exception as error:

        print(
            f"Presence hatası: {error}"
        )


@bot.event
async def on_guild_join(guild):

    print(
        f"➕ Sunucuya eklendi: "
        f"{guild.name}"
    )


@bot.event
async def on_guild_remove(guild):

    print(
        f"➖ Sunucudan çıkarıldı: "
        f"{guild.name}"
    )


@bot.event
async def on_command_error(
    ctx,
    error
):

    if isinstance(
        error,
        commands.CommandNotFound
    ):
        return

    if isinstance(
        error,
        commands.MissingPermissions
    ):

        await ctx.send(
            "❌ Bu komut için yetkin yok."
        )

        return

    print(
        f"Prefix hata: {error}"
    )


@bot.tree.error
async def slash_error(
    interaction: discord.Interaction,
    error
):

    print(
        f"Slash command error: {error}"
    )

    traceback.print_exc()

    message = (
        "❌ Komut çalıştırılırken "
        "bir hata oluştu."
    )

    try:

        if interaction.response.is_done():

            await interaction.followup.send(
                message,
                ephemeral=True
            )

        else:

            await interaction.response.send_message(
                message,
                ephemeral=True
            )

    except Exception:

        pass


@bot.command()
async def ping(ctx):

    latency = round(
        bot.latency * 1000
    )

    embed = discord.Embed(
        title="🏓 Pong!",
        description=(
            f"⚡ **{latency} ms**\n\n"
            f"🔥 Since 2015 aktif."
        )
    )

    await ctx.send(
        embed=embed
    )


@bot.command()
@commands.has_permissions(
    administrator=True
)
async def sync(ctx):

    try:

        synced = await bot.tree.sync()

        await ctx.send(
            f"✅ **{len(synced)}** "
            f"slash komutu güncellendi."
        )

    except Exception as error:

        await ctx.send(
            f"❌ Sync hatası:\n"
            f"```{error}```"
        )


@bot.command()
@commands.has_permissions(
    administrator=True
)
async def reload(ctx):

    extensions = [
        "economy",
        "casino",
        "shop",
        "activity",
        "progression",
        "admin"
    ]

    success = 0

    for extension in extensions:

        try:

            await bot.reload_extension(
                extension
            )

            success += 1

        except Exception as error:

            print(
                f"{extension} reload hata:"
            )

            print(error)

    await bot.tree.sync()

    await ctx.send(
        f"🔄 **{success}/{len(extensions)}** "
        f"modül yeniden yüklendi."
    )


if not TOKEN:

    raise RuntimeError(
        "\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "DISCORD_TOKEN BULUNAMADI\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Tokeni GitHub koduna yazma.\n"
        "Hosting paneline environment variable ekle:\n\n"
        "DISCORD_TOKEN = SENIN_BOT_TOKENIN\n"
    )


bot.run(
    TOKEN,
    log_handler=None
)
