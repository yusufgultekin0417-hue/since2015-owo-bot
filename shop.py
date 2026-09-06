import time
import discord
import aiosqlite

from discord import app_commands
from discord.ext import commands

from database import DB_NAME


PRODUCTS = {
    "play250": {
        "name": "250 TL Google Play",
        "emoji": "🎮",
        "price": 100_000_000,
    },
    "nitro3m": {
        "name": "3 Aylık Discord Nitro",
        "emoji": "💎",
        "price": 500_000_000,
    },
}


async def setup_shop_database():
    async with aiosqlite.connect(DB_NAME) as db:

        # Stok tablosu
        await db.execute("""
            CREATE TABLE IF NOT EXISTS shop_stock (
                item_id TEXT PRIMARY KEY,
                stock INTEGER NOT NULL DEFAULT 0
            )
        """)

        # Ürünleri stok tablosuna ekle
        for item_id in PRODUCTS:
            await db.execute(
                """
                INSERT OR IGNORE INTO shop_stock (item_id, stock)
                VALUES (?, 0)
                """,
                (item_id,)
            )

        await db.commit()


async def get_stock(item_id: str):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT stock
            FROM shop_stock
            WHERE item_id = ?
            """,
            (item_id,)
        )

        row = await cursor.fetchone()

        if not row:
            return 0

        return row[0]


async def get_balance(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT owo
            FROM users
            WHERE user_id = ?
            """,
            (user_id,)
        )

        row = await cursor.fetchone()

        if not row:
            return 0

        return row[0]


