from sqlalchemy.ext.asyncio import create_async_engine
from app.models import Base  # Импортируйте ваш базовый класс моделей
from app.config import DATABASE_URL  # Импортируйте URL вашей базы данных
import asyncio

# Создание асинхронного движка для подключения к базе данных
engine = create_async_engine(DATABASE_URL, echo=True)

# Асинхронная функция для полного сброса базы данных
async def reset_database():
    async with engine.begin() as conn:
        # Удаление всех таблиц, определенных в моделях
        await conn.run_sync(Base.metadata.drop_all)

# Запуск функции сброса базы данных
if __name__ == "__main__":
    # Добавляем подтверждение для безопасности
    confirmation = input("Вы уверены, что хотите удалить все таблицы? (y/n): ").lower()
    if confirmation == 'y':
        asyncio.run(reset_database())
        print("Все таблицы успешно удалены.")
    else:
        print("Операция отменена.")