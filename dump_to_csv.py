import asyncio
import os
import pandas as pd
from funcy import chunks
import smtplib

from db_client import DbPostgres, get_all_games

db = DbPostgres()


def cleaner() -> None:
    for i in os.listdir('data'):
        os.remove('data/' + i)


def write_to_csv() -> None:
    columns = ['AppId',
               'Заголовок',
               'Издания',
               'Цены изданий Россия',
               'Цены изданий без скидки Россия',
               'Разработчик',
               'Издатель',
               'Дополнение',
               'Жанр',
               'Дата выхода',
               'Платформы',
               'Язык',
               'Обложка',
               'Изображения',
               'Описание',
               'Системные требования']

    data = list(chunks(15000, db.fetch_all("""SELECT appid, title, edition, price, full_price, developer, 
                                                    publisher, dlc, genre, date, platform, language, cover, images, 
                                                    description, requirements FROM games""", factory='list')))
    for number, items in enumerate(data):
        df = pd.DataFrame(items, columns=columns)
        df.to_csv(fr"data/games_{number}.csv", index=False)


def write_data():
    cleaner()
    columns = ['AppId',
               'Заголовок',
               'Издания',
               'Цены изданий Турция',
               'Цены изданий без скидки Турция',
               'Цены изданий Аргентина',
               'Цены изданий без скидки Аргентина',
               'Цены изданий Казахстан',
               'Цены изданий без скидки Казахстан',
               'Цены изданий Россия',
               'Цены изданий без скидки Россия',
               'Разработчик',
               'Издатель',
               'Дополнение',
               'Жанр',
               'Дата выхода',
               'Платформы',
               'Язык',
               'Обложка',
               'Изображения',
               'Описание',
               'Системные требования']

    data = list(chunks(15_000, asyncio.run(get_all_games())))
    for number, items in enumerate(data):
        df = pd.DataFrame(items, columns=columns)
        df.to_csv(fr"data/games_{number}.csv", index=False)

def dump():
    cleaner()
    write_to_csv()

write_data()