async def get_pending_orders(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(
            """
            SELECT *
            FROM purchases
            WHERE user_id = ?
            AND status = 'pending'
            ORDER BY id DESC
            """,
            (user_id,)
        )

        return await cursor.fetchall()


class Shop(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="shop",
        description="Since 2015 ödül mağazasını gösterir."
    )
    async def shop(self, interaction: discord.Interaction):

        embed = discord.Embed(
            title="🛒 Since 2015 • Ödül Mağazası",
            description=(
                "Sunucuda OwO biriktir ve ödüllere ulaş.\n\n"
                "⚠️ Stokta olmayan ürün satın alınamaz."
            )
        )

        play_stock = await get_stock("play250")
        nitro_stock = await get_stock("nitro3m")

        embed.add_field(
            name="🎮 250 TL Google Play",
            value=(
                "💰 **100.000.000 OwO**\n"
                f"📦 Stok: **{play_stock}**\n"
                "`/buy play250`"
            ),
            inline=False
        )

        embed.add_field(
            name="💎 3 Aylık Discord Nitro",
            value=(
                "💰 **500.000.000 OwO**\n"
                f"📦 Stok: **{nitro_stock}**\n"
                "`/buy nitro3m`"
            ),
            inline=False
        )

        embed.set_footer(
            text="Since 2015 • Economy"
        )

        await interaction.response.send_message(
            embed=embed
        )

    @app_commands.command(
        name="buy",
        description="OwO kullanarak mağazadan ödül satın al."
    )
    @app_commands.choices(
        urun=[
            app_commands.Choice(
                name="250 TL Google Play",
                value="play250"
            ),
            app_commands.Choice(
                name="3 Aylık Discord Nitro",
                value="nitro3m"
            )
        ]
    )
    async def buy(
        self,
        interaction: discord.Interaction,
        urun: app_commands.Choice[str]
    ):

        uid = interaction.user.id
        item_id = urun.value

        product = PRODUCTS.get(item_id)

        if not product:
            await interaction.response.send_message(
                "❌ Böyle bir ürün bulunamadı.",
                ephemeral=True
            )
            return

        # Aynı üründen bekleyen sipariş var mı?
        async with aiosqlite.connect(DB_NAME) as db:
            cursor = await db.execute(
                """
                SELECT id
                FROM purchases
                WHERE user_id = ?
                AND item_id = ?
                AND status = 'pending'
                """,
                (uid, item_id)
            )

            existing = await cursor.fetchone()

        if existing:
            await interaction.response.send_message(
                "⏳ Bu ürün için zaten bekleyen bir talebin var.",
                ephemeral=True
            )
            return

        try:
            async with aiosqlite.connect(DB_NAME) as db:

                # Aynı anda iki kişi son stoğu almasın.
                await db.execute("BEGIN IMMEDIATE")

                cursor = await db.execute(
                    """
                    SELECT owo
                    FROM users
                    WHERE user_id = ?
                    """,
                    (uid,)
                )

                user = await cursor.fetchone()

                balance = user[0] if user else 0

                cursor = await db.execute(
                    """
                    SELECT stock
                    FROM shop_stock
                    WHERE item_id = ?
                    """,
                    (item_id,)
                )

                stock_row = await cursor.fetchone()

                stock = stock_row[0] if stock_row else 0

                if stock <= 0:
                    await db.rollback()

                    await interaction.response.send_message(
                        f"❌ {product['name']} şu anda **stokta yok**.",
                        ephemeral=True
                    )
                    return

                if balance < product["price"]:
                    missing = product["price"] - balance

                    await db.rollback()

                    await interaction.response.send_message(
                        f"❌ Yeterli OwO'n yok.\n\n"
                        f"💰 Bakiye: **{balance:,} OwO**\n"
                        f"🏷️ Fiyat: **{product['price']:,} OwO**\n"
                        f"📉 Eksik: **{missing:,} OwO**",
                        ephemeral=True
                    )
                    return

                # Parayı düş
                await db.execute(
                    """
                    UPDATE users
                    SET owo = owo - ?
                    WHERE user_id = ?
                    """,
                    (
                        product["price"],
                        uid
                    )
                )

                # Stoğu düş
                await db.execute(
                    """
                    UPDATE shop_stock
                    SET stock = stock - 1
                    WHERE item_id = ?
                    """,
                    (item_id,)
                )

                # Siparişi oluştur
                cursor = await db.execute(
                    """
                    INSERT INTO purchases (
                        user_id,
                        item_id,
                        price,
                        status,
                        created_at
                    )
                    VALUES (?, ?, ?, 'pending', ?)
                    """,
                    (
                        uid,
                        item_id,
                        product["price"],
                        int(time.time())
                    )
                )

                order_id = cursor.lastrowid

                await db.commit()

        except Exception as error:

            print(f"Satın alma hatası: {error}")

            await interaction.response.send_message(
                "❌ Satın alma sırasında bir hata oluştu.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="✅ Ödül Talebi Oluşturuldu",
            description=(
                f"{interaction.user.mention}\n\n"
                f"{product['emoji']} **{product['name']}**\n"
                f"💰 **-{product['price']:,} OwO**\n\n"
                f"🧾 Talep ID: **#{order_id}**\n"
                "⏳ Durum: **Yönetici onayı bekliyor**"
            )
        )

        embed.set_footer(
            text="Ödül teslimi sunucu yönetimi tarafından yapılır."
        )

        await interaction.response.send_message(
            embed=embed
        )

    @app_commands.command(
        name="orders",
        description="Bekleyen ödül taleplerini gösterir."
    )
    async def orders(
        self,
        interaction: discord.Interaction
    ):

        orders = await get_pending_orders(
            interaction.user.id
        )

        if not orders:

            await interaction.response.send_message(
                "📭 Bekleyen ödül talebin yok.",
                ephemeral=True
            )

            return

        lines = []

        for order in orders[:10]:

            product = PRODUCTS.get(
                order["item_id"]
            )

            if product:
                name = product["name"]
                emoji = product["emoji"]
            else:
                name = order["item_id"]
                emoji = "📦"

            lines.append(
                f"{emoji} **#{order['id']}** • {name}\n"
                f"💰 `{order['price']:,} OwO` • ⏳ Bekliyor"
            )

        embed = discord.Embed(
            title="📦 Ödül Taleplerim",
            description="\n\n".join(lines)
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

    @app_commands.command(
        name="setstock",
        description="Mağaza stok miktarını değiştirir."
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    @app_commands.choices(
        urun=[
            app_commands.Choice(
                name="250 TL Google Play",
                value="play250"
            ),
            app_commands.Choice(
                name="3 Aylık Discord Nitro",
                value="nitro3m"
            )
        ]
    )
    async def setstock(
        self,
        interaction: discord.Interaction,
        urun: app_commands.Choice[str],
        miktar: int
    ):

        if miktar < 0:

            await interaction.response.send_message(
                "❌ Stok negatif olamaz.",
                ephemeral=True
            )

            return

        async with aiosqlite.connect(DB_NAME) as db:

            await db.execute(
                """
                INSERT INTO shop_stock (
                    item_id,
                    stock
                )
                VALUES (?, ?)
                ON CONFLICT(item_id)
                DO UPDATE SET stock = excluded.stock
                """,
                (
                    urun.value,
                    miktar
                )
            )

            await db.commit()

        product = PRODUCTS[
            urun.value
        ]

        await interaction.response.send_message(
            f"✅ {product['emoji']} **{product['name']}** "
            f"stoğu **{miktar}** olarak ayarlandı.",
            ephemeral=True
        )

    @app_commands.command(
        name="approve",
        description="Bir ödül talebini onaylar."
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def approve(
        self,
        interaction: discord.Interaction,
        talep_id: int
    ):

        async with aiosqlite.connect(DB_NAME) as db:

            db.row_factory = aiosqlite.Row

            cursor = await db.execute(
                """
                SELECT *
                FROM purchases
                WHERE id = ?
                """,
                (talep_id,)
            )

            order = await cursor.fetchone()

            if not order:

                await interaction.response.send_message(
                    "❌ Talep bulunamadı.",
                    ephemeral=True
                )

                return

            if order["status"] != "pending":

                await interaction.response.send_message(
                    f"❌ Bu talebin durumu zaten "
                    f"**{order['status']}**.",
                    ephemeral=True
                )

                return

            await db.execute(
                """
                UPDATE purchases
                SET status = 'approved'
                WHERE id = ?
                """,
                (talep_id,)
            )

            await db.commit()

        product = PRODUCTS.get(
            order["item_id"]
        )

        product_name = (
            product["name"]
            if product
            else order["item_id"]
        )

        await interaction.response.send_message(
            f"✅ Talep **#{talep_id}** onaylandı.\n"
            f"📦 **{product_name}**"
        )

        try:

            user = await self.bot.fetch_user(
                order["user_id"]
            )

            await user.send(
                f"🎉 **Since 2015 ödül talebin onaylandı!**\n\n"
                f"📦 {product_name}\n"
                f"🧾 Talep: **#{talep_id}**\n\n"
                "Ödül teslimi için sunucu yönetimi seninle iletişime geçecek."
            )

        except Exception:
            pass

    @app_commands.command(
        name="reject",
        description="Talebi reddeder ve OwO'yu iade eder."
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def reject(
        self,
        interaction: discord.Interaction,
        talep_id: int
    ):

        async with aiosqlite.connect(DB_NAME) as db:

            db.row_factory = aiosqlite.Row

            await db.execute(
                "BEGIN IMMEDIATE"
            )

            cursor = await db.execute(
                """
                SELECT *
                FROM purchases
                WHERE id = ?
                """,
                (talep_id,)
            )

            order = await cursor.fetchone()

            if not order:

                await db.rollback()

                await interaction.response.send_message(
                    "❌ Talep bulunamadı.",
                    ephemeral=True
                )

                return

            if order["status"] != "pending":

                await db.rollback()

                await interaction.response.send_message(
                    f"❌ Bu talep zaten "
                    f"**{order['status']}** durumunda.",
                    ephemeral=True
                )

                return

            # Parayı geri ver
            await db.execute(
                """
                UPDATE users
                SET owo = owo + ?
                WHERE user_id = ?
                """,
                (
                    order["price"],
                    order["user_id"]
                )
            )

            # Stoğu geri koy
            await db.execute(
                """
                UPDATE shop_stock
                SET stock = stock + 1
                WHERE item_id = ?
                """,
                (order["item_id"],)
            )

            await db.execute(
                """
                UPDATE purchases
                SET status = 'rejected'
                WHERE id = ?
                """,
                (talep_id,)
            )

            await db.commit()

        await interaction.response.send_message(
            f"❌ Talep **#{talep_id}** reddedildi.\n"
            f"💰 **{order['price']:,} OwO** kullanıcıya iade edildi."
        )


async def setup(bot):

    await setup_shop_database()

    await bot.add_cog(
        Shop(bot)
          )
