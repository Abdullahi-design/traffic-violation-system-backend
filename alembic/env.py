from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, create_engine
from alembic import context
import ssl
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import Base
from app.models import User, ViolationType, Violation, Payment, Notification

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url():
    """Get database URL from env or alembic.ini, converting async to sync driver."""
    url = os.environ.get("DATABASE_URL", config.get_main_option("sqlalchemy.url"))
    # Alembic needs a sync driver
    return url.replace("mysql+aiomysql://", "mysql+pymysql://")


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "format"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    url = get_url()
    connect_args = {}
    if "tidbcloud.com" in url:
        ssl_context = ssl.create_default_context()
        connect_args["ssl"] = ssl_context
    # Remove ssl=true from URL if present
    url = url.replace("?ssl=true", "").replace("&ssl=true", "")

    connectable = create_engine(url, poolclass=pool.NullPool, connect_args=connect_args)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
