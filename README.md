# Google Photos Shared Albums to Immich Sync

The goal of this project is to integrate shared Albums from Google Photos into Immich.
If your friends are still on Google Photos, you can use this tool to acccess their shared albums and contribute to them directly from Immich.

This project takes a list of share google photo albums, and creates corresponding albums in Immich that are kept in sync.

**Roadmap**:
- [x] Create albums in Immich
- [x] Upload photos from Google Photos to Immich
- [ ] Upload photos from Immich to Google Photos
- [ ] Delete photos in Immich when deleted on Google Photos
- [ ] Delete photos in Google Photos when deleted on Immich

## Setup

### Install
The project uses uv to manage dependencies

```bash
uv sync
uv run playwright install chromium
```

### Configure
create a .env file in the root directory of the project with the following content:

```
IMMICH_URL=<your immich url without trailing slash>
IMMICH_API_KEY=<your immich api key>
```

create a file called `data/albums.txt` with one link to a shared google photos album per line.

Example:
```
https://photos.google.com/share/xxxx?key=yyyy
https://photos.app.goo.gl/xxxx
```

### Run
```bash
uv run main.py
```