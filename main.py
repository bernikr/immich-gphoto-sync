import asyncio

from playwright.async_api import async_playwright

import google_photos as gphoto
import immich
from config import ALBUMS_FILE, USER_DATA_FOLDER
from db import get_db


async def main() -> None:
    async with async_playwright() as playwright, get_db() as db:
        browser = await playwright.chromium.launch_persistent_context(
            USER_DATA_FOLDER,
            headless=False,
        )
        page = await browser.new_page()
        for url in ALBUMS_FILE.read_text().splitlines():
            album_id, key, title = await gphoto.load_album_meta(page, url)
            album = await db.get_or_create_album(album_id, key)
            if album.immich_id is None:
                album.immich_id = await immich.create_album(title)
        # await page.wait_for_event("close", timeout=0)


if __name__ == "__main__":
    asyncio.run(main())
