from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context
from app.models import Base  # Replace with the import path to your SQLAlchemy Base class
import os
from app.config import DATABASE_URL


# Create an asynchronous engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Async function to run migrations
async def run_migrations_online():
    async with engine.connect() as connection:
        await connection.run_sync(lambda sync_conn: context.configure(
            connection=sync_conn,
            target_metadata=Base.metadata,
            render_as_batch=True
        ))
        await connection.run_sync(lambda sync_conn: context.run_migrations())

# Run the migrations
if context.is_offline_mode():
    # Handle offline mode (if needed, define run_migrations_offline separately)
    raise NotImplementedError("Offline mode not implemented here.")
else:
    import asyncio
    asyncio.run(run_migrations_online())