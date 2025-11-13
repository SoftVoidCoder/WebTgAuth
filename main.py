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
            # Получаем ID альбома из track_short
            album_id = None
            if hasattr(track_short, 'albums') and track_short.albums:
                album_id = track_short.albums[0].id
            elif hasattr(track_short, 'album') and track_short.album:
                album_id = track_short.album.id
            
            track_id = f"{track_short.id}_{album_id}" if album_id else str(track_short.id)
            
            # Получаем название альбома
            album_title = "Неизвестный альбом"
            if hasattr(track_short, 'albums') and track_short.albums:
                album_title = track_short.albums[0].title
            elif hasattr(track_short, 'album') and track_short.album:
                album_title = track_short.album.title
            
            track_info = {
                "id": track_id,
                "title": track_short.title,
                "artists": [artist.name for artist in track_short.artists],
                "cover_uri": f"https://{track_short.cover_uri.replace('%%', '300x300')}" if track_short.cover_uri else None,
                "album": album_title
            }
            tracks_data.append(track_info)
        
        return {"tracks": tracks_data}
        
    except Exception as e:
        print(f"Error getting popular tracks: {e}")
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