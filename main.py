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
        if not yandex_client:
            return JSONResponse({"error": "Сервис недоступен"}, status_code=503)
        
        # Получаем чарт
        chart = yandex_client.chart()
        if not chart or not chart.chart:
            return {"tracks": []}
        
        tracks_data = []
        for track_short in chart.chart.tracks[:20]:
            # Получаем полный трек по ID
            track_id = track_short.id
            album_id = track_short.albums[0].id if track_short.albums else None
            
            # Получаем полную информацию о треке
            if album_id:
                full_tracks = yandex_client.tracks([f"{track_id}:{album_id}"])
            else:
                full_tracks = yandex_client.tracks([track_id])
            
            if full_tracks and full_tracks[0]:
                full_track = full_tracks[0]
                track_info = {
                    "id": f"{full_track.id}_{full_track.albums[0].id}" if full_track.albums else str(full_track.id),
                    "title": full_track.title,
                    "artists": [artist.name for artist in full_track.artists],
                    "cover_uri": f"https://{full_track.cover_uri.replace('%%', '300x300')}" if full_track.cover_uri else None,
                    "album": full_track.albums[0].title if full_track.albums else "Неизвестный альбом"
                }
                tracks_data.append(track_info)
        
        return {"tracks": tracks_data}
        
    except Exception as e:
        print(f"Error getting popular tracks: {e}")
        # Возвращаем тестовые данные
        return {
            "tracks": [
                {
                    "id": "10994777_1193829",
                    "title": "Тестовый трек 1",
                    "artists": ["Исполнитель 1"],
                    "cover_uri": None,
                    "album": "Альбом 1"
                },
                {
                    "id": "40133452_5206873",
                    "title": "Тестовый трек 2", 
                    "artists": ["Исполнитель 2"],
                    "cover_uri": None,
                    "album": "Альбом 2"
                }
            ]
        }

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