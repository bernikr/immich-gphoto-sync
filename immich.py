from http import HTTPStatus

import aiohttp

from config import IMMICH_API_KEY, IMMICH_URL


class APIError(Exception):
    pass


async def _call(method: str, endpoint: str, data: dict | None = None) -> dict:
    async with (
        aiohttp.ClientSession() as session,
        session.request(
            method,
            IMMICH_URL + "/api/" + endpoint,
            headers={"x-api-key": IMMICH_API_KEY},
            json=data if method != "GET" else None,
            params=data if method == "GET" else None,
        ) as res,
    ):
        status = HTTPStatus(res.status)
        if not status.is_success:
            msg = f"API call failed: {status} {res.reason}"
            raise APIError(msg)
        if status == HTTPStatus.NO_CONTENT:
            return {}
        return await res.json()


async def create_album(title: str) -> str:
    data = await _call("POST", "albums", data={"albumName": title})
    return data["id"]
