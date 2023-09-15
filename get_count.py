import requests
from bs4 import BeautifulSoup

url = 'https://store.steampowered.com/search/results/'

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
    # 'Set-Cookie': 'BY|e309cb4f6636dad2ba5ce17094fee8b1'
}

params = {
    'query': '',
    'start': 10,
    'count': 50,
    'dynamic_data': '',
    'force_infinite': 1,
    'hidef2p': 1,
    'sort_by': '_ASC',
    'category1': 998,
    'snr': '1_7_7_230_7',
    'ndl': 1,
    'infinite': 1,
}
prox = 'http://ravil911:QnFHoxnfYw@185.18.123.217:50100'
proxy = {'http://': prox, 'https://': prox}


def count():
    games = requests.get(url, headers=headers,  params=params, proxies=proxy).json()['total_count']
    params['category1'] = 21
    dlc = requests.get(url, headers=headers,  params=params, proxies=proxy).json()['total_count']
    return games, dlc

