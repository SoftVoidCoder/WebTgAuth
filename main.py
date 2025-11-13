import os
from fastapi import FastAPI, Request, Depends, Query
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from yandex_music import Client

from app.database import get_db, engine
from app import models
from app.dependencies import get_current_user
from app.routers import auth, users

# Создаем таблицы в БД при старте
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Crypto Portfolio")

# Раздача статических файлов (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Яндекс.Музыка клиент
YANDEX_MUSIC_TOKEN = "y0__xCq06KNAxje-AYgtsC_khWI-0_xZL5Ctrii1vxK_bVg6w2MHA"
try:
    yandex_client = Client(YANDEX_MUSIC_TOKEN).init()
    print("✅ Яндекс.Музыка клиент успешно инициализирован")
except Exception as e:
    print(f"❌ Ошибка инициализации Яндекс.Музыка: {e}")
    yandex_client = None

# Подключаем модули
app.include_router(auth.router)   # /auth/telegram, /auth/logout
app.include_router(users.router)  # /users/{id}

BOT_USERNAME = os.getenv("BOT_USERNAME")

# Главная страница С МУЗЫКОЙ
@app.get("/")
async def home(
    request: Request, 
    current_user: dict = Depends(get_current_user),
    query: str = Query(None)
):
    user_data = current_user["telegram_data"] if current_user else None
    db_user = current_user["db_user"] if current_user else None
    
    tracks = []
    popular_tracks = []
    
    try:
        if yandex_client:
            # Если есть поисковый запрос
            if query and query.strip():
                search_result = yandex_client.search(query, type_="track")
                if search_result and search_result.tracks:
                    tracks = search_result.tracks.results[:20]
            
            # Если нет поиска - показываем популярные треки
            if not query and not tracks:
                chart = yandex_client.chart()
                if chart and chart.chart:
                    popular_tracks = chart.chart.tracks[:15]
                    
    except Exception as e:
        print(f"Music error: {e}")
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user_data": user_data,
        "db_user": db_user,
        "bot_username": BOT_USERNAME,
        "tracks": tracks,
        "popular_tracks": popular_tracks,
        "search_query": query
    })

# API для получения трека
@app.get("/track/{track_id}")
async def get_track_url(track_id: str, current_user: dict = Depends(get_current_user)):
    """API для получения URL трека"""
    try:
        if not yandex_client:
            return {"error": "Сервис недоступен"}
        
        parts = track_id.split('_')
        if len(parts) != 2:
            return {"error": "Неверный формат ID трека"}
        
        track_id_num = parts[0]
        album_id = parts[1]
        
        tracks = yandex_client.tracks([f"{track_id_num}:{album_id}"])
        if not tracks:
            return {"error": "Трек не найден"}
        
        track = tracks[0]
        download_info = track.get_download_info()
        
        if download_info:
            best_download = None
            for info in download_info:
                if info.codec == 'mp3' and info.bitrate_in_kbps >= 192:
                    best_download = info
                    break
            
            if not best_download and download_info:
                best_download = download_info[0]
            
            if best_download:
                download_url = best_download.get_direct_link()
                return {
                    "download_url": download_url,
                    "title": track.title,
                    "artists": [artist.name for artist in track.artists]
                }
        
        return {"error": "Нет доступных ссылок"}
            
    except Exception as e:
        return {"error": str(e)}

# Страница профиля
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