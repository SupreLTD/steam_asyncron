import asyncio
import random
import re

from funcy import chunks
from tenacity import retry
from get_count import count
import requests
from bs4 import BeautifulSoup
from aiohttp import ClientSession
from loguru import logger
from db_client import save_in_db, DbPostgres


db = DbPostgres()

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
cookies = {
    'Steam_Language': 'russian',
}

with open('proxies.txt') as f:
    proxies = [i.strip() for i in f.readlines()]


async def get_data(session: ClientSession, url: str, dls: bool = False) -> tuple:
    proxy = random.choice(proxies)
    async with session.get(url, proxy=proxy) as response:
        logger.info(f'response status: {response.status} | {url}')
        assert response.status == 200
        soup = BeautifulSoup(await response.text(), 'lxml')
        assert soup is not None
        data = {}
        title = soup.find('div', {'id': 'appHubAppName'})
        pattern = r'/app/(\d+)/'
        match = re.search(pattern, url)

        # appid
        data['AppId'] = match.group(1) if match else None

        # Заголовок
        data['Заголовок'] = title.get_text() if title else ''

        # Цены и издания
        data['Издания'] = None
        data['Цены изданий'] = None
        data['Цены изданий без скидки'] = None
        try:
            game_area_purchase = soup.find('div', {'class': 'game_area_purchase'})
            if game_area_purchase:
                game_area_purchase_game = game_area_purchase.find_all('div', {'class': 'game_area_purchase_game'})
                if game_area_purchase_game:
                    editions = []
                    prices = []
                    old_prices = []
                    for game in game_area_purchase_game:
                        if not "demo_above_purchase" in game.get('class'):
                            edition = game.find('h1')
                            if edition and not 'НАБОР(?)' in edition.get_text(strip=True):
                                price = game.find(attrs={"data-price-final": True})
                                if price:
                                    editions.append(edition.get_text(strip=True).replace('Купить', ''))
                                    prices.append(
                                        str(round(float(price.get('data-price-final')) / 100, 2))) if price else None

                                    old_price = game.find('div', {'class': 'discount_original_price'})
                                    if old_price:
                                        old_price = old_price.get_text()
                                        old_price = old_price.replace(',', '.') if old_price else None
                                        match = re.search(r"(\d+(?:\.\d+)?)", old_price)
                                        old_price = match.group(1) if match else None
                                        old_prices.append(old_price)

                    data['Издания'] = ', '.join(editions)
                    data['Цены изданий'] = ', '.join(prices)
                    data['Цены изданий без скидки'] = ', '.join(old_prices)
        except Exception:
            logger.error(f"Цены и издания: {url}")
            return ()

        # Разработчик, издатель
        data['Разработчик'] = ""
        data['Издатель'] = ""
        try:
            glance_ctn_responsive_left = soup.find('div', {'class': 'glance_ctn_responsive_left'})
            if glance_ctn_responsive_left:
                dev_row = glance_ctn_responsive_left.find_all('div', {'class': 'dev_row'})
                if dev_row:
                    try:
                        data['Разработчик'] = dev_row[0].find('div', {'class': 'summary column'}).get_text(strip=True)
                    except:
                        data['Разработчик'] = ''
                    try:
                        data['Издатель'] = dev_row[1].find('div', {'class': 'summary column'}).get_text(strip=True)
                    except:
                        data['Издатель'] = ""
        except Exception as ex:
            logger.error(f"Разработчик, издатель: {ex} - {url}")

        data['Дополнение'] = 'dls_name'

        # Жанр
        genres = []
        try:
            genre_span = soup.select('#genresAndManufacturer > span')
            genre_list = genre_span[0] if genre_span else None
            if genre_list:
                for genre in genre_list.find_all('a'):
                    genres.append(genre.get_text())
        except Exception as ex:
            logger.error(f"Жанр: {ex} - {url}")
        data['Жанр'] = ', '.join(genres)

        # Дата выхода
        date = ''
        try:
            date = soup.find('div', {'class': 'date'}).get_text()

        except Exception as ex:
            logger.error(f"Дата выхода: {ex} - {url}")
        data['Дата выхода'] = date

        # Платформа
        data['Платформы'] = None
        try:
            platforms = []
            for platform in soup.find_all('div', {'class': 'sysreq_tab'}):
                platforms.append(platform.get_text()) if platform else None
            data['Платформы'] = ','.join(platforms)
        except Exception as ex:
            logger.error(f"Платформа: {ex} - {url}")

        if not data['Платформы']:
            data['Платформы'] = "Windows"

        # Язык
        language = 0
        try:
            language_table = soup.find('table', {'class': 'game_language_options'})
            if language_table:
                for lang_tr in language_table.find_all('tr'):
                    lang_td = lang_tr.find('td', {'class': 'ellipsis'})
                    if lang_td and 'русский' in lang_td.get_text():
                        lang_td = lang_tr.find_all('td', {'class': 'checkcol'})
                        for td in range(3):
                            try:
                                language += 1 if lang_td[td] and lang_td[td].find('span') else None
                            except:
                                None
                        break
        except Exception as ex:
            logger.error(f"Язык: {ex} - {url}")

        if language == 3:
            language = 'Полная локализация'
        elif language < 3 and language > 0:
            language = 'Только субтитры'
        elif language == 0:
            language = 'Нет'

        data['Язык'] = language

        # Картинки
        preview = soup.find('img', {'class': 'game_header_image_full'})
        preview = preview.get('src') if preview else None
        imgs = soup.find_all('a', {'class': 'highlight_screenshot_link'})
        imgs = [img.get('href') for img in imgs] if imgs else []
        data['Обложка'] = preview
        data['Изображения'] = ', '.join(imgs)

        # Описание
        description = soup.find('div', {'id': 'game_area_description'})
        # data['Описание'] = ''.join(str(item).strip() for item in description.contents) if description else ''
        data['Описание'] = description.get_text() if description else ''

        # Системные требования
        left_col = soup.find('div', {'class': 'game_area_sys_req sysreq_content active'})
        li_elements = left_col.select('ul.bb_ul li') if left_col else []

        data['ОС'] = ""
        data['Процессор'] = ""
        data['Оперативная память'] = ""
        data['Видеокарта'] = ""
        data['DirectX'] = ""
        data['Место на диске'] = ""

        for li_element in li_elements:
            strong_tag = li_element.find('strong')
            if strong_tag:
                key = strong_tag.get_text(strip=True)
                value = re.sub(rf'^{re.escape(key)}:', '', li_element.get_text(strip=True))
                value = value.replace(key, '').strip()

                if 'ОС' in key:
                    data['ОС'] = value
                if 'Процессор' in key:
                    data['Процессор'] = value
                if 'Оперативная память' in key:
                    data['Оперативная память'] = value
                if 'Видеокарта' in key:
                    data['Видеокарта'] = value
                if 'DirectX' in key:
                    data['DirectX'] = value
                if 'Место на диске' in key:
                    data['Место на диске'] = value

    print(data)


async def parse():
    categories = (('games_links', 'games'), ('dlc_links', 'dlc'))
    for category in categories:
        query = f"SELECT link FROM {category[0]}"
        query_save = f"INSERT INTO {category[1]} VALUES ()"
        links = list(chunks(1000, list(map(lambda el: el[0], db.fetch_all(query)))))

        for link in links:
            async with ClientSession(headers=headers, cookies=cookies) as session:
                tasks = []
                for url in link:
                    task = asyncio.create_task(get_data(session, url))
                    tasks.append(task)
                result = await asyncio.gather(*tasks)
                # result = sum(result, [])
                # await save_in_db(query_save, result, many=True)


if __name__ == '__main__':
    asyncio.run(parse())
