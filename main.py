import asyncio
import re
from pathlib import Path

from playwright.async_api import Page, async_playwright

DATA_FOLDER = Path("./data")


async def collect_photos(page: Page) -> set[str]:
    photos = set()
    previous_height = 0
    scroll_offset = await page.evaluate("window.innerHeight")
    pic_re = re.compile(r"\.\/share\/[^\/]*\/photo\/[^\/]*")
    while True:
        new_photos = await page.get_by_role("link").all()
        new_photos = [await p.get_attribute("href") for p in new_photos]
        photos |= {p for p in new_photos if p and pic_re.match(p)}
        await page.evaluate(
            f"document.querySelector('c-wiz[__is_owner=true]').scrollTo(0, {previous_height + scroll_offset})",
        )
        await asyncio.sleep(0.3)
        current_height = await page.evaluate("document.querySelector('c-wiz[__is_owner=true]').scrollTop")
        if current_height == previous_height:
            return photos
        previous_height = current_height


async def main() -> None:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch_persistent_context(
            DATA_FOLDER / "usrdata",
            headless=False,
        )
        page = await browser.new_page()
        for url in (DATA_FOLDER / "albums.txt").read_text().splitlines():
            await page.goto(url)
            await page.wait_for_url("https://photos.google.com/share/*")
            print(page.url)
            photos = await collect_photos(page)
            print(len(photos))
        await page.wait_for_event("close", timeout=0)


if __name__ == "__main__":
    asyncio.run(main())
