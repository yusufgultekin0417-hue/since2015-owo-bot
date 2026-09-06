import random
import time
from datetime import datetime, timezone

import aiosqlite
import discord
from discord import app_commands
from discord.ext import commands

from database import DB_NAME, create_user


DAILY_TASKS = [
    {
        "id": "msg10",
        "name": "Sohbetçi",
        "description": "10 ödüllendirilen mesaj gönder.",
        "target": 10,
        "reward": 1000,
    },
    {
        "id": "msg25",
        "name": "Aktif Üye",
        "description": "25 ödüllendirilen mesaj gönder.",
        "target": 25,
        "reward": 2500,
    },
    {
        "id": "msg50",
        "name": "Sunucu Canavarı",
        "description": "50 ödüllendirilen mesaj gönder.",
        "target": 50,
        "reward": 5000,
    }
]


async def setup_progression_database():
    async with aiosqlite.connect(DB_NAME) as db:

        await db.execute("""
            CREATE TABLE IF NOT EXISTS streaks (
                user_id INTEGER PRIMARY KEY,
                streak INTEGER NOT NULL DEFAULT 0,
                last_claim TEXT
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS task_claims (
                user_id INTEGER NOT NULL,
                task_id TEXT NOT NULL,
                claim_date TEXT NOT NULL,
                PRIMARY KEY (user_id, task_id, claim_date)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS weekly_claims (
                user_id INTEGER PRIMARY KEY,
                last_claim INTEGER NOT NULL DEFAULT 0
            )
        """)

        await db.commit()


def today():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


