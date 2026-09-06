import aiosqlite

DB_NAME = "since2015.db"


async def setup_database():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                owo INTEGER NOT NULL DEFAULT 0,
                xp INTEGER NOT NULL DEFAULT 0,
                level INTEGER NOT NULL DEFAULT 1,
                daily_streak INTEGER NOT NULL DEFAULT 0,
                hunts INTEGER NOT NULL DEFAULT 0,
                battles INTEGER NOT NULL DEFAULT 0,
                wins INTEGER NOT NULL DEFAULT 0
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                user_id INTEGER NOT NULL,
                item_id TEXT NOT NULL,
                amount INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (user_id, item_id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS animals (
                user_id INTEGER NOT NULL,
                animal_id TEXT NOT NULL,
                amount INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (user_id, animal_id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                item_id TEXT NOT NULL,
                price INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at INTEGER NOT NULL
            )
        """)

        await db.commit()


async def create_user(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
            (user_id,)
        )
        await db.commit()


async def get_user(user_id):
    await create_user(user_id)

    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,)
        )
        return await cursor.fetchone()


async def add_owo(user_id, amount):
    await create_user(user_id)

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE users SET owo = MAX(0, owo + ?) WHERE user_id = ?",
            (amount, user_id)
        )
        await db.commit()


async def get_balance(user_id):
    user = await get_user(user_id)
    return user["owo"]
