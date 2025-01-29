import asyncio
from tempfile import TemporaryDirectory

from tqdm import tqdm

import immich
from config import ALBUMS_FILE
from db import Album, Database, get_db
from google_photos import GooglePhotosApi, GooglePhotosApiError, get_google_photos_api


async def google_to_immich(album: Album, google_id: str, db: Database, gphoto: GooglePhotosApi) -> None:
    file, filename = await gphoto.download_photo(album.google_id, album.google_key, google_id)
    immich_id = await immich.upload_photo(file, filename)
    await immich.add_photo_to_album(album.immich_id, immich_id)
    await db.create_photo(album.id, google_id, immich_id, "to_immich")


async def immich_to_google(album: Album, immich_id: str, db: Database, gphoto: GooglePhotosApi) -> None:
    with TemporaryDirectory() as tmp_dir:
        file = await immich.download_photo(immich_id, tmp_dir)
        try:
            google_id = await gphoto.upload_photo_to_album(album.google_id, album.google_key, file)
            await db.create_photo(album.id, google_id, immich_id, "to_google")
        except GooglePhotosApiError as e:
            print("Error uploading to Google Photos:", e)
            print(f"immich_id: {immich_id}")


async def main() -> None:
    async with get_db() as db, get_google_photos_api() as gphoto:
        for url in ALBUMS_FILE.read_text().splitlines():
            album_id, key, title = await gphoto.load_album_meta(url)
            print(f"checking album '{title}'")
            album = await db.get_or_create_album(album_id, key)
            if album.immich_id is None:
                album.immich_id = await immich.create_album(title)

            photos = await db.get_photos(album.id)
            google_photo_ids = set(await gphoto.get_photo_ids(album.google_id, album.google_key))
            immich_photo_ids = set(await immich.get_photo_ids(album.immich_id))

            new_on_google_photos = google_photo_ids - {p.google_id for p in photos}
            if new_on_google_photos:
                print("uploading to Immich")
                for google_id in tqdm(new_on_google_photos):
                    await google_to_immich(album, google_id, db, gphoto)

            deleted_on_google_photos = {p.google_id for p in photos} - google_photo_ids
            if deleted_on_google_photos:
                print(f"{len(deleted_on_google_photos)} photos deleted on Google, not yet implemented")

            new_on_immich = immich_photo_ids - {p.immich_id for p in photos}
            if new_on_immich:
                print("uploading to Google Photos")
                for immich_id in tqdm(new_on_immich):
                    await immich_to_google(album, immich_id, db, gphoto)

            deleted_on_immich = {p.immich_id for p in photos} - immich_photo_ids
            if deleted_on_immich:
                print(f"{len(deleted_on_immich)} photos deleted on Immich, not yet implemented")


if __name__ == "__main__":
    asyncio.run(main())
