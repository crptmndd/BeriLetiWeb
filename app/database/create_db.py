from sqlalchemy.ext.asyncio import create_async_engine
from app.models import Base 
from app.config import DATABASE_URL


engine = create_async_engine(DATABASE_URL, echo=True)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


import asyncio
asyncio.run(init_db())