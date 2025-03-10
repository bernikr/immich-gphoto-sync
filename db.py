import asyncio
import typing
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Literal

from sqlalchemy import ForeignKey, String, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from config import DB_FILE
from google_photos import GoogleAlbumId, GoogleKey, GooglePhotoId
from immich import ImmichAlbumId, ImmichPhotoId


class Base(DeclarativeBase):
    type_annotation_map: typing.ClassVar = {
        GoogleAlbumId: String(),
        GoogleKey: String(),
        GooglePhotoId: String(),
        ImmichAlbumId: String(),
        ImmichPhotoId: String(),
    }


class Album(Base):
    __tablename__ = "albums"

    id: Mapped[int] = mapped_column(primary_key=True)
    google_id: Mapped[GoogleAlbumId] = mapped_column(unique=True)
    google_key: Mapped[GoogleKey]
    immich_id: Mapped[ImmichAlbumId]

    def __repr__(self) -> str:
        return f"<Album(google_id={self.google_id}, immich_id={self.immich_id})>"


Direction = Literal["to_immich", "to_google"]


class Photo(Base):
    __tablename__ = "photos"

    id: Mapped[int] = mapped_column(primary_key=True)
    album_id: Mapped[int] = mapped_column(ForeignKey("albums.id"))
    google_id: Mapped[GooglePhotoId]
    immich_id: Mapped[ImmichPhotoId]
    direction: Mapped[Direction]


class Database:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_album(self, google_id: GoogleAlbumId) -> Album | None:
        return (await self.session.execute(select(Album).filter(Album.google_id == google_id))).scalar_one_or_none()

    async def create_album(self, google_id: GoogleAlbumId, google_key: GoogleKey, immich_id: ImmichAlbumId) -> Album:
        album = Album(google_id=google_id, google_key=google_key, immich_id=immich_id)
        self.session.add(album)
        return album

    async def get_photos(self, album: Album) -> list[Photo]:
        return list((await self.session.execute(select(Photo).filter(Photo.album_id == album.id))).scalars().all())

    async def create_photo(
        self,
        album_id: int,
        google_id: GooglePhotoId,
        immich_id: ImmichPhotoId,
        direction: Direction,
    ) -> Photo:
        photo = Photo(album_id=album_id, google_id=google_id, immich_id=immich_id, direction=direction)
        self.session.add(photo)
        return photo


@asynccontextmanager
async def get_db() -> AsyncGenerator[Database]:
    engine = create_async_engine(f"sqlite+aiosqlite:///{DB_FILE}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        async with AsyncSession(engine) as session, session.begin():
            try:
                yield Database(session)
            finally:
                await session.commit()
    finally:
        await engine.dispose()


async def main() -> None:
    async with get_db():
        pass


if __name__ == "__main__":
    asyncio.run(main())
