import os
from dotenv import load_dotenv
from fastapi.templating import Jinja2Templates
from datetime import timedelta


load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")

DATABASE_URL = os.getenv("DATABASE_URL")

TWILIO_ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]

REDIS_URL = os.environ.get("REDIS_URL", "Not found")

templates = Jinja2Templates(directory="app/templates")


JWT_SECRET_KEY = os.getenv("SECRET_KEY")
JWT_ALGORITHM = "HS256"
JWT_EMAIL_EXPIRE = timedelta(hours=1) # Срок жизни токена подтверждения — 1 час


SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM = os.getenv("SMTP_FROM")
SMTP_TLS = os.getenv("SMTP_TLS")