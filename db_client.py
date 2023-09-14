import asyncpg
import asyncio
from environs import Env
from faker import Faker

faker = Faker()

env = Env()
env.read_env()


async def make_request():
    db_pool = await asyncpg.create_pool(env.str("DB"))
    await db_pool.executemany("""INSERT INTO test(name, surname) VALUES ($1, $2)""",
                              [tuple(faker.name().split()[:2]) for _ in range(1000)])


asyncio.run(make_request())
