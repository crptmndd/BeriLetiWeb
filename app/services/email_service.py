# app/services/email_service.py
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException
from app.config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EMAIL_EXPIRE
import aiosmtplib
from email.message import EmailMessage
from app.config import (
    SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD,
    SMTP_FROM, SMTP_TLS,
)
from email.utils import formataddr

class EmailService:
    @staticmethod
    def create_confirmation_token(user_id: str, email: str) -> str:
        now = datetime.now()
        payload = {
            "sub": user_id,
            "email": email,
            "iat": now,
            "exp": now + JWT_EMAIL_EXPIRE
        }
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return token

    @staticmethod
    def verify_confirmation_token(token: str) -> dict:
        try:
            data = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return data
        except jwt.ExpiredSignatureError:
            raise HTTPException(400, "Ссылка устарела")
        except jwt.PyJWTError:
            raise HTTPException(400, "Неверный токен подтверждения")
    
    @staticmethod
    async def send_confirmation_email(to_email: str, token: str):
        """
        Отправляет пользователю письмо с ссылкой для подтверждения e-mail.
        Ссылка формируется так: http://127.0.0.1:8002/profile/confirm-email?token={token}
        """
        # 1. Собираем письмо
        msg = EmailMessage()
        site_name = "БериЛети"
        msg["From"] = formataddr((site_name, SMTP_FROM))
        msg["To"] = to_email
        msg["Subject"] = "Подтвердите ваш e-mail"
        
        print(SMTP_FROM)
        
        confirmation_link = f"http://127.0.0.1:8002/profile/confirm-email?token={token}"
        body = f"""\
Здравствуйте!

Чтобы подтвердить ваш адрес электронной почты, перейдите по ссылке:

{confirmation_link}

Если вы не отправляли эту заявку, просто проигнорируйте это письмо.

С уважением,
Команда BeriLeti
"""
        msg.set_content(body)

        # 2. Отправляем через SMTP
        try:
            await aiosmtplib.send(
                msg,
                hostname=SMTP_HOST,
                port=SMTP_PORT,
                start_tls=SMTP_TLS,
                username=SMTP_USERNAME,
                password=SMTP_PASSWORD,
            )
        except aiosmtplib.errors.SMTPRecipientsRefused:
            raise HTTPException(400, f"Адрес {to_email} отклонил получение почты")
        except aiosmtplib.errors.SMTPAuthenticationError:
            raise HTTPException(500, "Ошибка аутентификации SMTP")
        except Exception as e:
            # Логируйте подробности e в реальном приложении
            raise HTTPException(500, "Не удалось отправить письмо для подтверждения") from e
