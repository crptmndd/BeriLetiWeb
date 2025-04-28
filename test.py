import redis
import bcrypt

try:
    # Подключение к Redis
    r = redis.Redis(
        host='127.0.0.1',
        port=6379,
        decode_responses=True
    )

    # Проверка подключения
    print("Проверка подключения:", r.ping())  # Должно вывести True

    # Хеширование и сохранение пароля
    password = "user_password"
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    # Преобразуем хеш в строку перед сохранением в Redis
    r.set('user:password', hashed.decode('utf-8'))

    # Проверка пароля
    stored_hash = r.get('user:password')
    # Преобразуем строку обратно в байты перед проверкой
    if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
        print("Пароль верный")
    else:
        print("Пароль неверный")

except redis.ConnectionError as e:
    print(f"Ошибка подключения к Redis: {e}")
except redis.AuthenticationError as e:
    print(f"Ошибка аутентификации: {e}")
except Exception as e:
    print(f"Неизвестная ошибка: {e}")