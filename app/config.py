import os
from dotenv import load_dotenv
from fastapi.templating import Jinja2Templates


load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
# CSRF_KEY = os.getenv("CSRF_KEY")

# Инициализация templates
templates = Jinja2Templates(directory="app/templates")