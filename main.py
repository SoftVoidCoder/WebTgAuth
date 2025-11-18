import os
from fastapi import FastAPI, Request, Depends, Query
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from yandex_music import Client
import random
from app import crud

from app.database import get_db, engine
from app import models
from app.dependencies import get_current_user
from app.routers import auth, users, music

# Получаем токен из переменных окружения
YANDEX_MUSIC_TOKEN = os.getenv("YANDEX_MUSIC_TOKEN")

if not YANDEX_MUSIC_TOKEN:
    raise ValueError("❌ YANDEX_MUSIC_TOKEN не установлен в переменных окружения")

# СОЗДАЕМ ТАБЛИЦЫ БЕЗ УДАЛЕНИЯ ДАННЫХ
print("🔄 Создаем таблицы БД...")
models.Base.metadata.create_all(bind=engine)

# Проверяем есть ли таблица liked_tracks
from sqlalchemy import inspect
inspector = inspect(engine)
if 'liked_tracks' not in inspector.get_table_names():
    print("✅ Создаем таблицу liked_tracks...")
    models.LikedTrack.__table__.create(engine)
else:
    print("✅ Таблица liked_tracks уже существует")

print("✅ Все таблицы БД готовы")

app = FastAPI(title="Music App")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(music.router)

# Яндекс.Музыка клиент
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


# API для получения популярных треков
@app.get("/api/popular")
async def get_popular_tracks():
    try:
        if not yandex_client:
            return JSONResponse({"error": "Сервис недоступен"}, status_code=503)
        
        # ТОЛЬКО русский рэп, фонк и похожие стили
        search_queries = [
            "русский рэп 2024", "новинки рэпа 2024", "русский фонк 2024",
            "Miyagi Эндшпиль", "Kizaru", "Макс Корж", "Scriptonite",
            "ЛСП", "FACE", "MORGENSHTERN", "Big Baby Tape",
            "Markul", "ANIKV", "A.V.G", "Ramil'",
            "Три дня дождя", "Boulevard Depo", "PHARAOH", "OG Buda",
            "Mayot", "MellowBite", "SODA LUV", "Yanix",
            "GONE.Fludd", "Thomas Mraz", "HENSY", "MACAN",
            "163ONMYNECK", "SEEMEE", "T-Fest", "M'Dee"
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
        
        print(f"🔵 LIKE TRACK REQUEST - User: {user_id}, Track ID: {track_id}")
        print(f"🔵 Track data received: {track_data}")
        
        # Убедимся что ID трека правильный
        if track_data.get('id') != track_id:
            print(f"🟡 Fixing track ID: {track_data.get('id')} -> {track_id}")
            track_data['id'] = track_id
        
        # Обрабатываем artists
        artists = track_data.get('artists', [])
        if isinstance(artists, list):
            artists_str = ','.join(artists)
        elif isinstance(artists, str):
            artists_str = artists
        else:
            artists_str = str(artists)
        
        print(f"🟡 Processed artists: {artists_str}")
        
        liked_track = crud.add_liked_track(db, user_id, track_data)
        
        if liked_track:
            print(f"✅ Track liked successfully! DB ID: {liked_track.id}")
            return {"status": "liked", "track_id": track_id}
        else:
            print("❌ Track already liked or error")
            return {"status": "already_liked", "track_id": track_id}
        
    except Exception as e:
        print(f"❌ Error liking track: {e}")
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
            # ФИКС: Преобразуем строку artists обратно в массив
            artists_array = []
            if track.track_artists:
                if ',' in track.track_artists:
                    artists_array = track.track_artists.split(',')
                else:
                    artists_array = [track.track_artists]
            
            tracks_data.append({
                "id": track.track_id,
                "title": track.track_title,
                "artists": artists_array,  # Теперь всегда массив!
                "cover_uri": track.track_cover_uri,
                "album": track.track_album
            })
        
        print(f"🟡 Returning {len(tracks_data)} liked tracks for user {user_id}")
        return {"tracks": tracks_data}
        
    except Exception as e:
        print(f"❌ Error getting liked tracks: {e}")
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
        print(f"🔵 UNLIKE TRACK - User: {user_id}, Track ID: {track_id}")
        success = crud.remove_liked_track(db, user_id, track_id)
        
        if success:
            print(f"✅ Track unliked successfully!")
            return {"status": "unliked", "track_id": track_id}
        else:
            print("❌ Track not found in likes")
            return {"status": "not_found", "track_id": track_id}
        
    except Exception as e:
        print(f"❌ Error unliking track: {e}")
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
        print(f"🟡 Check like - User: {user_id}, Track: {track_id}, Liked: {liked}")
        return {"liked": liked}
        
    except Exception as e:
        print(f"❌ Error checking like: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

# ДЕБАГ ЭНДПОИНТ
@app.get("/debug/liked-tracks")
async def debug_liked_tracks(current_user: dict = Depends(get_current_user)):
    if not current_user:
        return {"error": "Не авторизован"}
    
    db = next(get_db())
    user_id = current_user["db_user"].id
    
    # Получаем все лайкнутые треки напрямую
    liked_tracks = db.query(models.LikedTrack).filter(
        models.LikedTrack.user_id == user_id
    ).all()
    
    result = {
        "user_id": user_id,
        "total_liked": len(liked_tracks),
        "tracks": [
            {
                "id": track.id,
                "track_id": track.track_id,
                "title": track.track_title,
                "artists": track.track_artists,
                "cover_uri": track.track_cover_uri,
                "album": track.track_album,
                "liked_at": track.liked_at.isoformat() if track.liked_at else None
            } for track in liked_tracks
        ]
    }
    
    print(f"🔍 DEBUG LIKED TRACKS - User: {user_id}, Total: {len(liked_tracks)}")
    return result

# ДЕБАГ ВСЕХ ПОЛЬЗОВАТЕЛЕЙ
@app.get("/debug/users")
async def debug_users():
    db = next(get_db())
    users = db.query(models.User).all()
    
    return {
        "total_users": len(users),
        "users": [
            {
                "id": user.id,
                "telegram_id": user.telegram_id,
                "first_name": user.first_name,
                "username": user.username
            } for user in users
        ]
    }


@app.get("/api/similar")
async def get_similar_tracks(query: str = Query(...)):
    try:
        if not yandex_client:
            return {"tracks": []}
        
        print(f"🔍 Searching similar tracks for: {query}")
        search_result = yandex_client.search(query, type_="track")
        
        if not search_result or not search_result.tracks:
            return {"tracks": []}
        
        # Берем треки из результатов поиска
        all_tracks = search_result.tracks.results
        random.shuffle(all_tracks)
        
        tracks_data = []
        for track in all_tracks[:20]:  # Берем больше треков для разнообразия
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
        
        print(f"✅ Found {len(tracks_data)} similar tracks for '{query}'")
        return {"tracks": tracks_data}
        
    except Exception as e:
        print(f"❌ Error getting similar tracks: {e}")
        return {"tracks": []}