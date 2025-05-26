from asyncio import sleep
from http import HTTPStatus
from urllib import parse

from aiohttp import ClientSession, web
from aiohttp.test_utils import AioHTTPTestCase
from solution import (
    BASE_URL,
    get_next_page,
    get_response,
    get_soup,
    parse_pages_beasts,
)
from yarl import URL


class TestRequest(AioHTTPTestCase):

    async def get_application(self):
        async def timeout_handler(request):
            await sleep(12)
            return web.Response(text="timeout")

        async def succes_handler(request):
            return web.Response(text="Succes")

        async def first_page_handler(request):
            html = """
        <div id="mw-pages">
            <div style="font-size:85%">Инструменты:
                <ul>
                    <li><a href="Искать по категории" title="Животные по алфавиту">Искать по категории</a></li>
                </ul>
            </div>
            <a href="/next">Следующая страница</a>
            <div class="mw-category mw-category-columns">
                <div class="mw-category-group">
                    <h3>А</h3>
                    <ul>
                        <li><a href="/1" title="Аардоникс">Аардоникс</a></li>
                        <li><a href="/2" title="Абботины">Абботины</a></li>
                    </ul>
                </div>
            </div>
        </div>
        """
            return web.Response(text=html)

        async def second_page_handler(request):
            html = """
        <div id="mw-pages">
            <div style="font-size:85%">Инструменты:
                <ul>
                    <li><a href="Искать по категории" title="Животные по алфавиту">Искать по категории</a></li>
                </ul>
            </div>
            <a href="/next">Следующая страница</a>
            <div class="mw-category mw-category-columns">
                <div class="mw-category-group">
                    <h3>А</h3>
                    <ul>
                        <li><a href="/1" title="Животное 1">Животное 1</a></li>
                        <li><a href="/2" title="Животное 2">Животное 2</a></li>
                    </ul>
                </div>
                <div class="mw-category-group">
                    <h3>Б</h3>
                    <ul>
                        <li><a href="/1" title="Животное 3">Животное 3</a></li>
                        <li><a href="/2" title="Животное 4">Животное 4</a></li>
                    </ul>
                </div>
                <div class="mw-category-group">
                    <h3>В</h3>
                    <ul>
                        <li><a href="/1" title="Животное 5">Животное 5</a></li>
                        <li><a href="/2" title="Животное 6">Животное 6</a></li>
                    </ul>
                </div>
            </div>
        </div>
        """
            return web.Response(text=html)

        app = web.Application()
        app.router.add_get("/timeout", timeout_handler)
        app.router.add_get("/first", first_page_handler)
        app.router.add_get("/second", second_page_handler)
        app.router.add_get("/", succes_handler)
        return app

    @property
    def get_base_url(self):
        return URL(f"http://{self.server.host}:{self.server.port}")

    async def test_timeout(self):
        with self.assertRaises(TimeoutError):
            async with ClientSession() as session:
                await get_response(
                    session=session,
                    url=self.get_base_url / "timeout",
                )

    async def test_succes(self):
        async with ClientSession() as session:
            r = await get_response(
                session=session,
                url=self.get_base_url,
            )
            self.assertEqual(r.status, HTTPStatus.OK)
        self.assertEqual(await r.text(), "Succes")

    async def test_parse_first_page(self):
        expected = {"А": 2}
        data = await parse_pages_beasts(self.get_base_url / "first")
        self.assertEqual(data, expected)

    async def test_parse_second_page(self):
        expected = {"А": 2, "Б": 2, "В": 2}
        data = await parse_pages_beasts(self.get_base_url / "second")
        self.assertEqual(data, expected)

    async def test_get_next_page_not_found(self):
        html = """
            <div id="mw-pages">
                <div style="font-size:85%">Инструменты:
                    <ul>
                        <li><a href="Искать по категории" title="Животные по алфавиту">Искать по категории</a></li>
                    </ul>
                </div>
                
                <div class="mw-category mw-category-columns">
                    <div class="mw-category-group">
                        <h3>А</h3>
                        <ul>
                            <li><a href="/1" title="Животное 1>Животное 1</a></li>
                            <li><a href="/2" title="Животное 2>Животное 2</a></li>
                        </ul>
                    </div>
                </div>
            </div>
        """
        soup = get_soup(html)
        table = soup.select_one("#mw-pages")
        next_page = await get_next_page(table)
        self.assertIsNone(next_page)

    async def test_a_tag_dont_have_href(self):
        html = """
            <div id="mw-pages">
                <div style="font-size:85%">Инструменты:
                    <ul>
                        <li><a href="Искать по категории" title="Животные по алфавиту">Искать по категории</a></li>
                    </ul>
                </div>
                <a>Следующая страница</a>
                <div class="mw-category mw-category-columns">
                    <div class="mw-category-group">
                        <h3>А</h3>
                        <ul>
                            <li><a href="/1" title="Животное 1>Животное 1</a></li>
                            <li><a href="/2" title="Животное 2>Животное 2</a></li>
                        </ul>
                    </div>
                </div>
            </div>
        """
        soup = get_soup(html)
        table = soup.select_one("#mw-pages")
        next_page = await get_next_page(table)
        self.assertIsNone(next_page)

    async def test_get_next_page(self):
        html = """
            <div id="mw-pages">
                <div style="font-size:85%">Инструменты:
                    <ul>
                        <li><a href="Искать по категории" title="Животные по алфавиту">Искать по категории</a></li>
                    </ul>
                </div>
                <a href="/next">Следующая страница</a>
                <div class="mw-category mw-category-columns">
                    <div class="mw-category-group">
                        <h3>А</h3>
                        <ul>
                            <li><a href="/1" title="Животное 1>Животное 1</a></li>
                            <li><a href="/2" title="Животное 2>Животное 2</a></li>
                        </ul>
                    </div>
                </div>
            </div>
        """
        soup = get_soup(html)
        table = soup.select_one("#mw-pages")
        next_page = await get_next_page(table)
        self.assertEqual(next_page, parse.urljoin(BASE_URL, "/next"))
