import grequests
import requests
from bs4 import BeautifulSoup
from funcy import chunks
from tqdm import tqdm
from get_count import count
from loguru import logger
from db_client import DbPostgres

db = DbPostgres()

url = 'https://store.steampowered.com/search/results/?query=&start=150&count=100&dynamic_data=&force_infinite=1&category1=998,21&ndl=1&snr=1_7_7_230_7&infinite=1'


def get_all_links() -> None:
    cnt = count()
    print(cnt)
    params = ((cnt[0], "INSERT INTO games_links (link) VALUES (unnest(%s)) ON CONFLICT DO NOTHING", '988'),
              (cnt[1], "INSERT INTO dlc_links (link) VALUES (unnest(%s)) ON CONFLICT DO NOTHING", '21'))
    for param in params:

        links = [
            f'https://store.steampowered.com/search/results/?query=&start={str(i)}&count=100&dynamic_data=&force_infinite=1&category1=998,21&ndl=1&snr=1_7_7_230_7&infinite=1'
            for i in range(0, param[0], 100)]
        links.append(
            f'https://store.steampowered.com/search/results/?query=&start={str(param[0])}&count=100&dynamic_data=&force_infinite=1&category1={param[2]}&ndl=1&snr=1_7_7_230_7&infinite=1')
        links = list(chunks(200, links))
        for l in tqdm(links):
            urls = []
            for response in grequests.map(
                    (grequests.get(url) for url in l)):
                if response.status_code != 200:
                    logger.error(response.status_code)
                data = response.json()

                soup = BeautifulSoup(data['results_html'], 'lxml')
                if soup:
                    for a in soup.find_all('a', {'class': 'search_result_row ds_collapse_flag'}):
                        if a.find('div', {'class': 'discount_final_price'}):
                            link = a['href'].split('?')[0]
                            if 'bundle' in link or 'oundtrack' in link:
                                continue
                            urls.append(link)

            db.query_update(query=param[1], arg=(urls,), message="Saved")


get_all_links()
