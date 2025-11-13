import os
from fastapi import FastAPI, Request, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from yandex_music import Client

from app.database import get_db, engine
from app import models
from app.dependencies import get_current_user
from app.routers import auth, users, music

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Music App")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(music.router)

# Яндекс.Музыка клиент
YANDEX_MUSIC_TOKEN = "y0__xCq06KNAxje-AYgtsC_khWI-0_xZL5Ctrii1vxK_bVg6w2MHA"
try:
    yandex_client = Client(YANDEX_MUSIC_TOKEN).init()
    print("✅ Яндекс.Музыка клиент успешно инициализирован")
except Exception as e:
    print(f"❌ Ошибка инициализации Яндекс.Музыка: {e}")
    yandex_client = None

BOT_USERNAME = os.getenv("BOT_USERNAME")

@app.get("/")
async def home(request: Request, current_user: dict = Depends(get_current_user)):
    user_data = current_user["telegram_data"] if current_user else None
    db_user = current_user["db_user"] if current_user else None
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user_data": user_data,
        "db_user": db_user,
        "bot_username": BOT_USERNAME
    })

# В main.py заменяем эндпоинт /api/popular
@app.get("/api/popular")
async def get_popular_tracks():
    try:
        # Просто возвращаем тестовые данные
        tracks_data = [
            {
                "id": "10994777_1193829",
                "title": "Тестовый трек 1",
                "artists": ["Kizaru"],
                "cover_uri": None,
                "album": "Тестовый альбом"
            },
            {
                "id": "40133452_5206873",
                "title": "Тестовый трек 2", 
                "artists": ["Miyagi", "Эндшпиль"],
                "cover_uri": None,
                "album": "Другой альбом"
            },
            {
                "id": "51385674_7163467",
                "title": "Тестовый трек 3",
                "artists": ["Макс Корж"],
                "cover_uri": None, 
                "album": "Третий альбом"
            }
        ]
        
        return {"tracks": tracks_data}
        
    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/profile")
async def profile(request: Request, current_user: dict = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/")
    
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user_data": current_user["telegram_data"],
        "db_user": current_user["db_user"],
        "bot_username": BOT_USERNAME
    })