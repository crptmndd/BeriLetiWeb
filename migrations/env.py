# migrations/env.py
from logging.config import fileConfig
from sqlalchemy import pool, create_engine
from sqlalchemy.engine import Connection
from alembic import context

# 1) Импортируем ваше Base
from app.models import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
fileConfig(config.config_file_name)

# Получаем URL из alembic.ini
db_url = config.get_main_option("sqlalchemy.url")

def run_migrations_online():
    # 2) Синхронный движок для миграций
    connectable = create_engine(db_url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        # 3) Передаём Base.metadata в context
        context.configure(
            connection=connection,
            target_metadata=Base.metadata,
            compare_type=True,
            render_as_batch=True,  # на случай SQLite; можно убрать, если не нужно
        )
        with context.begin_transaction():
            context.run_migrations()

def run_migrations_offline():
    context.configure(
        url=db_url,
        target_metadata=Base.metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
