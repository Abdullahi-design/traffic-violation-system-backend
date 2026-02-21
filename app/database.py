import ssl
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings

settings = get_settings()

connect_args = {}
if "tidbcloud.com" in settings.DATABASE_URL or "ssl=true" in settings.DATABASE_URL.lower():
    ssl_context = ssl.create_default_context()
    connect_args["ssl"] = ssl_context
    # Remove ssl=true from URL if present (handled via connect_args)
    db_url = settings.DATABASE_URL.replace("?ssl=true", "").replace("&ssl=true", "")
else:
    db_url = settings.DATABASE_URL

engine = create_async_engine(db_url, echo=False, pool_pre_ping=True, connect_args=connect_args)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
