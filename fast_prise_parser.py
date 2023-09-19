import asyncio
import asyncpg
import aiohttp

from db_client import ids_for_fast

print(asyncio.run(ids_for_fast()))