import asyncio
from random import shuffle, choice
from time import perf_counter

import asyncpg
from aiohttp import ClientSession
from funcy import chunks
from tenacity import retry

from db_client import ids_for_fast
from models import Price
from loguru import logger

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/116.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
}

with open('proxies_for_fast.txt') as f:
    proxies = [i.strip() for i in f.readlines()]
proxies.append('')
print(proxies)

ids = asyncio.run(ids_for_fast())


@retry
async def get_data(session: ClientSession, url: str):
    data = []
    proxy = choice(proxies)
    print(proxy)
    async with session.get(url, proxy=proxy) as response:
        assert response.status == 200
        response = await response.json()
        for k, v in response.items():
            try:
                raw = Price(**{'appid': k}, **v['data'])
                data.append((raw.price_overview.initial, raw.price_overview.final, raw.appid))
            except:
                logger.error(f'{k} | {v}')

    return data


async def fast_price():
    async with ClientSession() as session:
        # ids = await ids_for_fast()
        currency = ('tr', 'kz', 'ar', 'ru')
        for cur in currency:
            shuffle(ids)
            params = [','.join(i) for i in list(chunks(800, ids))]
            urls = [
                f"https://store.steampowered.com/api/appdetails?cc={cur}&filters=price_overview&appids={i}"
                for i in params]

            tasks = []
            for url in urls:
                task = asyncio.create_task(get_data(session, url))
                tasks.append(task)
            result = await asyncio.gather(*tasks)
            result = sum(result, [])
            print(result)
            print()


asyncio.run(fast_price())
