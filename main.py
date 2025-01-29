import asyncio
import re
from collections.abc import AsyncGenerator

from playwright.async_api import Page, async_playwright

from config import ALBUMS_FILE, USER_DATA_FOLDER


async def get_photo_ids(page: Page, album_id: str, key: str) -> list[str]:
    photos: dict[str, None] = {}
    previous_height = 0
    await page.goto(f"https://photos.google.com/share/{album_id}?key={key}")

    scroll_offset = await page.evaluate("window.innerHeight") / 2
    while True:
        new_photos = await page.get_by_role("link").all()
        new_photos = [await p.get_attribute("href") for p in new_photos]
        photos |= {
            p: None for p_link in new_photos if p_link is not None for p in re.findall(r"photo\/([^\/?]+)", p_link)
        }
        await page.evaluate(
            f"document.querySelector('c-wiz[__is_owner=true]').scrollTo(0, {previous_height + scroll_offset})",
        )
        await asyncio.sleep(0.3)
        current_height = await page.evaluate("document.querySelector('c-wiz[__is_owner=true]').scrollTop")
        if current_height == previous_height:
            return list(photos)
        previous_height = current_height


async def load_album_ids(page: Page) -> AsyncGenerator[tuple[str, str]]:
    for url in ALBUMS_FILE.read_text().splitlines():
        await page.goto(url)
        await page.wait_for_url("https://photos.google.com/share/*")
        galbum_id, gkey = re.findall(r"share\/([^\/?]+).*[?&]key=([^\/&]+)", page.url)[0]
        yield galbum_id, gkey


async def main() -> None:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch_persistent_context(
            USER_DATA_FOLDER,
            headless=False,
        )
        page = await browser.new_page()
        async for album, key in load_album_ids(page):
            photos = await get_photo_ids(page, album, key)
            print(photos)
            print(len(photos))
        # await page.wait_for_event("close", timeout=0)


if __name__ == "__main__":
    asyncio.run(main())
