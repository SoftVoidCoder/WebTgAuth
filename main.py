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
        
        # Получаем популярные треки через новые чарты
        chart = yandex_client.chart('world')
        if not chart:
            return {"tracks": []}
        
        tracks_data = []
        for track in chart.chart.tracks[:20]:
            # Безопасно получаем все данные
            track_id = str(track.id)
            
            # Артисты
            artists = []
            if hasattr(track, 'artists') and track.artists:
                for artist in track.artists:
                    if hasattr(artist, 'name'):
                        artists.append(artist.name)
            
            # Альбом
            album_title = "Неизвестный альбом"
            album_id = None
            
            if hasattr(track, 'album') and track.album:
                if hasattr(track.album, 'title'):
                    album_title = track.album.title
                if hasattr(track.album, 'id'):
                    album_id = track.album.id
            elif hasattr(track, 'albums') and track.albums and len(track.albums) > 0:
                album = track.albums[0]
                if hasattr(album, 'title'):
                    album_title = album.title
                if hasattr(album, 'id'):
                    album_id = album.id
            
            # ID трека
            track_full_id = f"{track_id}_{album_id}" if album_id else track_id
            
            # Обложка
            cover_uri = None
            if hasattr(track, 'cover_uri') and track.cover_uri:
                cover_uri = f"https://{track.cover_uri.replace('%%', '400x400')}"
            elif hasattr(track, 'og_image') and track.og_image:
                cover_uri = f"https://{track.og_image.replace('%%', '400x400')}"
            
            track_info = {
                "id": track_full_id,
                "title": track.title,
                "artists": artists,
                "cover_uri": cover_uri,
                "album": album_title
            }
            tracks_data.append(track_info)
        
        return {"tracks": tracks_data}
        
    except Exception as e:
        print(f"Error getting popular tracks: {e}")
        # Возвращаем тестовые данные в случае ошибки
        return {
            "tracks": [
                {
                    "id": "10994777_1193829",
                    "title": "Трек 1",
                    "artists": ["Исполнитель 1"],
                    "cover_uri": None,
                    "album": "Альбом 1"
                },
                {
                    "id": "40133452_5206873",
                    "title": "Трек 2", 
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