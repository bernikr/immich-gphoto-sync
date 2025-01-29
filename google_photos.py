import asyncio
import re
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from playwright.async_api import BrowserContext, Page, async_playwright

from config import HEADLESS, USER_DATA_FOLDER


class GooglePhotosApi:
    def __init__(self, browser: BrowserContext, page: Page) -> None:
        self.browser = browser
        self.page = page

    async def get_photo_ids(self, album_id: str, key: str) -> list[str]:
        photos: dict[str, None] = {}
        previous_height = 0
        await self.page.goto(f"https://photos.google.com/share/{album_id}?key={key}")

        scroll_offset = await self.page.evaluate("window.innerHeight") / 2
        while True:
            new_photos = await self.page.get_by_role("link").all()
            new_photos = [await p.get_attribute("href") for p in new_photos]
            photos |= {
                p: None for p_link in new_photos if p_link is not None for p in re.findall(r"photo\/([^\/?]+)", p_link)
            }
            await self.page.evaluate(
                f"document.querySelector('c-wiz[__is_owner=true]').scrollTo(0, {previous_height + scroll_offset})",
            )
            await asyncio.sleep(0.3)
            current_height = await self.page.evaluate("document.querySelector('c-wiz[__is_owner=true]').scrollTop")
            if current_height == previous_height:
                return list(photos)
            previous_height = current_height

    async def load_album_meta(self, url: str) -> tuple[str, str, str]:
        await self.page.goto(url)
        await self.page.wait_for_url("https://photos.google.com/share/*")
        galbum_id, gkey = re.findall(r"share\/([^\/?]+).*[?&]key=([^\/&]+)", self.page.url)[0]
        title = (await self.page.title()).replace(" - Google Photos", "")
        return galbum_id, gkey, title

    async def download_photo(self, album_id: str, key: str, image_id: str) -> tuple[Path, str]:
        await self.page.goto(f"https://photos.google.com/share/{album_id}/photo/{image_id}?key={key}")
        await asyncio.sleep(0.3)
        async with self.page.expect_download() as download_info:
            await self.page.keyboard.press("Shift+D")
        download = await download_info.value
        return await download.path(), download.suggested_filename


@asynccontextmanager
async def get_google_photos_api() -> AsyncGenerator[GooglePhotosApi]:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch_persistent_context(
            USER_DATA_FOLDER,
            headless=HEADLESS,
        )
        page = await browser.new_page()
        yield GooglePhotosApi(browser, page)
