import asyncio

from playwright.async_api import Page, async_playwright
from tqdm import tqdm

import google_photos as gphoto
import immich
from config import ALBUMS_FILE, HEADLESS, USER_DATA_FOLDER
from db import Album, Database, get_db


async def google_to_immich(page: Page, album: Album, google_id: str, db: Database) -> None:
    file, filename = await gphoto.download_photo(page, album.google_id, album.google_key, google_id)
    immich_id = await immich.upload_photo(file, filename)
    await immich.add_photo_to_album(album.immich_id, immich_id)
    await db.create_photo(album.id, google_id, immich_id, "to_immich")


async def main() -> None:
    async with async_playwright() as playwright, get_db() as db:
        browser = await playwright.chromium.launch_persistent_context(
            USER_DATA_FOLDER,
            headless=HEADLESS,
        )
        page = await browser.new_page()
        for url in ALBUMS_FILE.read_text().splitlines():
            album_id, key, title = await gphoto.load_album_meta(page, url)
            print(f"checcking album '{title}'")
            album = await db.get_or_create_album(album_id, key)
            if album.immich_id is None:
                album.immich_id = await immich.create_album(title)

            photos = await db.get_photos(album.id)
            google_photo_ids = set(await gphoto.get_photo_ids(page, album.google_id, album.google_key))
            immich_photo_ids = set(await immich.get_photo_ids(album.immich_id))

            new_on_google_photos = google_photo_ids - {p.google_id for p in photos}
            if new_on_google_photos:
                print("uploading images to Immich")
                for google_id in tqdm(new_on_google_photos):
                    await google_to_immich(page, album, google_id, db)

            deleted_on_google_photos = {p.google_id for p in photos} - google_photo_ids
            if deleted_on_google_photos:
                print(f"{len(deleted_on_google_photos)} photos deleted on Google, not yet implemented")

            new_on_immich = immich_photo_ids - {p.immich_id for p in photos}
            if new_on_immich:
                print(f"{len(new_on_immich)} new photos on Immich, not yet implemented")

            deleted_on_immich = {p.immich_id for p in photos} - immich_photo_ids
            if deleted_on_immich:
                print(f"{len(deleted_on_immich)} photos deleted on Immich, not yet implemented")


if __name__ == "__main__":
    asyncio.run(main())
