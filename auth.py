import asyncio

from playwright.async_api import async_playwright

from config import USER_DATA_FOLDER


async def main() -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            USER_DATA_FOLDER,
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
            ],
        )
        page = await browser.new_page()
        await page.goto("https://photos.google.com/")
        await page.wait_for_event("close", timeout=0)


asyncio.run(main())
