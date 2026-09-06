import random
import time
import discord
from discord import app_commands
from discord.ext import commands

# Sunucu yeniden başlatıldığında sıfırlanan eğlence bakiyesi.
# Sonra bunu database.py'ye taşıyacağız.
fun_balances = {}
daily_plays = {}

START_BALANCE = 10_000
DAILY_GAME_LIMIT = 20


def get_balance(user_id):
    if user_id not in fun_balances:
        fun_balances[user_id] = START_BALANCE
    return fun_balances[user_id]


def new_day(user_id):
    today = time.strftime("%Y-%m-%d")
    data = daily_plays.get(user_id)

    if not data or data["day"] != today:
        daily_plays[user_id] = {
            "day": today,
            "used": 0
        }

    return daily_plays[user_id]


def use_game(user_id):
    data = new_day(user_id)

    if data["used"] >= DAILY_GAME_LIMIT:
        return False

    data["used"] += 1
    return True


class Casino(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="funbalance",
        description="Eğlence bakiyeni gösterir."
    )
    async def funbalance(self, interaction: discord.Interaction):
        balance = get_balance(interaction.user.id)
        plays = new_day(interaction.user.id)

        await interaction.response.send_message(
            f"🎮 **Fun Coin:** `{balance:,}`\n"
            f"🎟️ Günlük hak: "
            f"`{DAILY_GAME_LIMIT - plays['used']}/{DAILY_GAME_LIMIT}`"
        )

    @app_commands.command(
        name="risk",
        description="Fun Coin ile risk al."
    )
    async def risk(
        self,
        interaction: discord.Interaction,
        miktar: int
    ):
        uid = interaction.user.id
        balance = get_balance(uid)

        if miktar < 100:
            await interaction.response.send_message(
                "❌ Minimum miktar **100 Fun Coin**.",
                ephemeral=True
            )
            return

        if miktar > balance:
            await interaction.response.send_message(
                "❌ Yeterli Fun Coin'in yok.",
                ephemeral=True
            )
            return

        if not use_game(uid):
            await interaction.response.send_message(
                "🎟️ Bugünkü oyun haklarının hepsini kullandın.",
                ephemeral=True
            )
            return

        roll = random.random()

        if roll < 0.60:
            fun_balances[uid] -= miktar
            result = (
                f"💀 Kaybettin!\n"
                f"**-{miktar:,} Fun Coin**"
            )

        elif roll < 0.90:
            profit = int(miktar * 0.5)
            fun_balances[uid] += profit
            result = (
                f"🔥 Kazandın!\n"
                f"**+{profit:,} Fun Coin**"
            )

        elif roll < 0.99:
            profit = miktar
            fun_balances[uid] += profit
            result = (
                f"💎 2X!\n"
                f"**+{profit:,} Fun Coin**"
            )

        else:
            profit = miktar * 4
            fun_balances[uid] += profit
            result = (
                f"🚨 **JACKPOT!**\n"
                f"**+{profit:,} Fun Coin**"
            )

        remaining = DAILY_GAME_LIMIT - new_day(uid)["used"]

        await interaction.response.send_message(
            f"🎲 **SINCE 2015 • RISK**\n\n"
            f"{result}\n\n"
            f"💰 Bakiye: **{fun_balances[uid]:,}**\n"
            f"🎟️ Bugün kalan hak: **{remaining}**"
        )

    @app_commands.command(
        name="coinflip",
        description="Yazı veya tura seç."
    )
    @app_commands.choices(secim=[
        app_commands.Choice(name="Yazı", value="yazi"),
        app_commands.Choice(name="Tura", value="tura")
    ])
    async def coinflip(
        self,
        interaction: discord.Interaction,
        secim: app_commands.Choice[str],
        miktar: int
    ):
        uid = interaction.user.id
        balance = get_balance(uid)

        if miktar < 100 or miktar > balance:
            await interaction.response.send_message(
                "❌ Geçersiz miktar.",
                ephemeral=True
            )
            return

        if not use_game(uid):
            await interaction.response.send_message(
                "🎟️ Günlük oyun hakkın bitti.",
                ephemeral=True
            )
            return

        result = random.choice(["yazi", "tura"])

        if secim.value == result:
            fun_balances[uid] += miktar
            text = f"✅ Kazandın! **+{miktar:,}**"
        else:
            fun_balances[uid] -= miktar
            text = f"❌ Kaybettin! **-{miktar:,}**"

        readable = "YAZI" if result == "yazi" else "TURA"

        await interaction.response.send_message(
            f"🪙 **{readable}!**\n\n"
            f"{text}\n"
            f"💰 Bakiye: **{fun_balances[uid]:,} Fun Coin**"
        )


async def setup(bot):
    await bot.add_cog(Casino(bot))
