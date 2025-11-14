import os
from fastapi import FastAPI, Request, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from yandex_music import Client
from app import crud

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
        
        # Современные русские треки 2016-2025
        search_queries = [
            "русский рэп 2024", "русская музыка 2024", "новинки рэпа 2024",
            "Miyagi Эндшпиль", "Kizaru", "Макс Корж", "Scriptonite",
            "ЛСП", "FACE", "MORGENSHTERN", "Big Baby Tape",
            "популярные треки 2024", "хиты 2024", "топ чарт 2024",
            "русская поп музыка 2024", "новинки музыки 2024",
            "Ramil'", "Markul", "ANIKV", "Три дня дождя",
            "A.V.G", "Би-2", "Земфира", "Нервы"
        ]
        
        import random
        random_query = random.choice(search_queries)
        
        print(f"Searching for: {random_query}")
        search_result = yandex_client.search(random_query, type_="track")
        
        if not search_result or not search_result.tracks:
            return {"tracks": []}
        
        # Берем случайные треки из результатов
        all_tracks = search_result.tracks.results
        random.shuffle(all_tracks)
        
        tracks_data = []
        for track in all_tracks[:15]:
            # Безопасно получаем данные
            album_id = None
            if hasattr(track, 'albums') and track.albums and len(track.albums) > 0:
                album_id = track.albums[0].id
            elif hasattr(track, 'album') and track.album:
                album_id = track.album.id
            
            track_id = f"{track.id}_{album_id}" if album_id else str(track.id)
            
            album_title = "Неизвестный альбом"
            if hasattr(track, 'albums') and track.albums and len(track.albums) > 0:
                album_title = track.albums[0].title
            elif hasattr(track, 'album') and track.album:
                album_title = track.album.title
            
            # Артисты
            artists = []
            if hasattr(track, 'artists') and track.artists:
                for artist in track.artists:
                    if hasattr(artist, 'name'):
                        artists.append(artist.name)
            
            # Обложка
            cover_uri = None
            if hasattr(track, 'cover_uri') and track.cover_uri:
                cover_uri = f"https://{track.cover_uri.replace('%%', '300x300')}"
            
            track_info = {
                "id": track_id,
                "title": track.title,
                "artists": artists,
                "cover_uri": cover_uri,
                "album": album_title
            }
            tracks_data.append(track_info)
        
        print(f"Found {len(tracks_data)} tracks")
        return {"tracks": tracks_data}
        
    except Exception as e:
        print(f"Error getting popular tracks: {e}")
        return {"tracks": []}
    
    
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


@app.post("/api/like/{track_id}")
async def like_track(
    track_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    if not current_user:
        return JSONResponse({"error": "Не авторизован"}, status_code=401)
    
    db = next(get_db())
    user_id = current_user["db_user"].id
    
    try:
        # Получаем данные трека из тела запроса
        track_data = await request.json()
        
        liked_track = crud.add_liked_track(db, user_id, track_data)
        return {"status": "liked", "track_id": track_id}
        
    except Exception as e:
        print(f"Error liking track: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/liked-tracks")
async def get_liked_tracks(current_user: dict = Depends(get_current_user)):
    if not current_user:
        return JSONResponse({"error": "Не авторизован"}, status_code=401)
    
    db = next(get_db())
    user_id = current_user["db_user"].id
    
    try:
        liked_tracks = crud.get_liked_tracks(db, user_id)
        tracks_data = []
        for track in liked_tracks:
            tracks_data.append({
                "id": track.track_id,
                "title": track.track_title,
                "artists": track.track_artists.split(',') if track.track_artists else [],
                "cover_uri": track.track_cover_uri,
                "album": track.track_album
            })
        
        return {"tracks": tracks_data}
        
    except Exception as e:
        print(f"Error getting liked tracks: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.delete("/api/unlike/{track_id}")
async def unlike_track(
    track_id: str,
    current_user: dict = Depends(get_current_user)
):
    if not current_user:
        return JSONResponse({"error": "Не авторизован"}, status_code=401)
    
    db = next(get_db())
    user_id = current_user["db_user"].id
    
    try:
        success = crud.remove_liked_track(db, user_id, track_id)
        return {"status": "unliked", "track_id": track_id}
        
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/liked-tracks")
async def get_liked_tracks(current_user: dict = Depends(get_current_user)):
    if not current_user:
        return JSONResponse({"error": "Не авторизован"}, status_code=401)
    
    db = next(get_db())
    user_id = current_user["db_user"].id
    
    try:
        liked_tracks = crud.get_liked_tracks(db, user_id)
        tracks_data = []
        for track in liked_tracks:
            tracks_data.append({
                "id": track.track_id,
                "title": track.track_title,
                "artists": track.track_artists.split(','),
                "cover_uri": track.track_cover_uri,
                "album": track.track_album
            })
        
        return {"tracks": tracks_data}
        
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    

@app.get("/api/is-liked/{track_id}")
async def is_track_liked(
    track_id: str,
    current_user: dict = Depends(get_current_user)
):
    if not current_user:
        return JSONResponse({"error": "Не авторизован"}, status_code=401)
    
    db = next(get_db())
    user_id = current_user["db_user"].id
    
    try:
        liked = crud.is_track_liked(db, user_id, track_id)
        return {"liked": liked}
        
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)