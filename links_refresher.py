import asyncio
from tqdm import tqdm
from funcy import chunks
from tenacity import retry
from bs4 import BeautifulSoup
from aiohttp import ClientSession
from loguru import logger
from db_client import save_in_db

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/116.0',
    'Accept': 'text/javascript, text/html, application/xml, text/xml, */*',
    'Accept-Language': 'en-US,en;q=0.5',
    # 'Accept-Encoding': 'gzip, deflate, br',
    'X-Requested-With': 'XMLHttpRequest',
    'X-Prototype-Version': '1.7',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
}

url = ('https://store.steampowered.com/search/results/?query=&start=0&count=50&dynamic_data=&force_infinite=1&hidef2p'
       '=1sort_by=_ASC&category1=998,21&ndl=1&snr=1_7_7_230_7&infinite=1')


@retry
async def get_data(session: ClientSession, link: str) -> list[tuple]:
    links = []

    async with session.get(link) as response:
        logger.info(f'response status: {response.status}')
        assert response.status == 200

        data = await response.json()

        soup = BeautifulSoup(data['results_html'], 'lxml')
        if soup:
            for a in soup.find_all('a', {'class': 'search_result_row ds_collapse_flag'}):
                if a.find('div', {'class': 'discount_final_price'}):
                    link = a['href'].split('?')[0]
                    if 'bundle' in link or 'oundtrack' in link:
                        continue
                    links.append((link,))

    return links


async def refresh_links():
    async with ClientSession(headers=headers) as session:
        async with session.get(url=url) as response:
            count = await response.json()

        count = count['total_count']
        print(count)
        links = [
            (f"https://store.steampowered.com/search/results/?query=&start={str(i)}&count=100&dynamic_data"
             f"=&force_infinite=1&hidef2p=1sort_by=_ASC&category1=998,21&ndl=1&snr=1_7_7_230_7&infinite=1")
            for i in range(0, count, 100)
        ]
        links.append(
            f"https://store.steampowered.com/search/results/?query=&start={str(count)}&count=100&dynamic_data"
            f"=&force_infinite=1&hidef2p=1sort_by=_ASC&category1=998,21&ndl=1&snr=1_7_7_230_7&infinite=1")
        links = list(chunks(200, links))
        for bundle in tqdm(links, desc='Refresh links in DB: '):
            tasks = []
            for link in bundle:
                task = asyncio.create_task(get_data(session, link))
                tasks.append(task)
            result = await asyncio.gather(*tasks)
            result = sum(result, [])
            await save_in_db("""INSERT INTO links(link) VALUES ($1) ON CONFLICT DO NOTHING""", result, many=True)