class Progression(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="profile",
        description="Since 2015 profilini gösterir."
    )
    async def profile(
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
                SELECT owo, xp, level, daily_streak,
                       hunts, battles, wins
                FROM users
                WHERE user_id = ?
                """,
                (target.id,)
            )

            data = await cursor.fetchone()

            cursor = await db.execute(
                """
                SELECT total_messages
                FROM activity
                WHERE user_id = ?
                """,
                (target.id,)
            )

            activity = await cursor.fetchone()

        messages = activity["total_messages"] if activity else 0

        embed = discord.Embed(
            title=f"👤 {target.display_name}",
            description=(
                f"💰 **OwO:** `{data['owo']:,}`\n"
                f"⭐ **Level:** `{data['level']}`\n"
                f"✨ **XP:** `{data['xp']:,}`\n"
                f"🔥 **Streak:** `{data['daily_streak']}`\n"
                f"💬 **Aktif mesaj:** `{messages:,}`"
            )
        )

        embed.set_thumbnail(
            url=target.display_avatar.url
        )

        embed.set_footer(
            text="Since 2015 • Economy"
        )

        await interaction.response.send_message(
            embed=embed
        )

    @app_commands.command(
        name="top",
        description="En zengin üyeleri gösterir."
    )
    async def top(
        self,
        interaction: discord.Interaction
    ):
        async with aiosqlite.connect(DB_NAME) as db:
            db.row_factory = aiosqlite.Row

            cursor = await db.execute(
                """
                SELECT user_id, owo, level
                FROM users
                ORDER BY owo DESC
                LIMIT 10
                """
            )

            rows = await cursor.fetchall()

        if not rows:
            await interaction.response.send_message(
                "Henüz sıralama oluşmadı."
            )
            return

        lines = []

        medals = ["🥇", "🥈", "🥉"]

        for index, row in enumerate(rows):
            try:
                user = self.bot.get_user(
                    row["user_id"]
                )

                name = (
                    user.display_name
                    if user
                    else f"User {row['user_id']}"
                )

            except Exception:
                name = str(row["user_id"])

            prefix = (
                medals[index]
                if index < 3
                else f"`#{index + 1}`"
            )

            lines.append(
                f"{prefix} **{name}** — "
                f"💰 `{row['owo']:,}` OwO • "
                f"⭐ Lv.{row['level']}"
            )

        embed = discord.Embed(
            title="🏆 Since 2015 • TOP 10",
            description="\n".join(lines)
        )

        await interaction.response.send_message(
            embed=embed
        )

    @app_commands.command(
        name="tasks",
        description="Günlük görevlerini gösterir."
    )
    async def tasks(
        self,
        interaction: discord.Interaction
    ):
        uid = interaction.user.id

        async with aiosqlite.connect(DB_NAME) as db:
            db.row_factory = aiosqlite.Row

            cursor = await db.execute(
                """
                SELECT total_messages
                FROM activity
                WHERE user_id = ?
                """,
                (uid,)
            )

            row = await cursor.fetchone()

            progress = (
                row["total_messages"]
                if row
                else 0
            )

            cursor = await db.execute(
                """
                SELECT task_id
                FROM task_claims
                WHERE user_id = ?
                AND claim_date = ?
                """,
                (uid, today())
            )

            claimed_rows = await cursor.fetchall()

        claimed = {
            row["task_id"]
            for row in claimed_rows
        }

        lines = []

        for task in DAILY_TASKS:

            done = (
                progress >= task["target"]
            )

            claimed_text = (
                "✅ Alındı"
                if task["id"] in claimed
                else (
                    "🎁 Hazır"
                    if done
                    else "⏳ Devam ediyor"
                )
            )

            lines.append(
                f"**{task['name']}**\n"
                f"{task['description']}\n"
                f"İlerleme: `{min(progress, task['target'])}/{task['target']}`\n"
                f"Ödül: **{task['reward']:,} OwO** • {claimed_text}"
            )

        embed = discord.Embed(
            title="🎯 Günlük Görevler",
            description="\n\n".join(lines)
        )

        embed.set_footer(
            text="Hazır görevler için /claimtask"
        )

        await interaction.response.send_message(
            embed=embed
        )

    @app_commands.command(
        name="claimtask",
        description="Tamamladığın günlük görevin ödülünü al."
    )
    @app_commands.choices(
        gorev=[
            app_commands.Choice(
                name="Sohbetçi • 10 mesaj",
                value="msg10"
            ),
            app_commands.Choice(
                name="Aktif Üye • 25 mesaj",
                value="msg25"
            ),
            app_commands.Choice(
                name="Sunucu Canavarı • 50 mesaj",
                value="msg50"
            )
        ]
    )
    async def claimtask(
        self,
        interaction: discord.Interaction,
        gorev: app_commands.Choice[str]
    ):
        uid = interaction.user.id

        task = next(
            (
                task
                for task in DAILY_TASKS
                if task["id"] == gorev.value
            ),
            None
        )

        if not task:
            await interaction.response.send_message(
                "❌ Görev bulunamadı.",
                ephemeral=True
            )
            return

        async with aiosqlite.connect(DB_NAME) as db:
            db.row_factory = aiosqlite.Row

            cursor = await db.execute(
                """
                SELECT total_messages
                FROM activity
                WHERE user_id = ?
                """,
                (uid,)
            )

            row = await cursor.fetchone()

            progress = (
                row["total_messages"]
                if row
                else 0
            )

            if progress < task["target"]:
                await interaction.response.send_message(
                    f"❌ Görev henüz tamamlanmadı.\n"
                    f"`{progress}/{task['target']}`",
                    ephemeral=True
                )
                return

            try:
                await db.execute(
                    """
                    INSERT INTO task_claims (
                        user_id,
                        task_id,
                        claim_date
                    )
                    VALUES (?, ?, ?)
                    """,
                    (
                        uid,
                        task["id"],
                        today()
                    )
                )

            except aiosqlite.IntegrityError:
                await interaction.response.send_message(
                    "❌ Bu görevin ödülünü bugün zaten aldın.",
                    ephemeral=True
                )
                return

            await create_user(uid)

            await db.execute(
                """
                UPDATE users
                SET owo = owo + ?
                WHERE user_id = ?
                """,
                (
                    task["reward"],
                    uid
                )
            )

            await db.commit()

        await interaction.response.send_message(
            f"🎯 **{task['name']} tamamlandı!**\n"
            f"💰 +**{task['reward']:,} OwO**"
        )

    @app_commands.command(
        name="weekly",
        description="Haftalık ödülünü al."
    )
    async def weekly(
        self,
        interaction: discord.Interaction
    ):
        uid = interaction.user.id

        now = int(time.time())

        cooldown = 7 * 24 * 60 * 60

        await create_user(uid)

        async with aiosqlite.connect(DB_NAME) as db:
            db.row_factory = aiosqlite.Row

            cursor = await db.execute(
                """
                SELECT last_claim
                FROM weekly_claims
                WHERE user_id = ?
                """,
                (uid,)
            )

            row = await cursor.fetchone()

            last_claim = (
                row["last_claim"]
                if row
                else 0
            )

            if now - last_claim < cooldown:

                remaining = cooldown - (
                    now - last_claim
                )

                days = remaining // 86400
                hours = (
                    remaining % 86400
                ) // 3600

                await interaction.response.send_message(
                    f"⏳ Haftalık ödül için "
                    f"**{days}g {hours}sa** bekle.",
                    ephemeral=True
                )
                return

            reward = random.randint(
                15_000,
                40_000
            )

            await db.execute(
                """
                INSERT INTO weekly_claims (
                    user_id,
                    last_claim
                )
                VALUES (?, ?)
                ON CONFLICT(user_id)
                DO UPDATE SET
                    last_claim = excluded.last_claim
                """,
                (uid, now)
            )

            await db.execute(
                """
                UPDATE users
                SET owo = owo + ?
                WHERE user_id = ?
                """,
                (reward, uid)
            )

            await db.commit()

        await interaction.response.send_message(
            f"🎁 **Haftalık ödül!**\n"
            f"💰 +**{reward:,} OwO**"
        )


async def setup(bot):
    await setup_progression_database()
    await bot.add_cog(
        Progression(bot)
      )
