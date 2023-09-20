import asyncio
from random import shuffle, choice

from aiohttp import ClientSession
from funcy import chunks
from tenacity import retry

from db_client import ids_for_fast, update_price_fast
from models import Price
from loguru import logger

with open('proxies_for_fast.txt') as f:
    proxies = [i.strip() for i in f.readlines()]
proxies.append('')


@retry
async def get_data(session: ClientSession, url: str) -> list[tuple]:
    data = []
    proxy = choice(proxies)
    async with session.get(url, proxy=proxy) as response:
        assert response.status == 200
        response = await response.json()
        for k, v in response.items():
            try:
                raw = Price(**{'appid': k}, **v['data'])
                data.append((raw.price_overview.initial, raw.price_overview.final, raw.appid))
            except Exception as e:
                continue

    return data


async def fast_price() -> None:
    async with ClientSession() as session:
        ids = await ids_for_fast()
        currency = ('tr', 'kz', 'ar', 'ru')
        for cur in currency:
            shuffle(ids)
            params = [','.join(i) for i in list(chunks(950, ids))]
            urls = [
                f"https://store.steampowered.com/api/appdetails?cc={cur}&filters=price_overview&appids={i}"
                for i in params]
            logger.info(f"Parsing {cur} now")
            tasks = []
            for url in urls:
                task = asyncio.create_task(get_data(session, url))
                tasks.append(task)
            result = await asyncio.gather(*tasks)
            result = sum(result, [])
            await update_price_fast(cur, result)
            logger.info(f"Updated {cur} | total: {len(result)}")


asyncio.run(fast_price())
