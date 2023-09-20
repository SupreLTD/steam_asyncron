import asyncio

from fast_prise_parser import fast_price


def main() -> None:
    asyncio.run(fast_price())
    asyncio.run(parse())


if __name__ == '__main__':
    main()
