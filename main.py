import asyncio

from links_refresher import refresh_links
from parser_games import parse


def main() -> None:
    asyncio.run(refresh_links())
    asyncio.run(parse())


if __name__ == '__main__':
    main()
