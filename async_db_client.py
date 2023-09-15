import asyncio
from time import perf_counter

import asyncpg
from environs import Env
from faker import Faker

faker = Faker()

env = Env()
env.read_env()


async def save_in_db(query: str, data: tuple | list[tuple], many: bool = False) -> None:
    """

    :param query: SQL query
    :param data: tuple or list
    :param many: if many is False -> working execute adn data is tuple,
                 if many is True -> working executemany and data is list[tuple]
    :return: None
    """
    async with await asyncpg.create_pool(env.str("DB")) as pool:
        async with pool.acquire() as conn:
            if many:
                await conn.executemany(query, data)
            else:
                await conn.fetch(query, data)


async def get_links() -> list:
    db_pool = await asyncpg.create_pool(env.str("DB"))
    print([list(i.values()) for i in await db_pool.fetch("""SELECT name, surname from test""")])

#
# asyncio.run(
#     save_in_db("""TRUNCATE test; INSERT INTO test(name, surname) VALUES ($1, $2)""", [tuple(faker.name().split()[:2]) for _ in range(1000000)], many=True))
# asyncio.run(get_links())