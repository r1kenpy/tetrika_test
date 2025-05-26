import asyncio
import csv
import logging
from collections import defaultdict
from urllib import parse

from aiohttp import ClientResponse, ClientSession, ClientTimeout
from bs4 import BeautifulSoup

LOGGING_FORMAT = "%(asctime)s - %(levelname)s - %(funcName)s - %(message)s"
BASE_URL = "https://ru.wikipedia.org"
START_URL = f"{BASE_URL}/wiki/Категория:Животные_по_алфавиту"

TIMEOUT = ClientTimeout(10.0)

logger = logging.getLogger(__name__)
logging.basicConfig(format=LOGGING_FORMAT)
logger.setLevel(logging.INFO)


def create_csv_file(
    data: dict[str, int],
    file_name: str = "beasts",
    encoding: str = "utf-8",
    newline: str = "",
) -> None:
    """Создание файла с соличеством животных."""
    with open(
        f"{file_name}.csv",
        "w",
        encoding=encoding,
        newline=newline,
    ) as file:
        logger.info(data)
        writer = csv.writer(file)
        writer.writerows(list(data.items()))


def get_soup(page: str, parser: str = "lxml") -> BeautifulSoup:
    return BeautifulSoup(page, parser)


async def get_response(
    session: ClientSession,
    url: str,
    timeout: ClientTimeout = TIMEOUT,
) -> ClientResponse:
    """Запрос на получение страницы."""
    try:
        response = await session.get(url, timeout=timeout)
        response.raise_for_status()
        return response
    except Exception as e:
        logger.error(f"Ошибка при запросе на страницу {url=}: {e}")
        raise


async def get_next_page(table_with_beasts) -> str | None:
    """Поиск ссылки на следующую страницу."""
    div_tag = table_with_beasts.select_one("div")
    tags_a = div_tag.find_next_siblings("a")

    for tag_a in tags_a:
        if tag_a.text == "Следующая страница":
            next_page = tag_a.get("href", None)
            if next_page is None:
                return None
            return parse.urljoin(BASE_URL, next_page)
    return None


async def parse_pages_beasts(start_url: str = START_URL) -> dict[str, int]:
    """Парсинг страницы с животными и получение их количества."""
    beasts_data: dict[str, int] = defaultdict(int)
    next_page_url: str | None = start_url
    async with ClientSession() as session:

        while next_page_url is not None:
            try:
                r = await get_response(session, next_page_url)
                soup = get_soup(await r.text())
                table_with_beasts = soup.select_one("#mw-pages")
                all_class_beast = table_with_beasts.select(  # type: ignore
                    ".mw-category-group"
                )
                next_page_url = await get_next_page(table_with_beasts)
                for div in all_class_beast:
                    h3_tag = div.find("h3").text  # type: ignore
                    logger.info(h3_tag)
                    li_tags = div.select("ul > li")

                    beasts_data[h3_tag] += len(li_tags)
                logger.info(f"{beasts_data=}")

            except Exception as e:
                logger.error(f"Ошибка при парсинге страницы: {e}")
                break

    return dict(beasts_data)


async def main() -> None:
    try:
        beasts_data = await parse_pages_beasts()
        logger.info(f"{beasts_data=}")
        create_csv_file(beasts_data)
    except Exception as e:
        logger.error(e)


if __name__ == "__main__":

    try:
        logger.info("Запуск парсера")
        asyncio.run(main())
        logger.info("Парсинг закончен")
    except Exception as e:
        logger.error(e)
