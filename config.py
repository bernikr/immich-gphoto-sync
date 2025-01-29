import os
from pathlib import Path

IMMICH_URL = os.environ["IMMICH_URL"]
IMMICH_API_KEY = os.environ["IMMICH_API_KEY"]
DATA_FOLDER = Path("./data")
ALBUMS_FILE = DATA_FOLDER / "albums.txt"
USER_DATA_FOLDER = DATA_FOLDER / "usrdata"
DB_FILE = DATA_FOLDER / "db.sqlite"
HEADLESS = bool(os.environ.get("HEADLESS", "true").lower() == "true")
