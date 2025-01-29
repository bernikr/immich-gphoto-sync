import datetime
from http import HTTPStatus
from pathlib import Path
from typing import Literal

import aiofiles
import aiohttp

from config import IMMICH_API_KEY, IMMICH_URL


class APIError(Exception):
    pass


async def _call(
    method: Literal["GET", "POST", "PUT", "DELETE"],
    endpoint: str,
    data: dict | aiohttp.FormData | None = None,
) -> dict:
    async with (
        aiohttp.ClientSession() as session,
        session.request(
            method,
            IMMICH_URL + "/api/" + endpoint,
            headers={"Accept": "application/json", "x-api-key": IMMICH_API_KEY},
            json=data if method != "GET" and isinstance(data, dict) else None,
            params=data if method == "GET" and isinstance(data, dict) else None,
            data=data if isinstance(data, aiohttp.FormData) else None,
        ) as res,
    ):
        try:
            status = HTTPStatus(res.status)
        except ValueError:
            status = HTTPStatus.BAD_REQUEST
        if not status.is_success:
            print(await res.text())
            msg = f"API call failed: {status} {res.reason}"
            raise APIError(msg)
        if status == HTTPStatus.NO_CONTENT:
            return {}
        return await res.json()


async def create_album(title: str) -> str:
    res = await _call("POST", "albums", data={"albumName": title})
    return res["id"]


async def get_photo_ids(album_id: str) -> list[str]:
    res = await _call("GET", f"albums/{album_id}")
    return [p["id"] for p in res["assets"]]


async def upload_photo(file: Path, filename: str) -> str:
    stats = file.stat()
    data = {
        "deviceAssetId": f"{file}-{stats.st_mtime}",
        "deviceId": "python",
        "fileCreatedAt": datetime.datetime.fromtimestamp(stats.st_mtime, datetime.UTC).isoformat(),
        "fileModifiedAt": datetime.datetime.fromtimestamp(stats.st_mtime, datetime.UTC).isoformat(),
        "isFavorite": "false",
    }
    data = aiohttp.FormData(data)
    data.add_field("assetData", await aiofiles.open(file, "rb"), filename=filename)
    res = await _call("POST", "assets", data=data)
    return res["id"]


async def add_photo_to_album(album_id: str, photo_id: str) -> None:
    await _call("PUT", f"albums/{album_id}/assets", data={"ids": [photo_id]})


async def download_photo(photo_id: str, folder: Path | str) -> Path:
    filename = (await _call("GET", f"assets/{photo_id}"))["originalFileName"]
    file = Path(folder) / filename
    async with (
        aiohttp.ClientSession() as session,
        session.get(
            IMMICH_URL + f"/api/assets/{photo_id}/original",
            headers={"Accept": "application/octet-stream", "x-api-key": IMMICH_API_KEY},
        ) as res,
    ):
        with file.open("wb") as f:
            while True:
                chunk = await res.content.readany()
                if not chunk:
                    break
                f.write(chunk)
    return file
