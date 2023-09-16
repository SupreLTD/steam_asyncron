import pandas as pd
from funcy import chunks

from db_client import DbPostgres

db = DbPostgres()


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


write_to_csv()
