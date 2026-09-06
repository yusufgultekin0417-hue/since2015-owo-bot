import random
import time
import discord
from discord import app_commands
from discord.ext import commands

from database import create_user, get_user, add_owo


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.work_cooldowns = {}
        self.daily_cooldowns = {}

    @app_commands.command(name="cash", description="OwO bakiyeni gösterir.")
    async def cash(self, interaction: discord.Interaction):
        await create_user(interaction.user.id)
        user = await get_user(interaction.user.id)

        embed = discord.Embed(
            title="💰 Since 2015 • Cüzdan",
            description=(
                f"👤 {interaction.user.mention}\n\n"
                f"💵 **{user['owo']:,} OwO**"
            )
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="work", description="Çalışarak OwO kazan.")
    async def work(self, interaction: discord.Interaction):
        uid = interaction.user.id
        now = time.time()

        cooldown = 30 * 60
        last = self.work_cooldowns.get(uid, 0)

        if now - last < cooldown:
            remaining = int(cooldown - (now - last))

            minutes = remaining // 60
            seconds = remaining % 60

            await interaction.response.send_message(
                f"⏳ Tekrar çalışmak için **{minutes}dk {seconds}sn** bekle.",
                ephemeral=True
            )
            return

        # Para bilerek zor kazanılıyor.
        reward = random.randint(300, 1200)

        # Çok düşük ihtimalle bonus.
        if random.randint(1, 100) == 1:
            reward += random.randint(1500, 4000)
            bonus = "\n✨ **Şans bonusu yakaladın!**"
        else:
            bonus = ""

        await add_owo(uid, reward)
        self.work_cooldowns[uid] = now

        await interaction.response.send_message(
            f"💼 {interaction.user.mention} çalıştı.\n"
            f"💰 **+{reward:,} OwO** kazandı.{bonus}"
        )

    @app_commands.command(name="daily", description="Günlük OwO ödülünü al.")
    async def daily(self, interaction: discord.Interaction):
        uid = interaction.user.id
        now = time.time()

        cooldown = 24 * 60 * 60
        last = self.daily_cooldowns.get(uid, 0)

        if now - last < cooldown:
            remaining = int(cooldown - (now - last))

            hours = remaining // 3600
            minutes = (remaining % 3600) // 60

            await interaction.response.send_message(
                f"🕐 Günlük ödülünü zaten aldın.\n"
                f"Tekrar: **{hours}sa {minutes}dk**",
                ephemeral=True
            )
            return

        reward = random.randint(3000, 8000)

        await add_owo(uid, reward)
        self.daily_cooldowns[uid] = now

        await interaction.response.send_message(
            f"🎁 **Günlük Ödül**\n\n"
            f"{interaction.user.mention}\n"
            f"💰 **+{reward:,} OwO**"
        )


async def setup(bot):
    await bot.add_cog(Economy(bot))
