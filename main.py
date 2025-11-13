import os
from fastapi import FastAPI, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import get_db, engine
from app import models
from app.dependencies import get_current_user
from app.routers import auth, users

# Создаем таблицы
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Crypto Portfolio")

# Подключаем статические файлы и шаблоны
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Подключаем роутеры
app.include_router(auth.router)
app.include_router(users.router)

BOT_USERNAME = os.getenv("BOT_USERNAME")

@app.get("/")
async def home(
    request: Request, 
    current_user: dict = Depends(get_current_user)
):
    user_data = current_user["telegram_data"] if current_user else None
    db_user = current_user["db_user"] if current_user else None
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user_data": user_data,
        "db_user": db_user,
        "bot_username": BOT_USERNAME
    })

@app.get("/profile")
async def profile(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(url="/")
    
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user_data": current_user["telegram_data"],
        "db_user": current_user["db_user"],
        "bot_username": BOT_USERNAME
    })