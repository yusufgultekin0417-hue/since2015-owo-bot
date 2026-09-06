import random
import time
from datetime import datetime, timezone

import aiosqlite
import discord
from discord import app_commands
from discord.ext import commands

from database import DB_NAME, create_user


MESSAGE_COOLDOWN = 60
DAILY_OWO_LIMIT = 500

MIN_MESSAGE_OWO = 1
MAX_MESSAGE_OWO = 3

MIN_XP = 8
MAX_XP = 18


async def setup_activity_database():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS activity (
                user_id INTEGER PRIMARY KEY,
                daily_owo INTEGER NOT NULL DEFAULT 0,
                daily_date TEXT,
                total_messages INTEGER NOT NULL DEFAULT 0,
                last_message TEXT
            )
        """)

        await db.commit()


def level_required(level: int):
    return 100 + ((level - 1) * 75)


class Activity(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        # Son ödüllendirilen mesaj zamanı
        self.cooldowns = {}

        # Basit tekrar/spam koruması
        self.last_messages = {}

    async def get_activity(self, user_id: int):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        async with aiosqlite.connect(DB_NAME) as db:
            db.row_factory = aiosqlite.Row

            await db.execute(
                """
                INSERT OR IGNORE INTO activity
                (user_id, daily_owo, daily_date)
                VALUES (?, 0, ?)
                """,
                (user_id, today)
            )

            cursor = await db.execute(
                """
                SELECT *
                FROM activity
                WHERE user_id = ?
                """,
                (user_id,)
            )

            row = await cursor.fetchone()

            if row["daily_date"] != today:
                await db.execute(
                    """
                    UPDATE activity
                    SET daily_owo = 0,
                        daily_date = ?
                    WHERE user_id = ?
                    """,
                    (today, user_id)
                )

                await db.commit()

                cursor = await db.execute(
                    """
                    SELECT *
                    FROM activity
                    WHERE user_id = ?
                    """,
                    (user_id,)
                )

                row = await cursor.fetchone()

            return row

    async def reward_message(self, user_id: int):
        activity = await self.get_activity(user_id)

        remaining = DAILY_OWO_LIMIT - activity["daily_owo"]

        # Günlük OwO sınırı dolduysa XP verebiliriz,
        # fakat daha fazla OwO vermeyiz.
        owo_reward = 0

        if remaining > 0:
            owo_reward = random.randint(
                MIN_MESSAGE_OWO,
                MAX_MESSAGE_OWO
            )

            owo_reward = min(
                owo_reward,
                remaining
            )

        xp_reward = random.randint(
            MIN_XP,
            MAX_XP
        )

        await create_user(user_id)

        async with aiosqlite.connect(DB_NAME) as db:
            db.row_factory = aiosqlite.Row

            cursor = await db.execute(
                """
                SELECT xp, level
                FROM users
                WHERE user_id = ?
                """,
                (user_id,)
            )

            user = await cursor.fetchone()

            xp = user["xp"] + xp_reward
            level = user["level"]

            leveled_up = False

            while xp >= level_required(level):
                xp -= level_required(level)
                level += 1
                leveled_up = True

            await db.execute(
                """
                UPDATE users
                SET owo = owo + ?,
                    xp = ?,
                    level = ?
                WHERE user_id = ?
                """,
                (
                    owo_reward,
                    xp,
                    level,
                    user_id
                )
            )

            await db.execute(
                """
                UPDATE activity
                SET daily_owo = daily_owo + ?,
                    total_messages = total_messages + 1
                WHERE user_id = ?
                """,
                (
                    owo_reward,
                    user_id
                )
            )

            await db.commit()

        return {
            "owo": owo_reward,
            "xp": xp_reward,
            "level": level,
            "leveled_up": leveled_up
        }

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):

        if message.author.bot:
            return

        if not message.guild:
            return

        content = message.content.strip()

        # Çok kısa mesajlardan ödül yok
        if len(content) < 4:
            return

        uid = message.author.id
        now = time.time()

        # Aynı mesajı arka arkaya atarak kasmayı engelle
        previous = self.last_messages.get(uid)

        normalized = content.lower()

        if previous == normalized:
            return

        self.last_messages[uid] = normalized

        # 60 saniyede bir ödül
        last_reward = self.cooldowns.get(uid, 0)

        if now - last_reward < MESSAGE_COOLDOWN:
            return

        self.cooldowns[uid] = now

        reward = await self.reward_message(uid)

        # Her mesajda cevap atmayalım.
        # Sadece level atlandığında kutlama mesajı gönder.
        if reward["leveled_up"]:
            await message.channel.send(
                f"🎉 {message.author.mention} "
                f"**Level {reward['level']}** oldu! ⭐"
            )

    @app_commands.command(
        name="level",
        description="Level ve XP durumunu gösterir."
    )
    async def level(
        self,
        interaction: discord.Interaction,
        user: discord.Member | None = None
    ):

        target = user or interaction.user

        await create_user(target.id)

        async with aiosqlite.connect(DB_NAME) as db:
            db.row_factory = aiosqlite.Row

            cursor = await db.execute(
                """
                SELECT owo, xp, level
                FROM users
                WHERE user_id = ?
                """,
                (target.id,)
            )

            data = await cursor.fetchone()

        required = level_required(
            data["level"]
        )

        percent = min(
            data["xp"] / required,
            1
        )

        filled = int(percent * 10)

        bar = (
            "🟩" * filled +
            "⬛" * (10 - filled)
        )

        embed = discord.Embed(
            title=f"⭐ {target.display_name} • Level",
            description=(
                f"**Level {data['level']}**\n\n"
                f"{bar}\n"
                f"`{data['xp']:,} / {required:,} XP`\n\n"
                f"💰 **{data['owo']:,} OwO**"
            )
        )

        if target.display_avatar:
            embed.set_thumbnail(
                url=target.display_avatar.url
            )

        embed.set_footer(
            text="Since 2015 • Activity"
        )

        await interaction.response.send_message(
            embed=embed
        )

    @app_commands.command(
        name="activity",
        description="Bugünkü aktivite kazancını gösterir."
    )
    async def activity(
        self,
        interaction: discord.Interaction
    ):

        data = await self.get_activity(
            interaction.user.id
        )

        remaining = max(
            0,
            DAILY_OWO_LIMIT - data["daily_owo"]
        )

        embed = discord.Embed(
            title="💬 Günlük Aktivite",
            description=(
                f"💰 Bugün mesajlardan:\n"
                f"**{data['daily_owo']:,} / "
                f"{DAILY_OWO_LIMIT:,} OwO**\n\n"
                f"📥 Kalan kazanım:\n"
                f"**{remaining:,} OwO**\n\n"
                f"💬 Ödüllendirilen toplam mesaj:\n"
                f"**{data['total_messages']:,}**"
            )
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


async def setup(bot):
    await setup_activity_database()
    await bot.add_cog(Activity(bot))
