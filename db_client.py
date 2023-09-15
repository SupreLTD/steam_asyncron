import asyncpg
import psycopg2

from psycopg2 import extras
from environs import Env

env = Env()
env.read_env()


class DbPostgres:
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def fetch_one(self, query, arg=None, factory=None, clean=None):
        ''' Получает только одно ЕДИНСТВЕННОЕ значение (не ряд!) из таблицы
        :param query: Запрос
        :param arg: Переменные
        :param factory: dic (возвращает словарь - ключ/значение) или list (возвращает list)
        :param clean: С параметром вернет только значение. Без параметра вернет значение  в кортеже.
        '''
        try:
            with self.__connection(factory) as cur:
                self.__execute(cur, query, arg)
                return self.__fetch(cur, clean)

        except (Exception, psycopg2.Error) as error:
            self.__error(error)

    def fetch_all(self, query, arg=None, factory=None):
        """ Получает множетсвенные данные из таблицы
        :param query: Запрос
        :param arg: Переменные
        :param factory: dict (возвращает словарь - ключ/значение) или list (возвращает list)
        """
        try:
            with self.__connection(factory) as cur:
                self.__execute(cur, query, arg)
                return cur.fetchall()

        except (Exception, psycopg2.Error) as error:
            self.__error(error)

    def query_update(self, query: str, arg=None, message='Ok', many=False):
        """
        Обновляет данные в таблице и возвращает сообщение об успешной операции
        :param query: Запрос
        :param arg: Переменные
        :param message: Сообщение о выполненной операции в консоль
        :param many: 
        :return:
        """
        try:
            with self.__connection() as cur:
                self.__execute(cur, query, many, arg)
            print(message)

        except (Exception, psycopg2.Error) as error:
            self.__error(error)

    @classmethod
    def __connection(cls, factory=None):
        conn = psycopg2.connect(env.str("DB"))
        conn.autocommit = True
        # Dic - возвращает словарь - ключ/значение
        if factory == 'dict':
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # List - возвращает list (хотя и называется DictCursor)
        elif factory == 'list':
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Tuple
        else:
            cur = conn.cursor()

        return cur

    @staticmethod
    def __execute(cur, query, many, arg=None):
        # Метод 'execute' всегда возвращает None
        if many:
            if arg:
                cur.executemany(query, arg)
            else:
                cur.executemany(query)
        else:
            if arg:
                cur.execute(query, arg)
            else:
                cur.execute(query)

    @staticmethod
    def __fetch(cur, clean):
        # Если запрос был выполнен успешно, получим данные с помощью 'fetchone'
        if clean == None:
            fetch = cur.fetchone()
        else:
            fetch = cur.fetchone()[0]
        return fetch

    @staticmethod
    def __error(error):
        # В том числе, если в БД данных нет, будет ошибка на этапе fetchone
        print(error)


async def save_in_db(query: str, data: tuple | list[tuple], many: bool = False) -> None:
    """

    :param query: SQL query
    :param data: tuple or list
    :param many: if many is False -> working execute adn data is tuple,
                 if many is True -> working executemany and data is list[tuple]
    :return: None
    """
    async with await asyncpg.create_pool(env.str("DB")) as pool:
        async with pool.acquire() as conn:
            if many:
                await conn.executemany(query, data)
            else:
                await conn.fetch(query, data)
