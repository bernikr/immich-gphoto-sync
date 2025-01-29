import asyncio
import re
from pathlib import Path

from playwright.async_api import Page


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


async def load_album_meta(page: Page, url: str) -> tuple[str, str, str]:
    await page.goto(url)
    await page.wait_for_url("https://photos.google.com/share/*")
    galbum_id, gkey = re.findall(r"share\/([^\/?]+).*[?&]key=([^\/&]+)", page.url)[0]
    title = (await page.title()).replace(" - Google Photos", "")
    return galbum_id, gkey, title


async def download_photo(page: Page, album_id: str, key: str, image_id: str) -> tuple[Path, str]:
    await page.goto(f"https://photos.google.com/share/{album_id}/photo/{image_id}?key={key}")
    await asyncio.sleep(0.3)
    async with page.expect_download() as download_info:
        await page.keyboard.press("Shift+D")
    download = await download_info.value
    return await download.path(), download.suggested_filename
