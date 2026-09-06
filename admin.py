import aiosqlite
import discord
from discord import app_commands
from discord.ext import commands

from database import DB_NAME, create_user


class Admin(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="addowo",
        description="Bir kullanıcıya OwO ekler."
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def addowo(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        miktar: int
    ):
        if miktar <= 0:
            await interaction.response.send_message(
                "❌ Miktar 0'dan büyük olmalı.",
                ephemeral=True
            )
            return

        await create_user(user.id)

        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute(
                """
                UPDATE users
                SET owo = owo + ?
                WHERE user_id = ?
                """,
                (miktar, user.id)
            )

            await db.commit()

        await interaction.response.send_message(
            f"✅ {user.mention} kullanıcısına "
            f"**{miktar:,} OwO** eklendi.",
            ephemeral=True
        )

    @app_commands.command(
        name="removeowo",
        description="Bir kullanıcıdan OwO siler."
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def removeowo(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        miktar: int
    ):
        if miktar <= 0:
            await interaction.response.send_message(
                "❌ Geçersiz miktar.",
                ephemeral=True
            )
            return

        await create_user(user.id)

        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute(
                """
                UPDATE users
                SET owo = MAX(0, owo - ?)
                WHERE user_id = ?
                """,
                (miktar, user.id)
            )

            await db.commit()

        await interaction.response.send_message(
            f"✅ {user.mention} kullanıcısından "
            f"**{miktar:,} OwO** düşüldü.",
            ephemeral=True
        )

    @app_commands.command(
        name="setowo",
        description="Bir kullanıcının OwO bakiyesini ayarlar."
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def setowo(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        miktar: int
    ):
        if miktar < 0:
            miktar = 0

        await create_user(user.id)

        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute(
                """
                UPDATE users
                SET owo = ?
                WHERE user_id = ?
                """,
                (miktar, user.id)
            )

            await db.commit()

        await interaction.response.send_message(
            f"✅ {user.mention} bakiyesi "
            f"**{miktar:,} OwO** olarak ayarlandı.",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(
        Admin(bot)
    )
