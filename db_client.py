import asyncpg
import asyncio
from environs import Env
from faker import Faker

faker = Faker()

env = Env()
env.read_env()


async def save_in_db(query: str, data: tuple | list[tuple], many: str = False) -> None:
    """

    :param query: SQL query
    :param data: tuple or list
    :param many: if many is False -> working execute adn data is tuple,
                 if many is True -> working executemany and data is list[tuple]
    :return: None
    """
    db_pool = await asyncpg.create_pool(env.str("DB"))
    if many:
        await db_pool.executemany(query, data)
    else:
        await db_pool.execute(query, data)
