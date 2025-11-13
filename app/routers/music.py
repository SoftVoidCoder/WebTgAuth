from fastapi import APIRouter, Request, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from yandex_music import Client
import os
from app.dependencies import get_current_user

router = APIRouter(prefix="/music", tags=["music"])
templates = Jinja2Templates(directory="templates")

# Токен Яндекс.Музыки
YANDEX_MUSIC_TOKEN = "y0__xCq06KNAxje-AYgtsC_khWI-0_xZL5Ctrii1vxK_bVg6w2MHA"

# Инициализация клиента с токеном
try:
    yandex_client = Client(YANDEX_MUSIC_TOKEN).init()
    print("✅ Яндекс.Музыка клиент успешно инициализирован")
except Exception as e:
    print(f"❌ Ошибка инициализации Яндекс.Музыка: {e}")
    yandex_client = None

@router.get("/", response_class=HTMLResponse)
async def music_home(
    request: Request, 
    current_user: dict = Depends(get_current_user),
    query: str = Query(None),
    page: int = Query(1, ge=1)
):
    user_data = current_user["telegram_data"] if current_user else None
    db_user = current_user["db_user"] if current_user else None
    
    tracks = []
    popular_tracks = []
    search_info = None
    error = None
    
    try:
        if not yandex_client:
            raise Exception("Сервис музыки временно недоступен")
        
        # Если есть поисковый запрос
        if query and query.strip():
            search_result = yandex_client.search(query, type_="track", page=page-1)
            if search_result and search_result.tracks:
                tracks = search_result.tracks.results[:50]
                search_info = {
                    "query": query,
                    "total": search_result.tracks.total,
                    "page": page
                }
        
        # Если нет поиска - показываем популярные треки
        if not query and not tracks:
            chart = yandex_client.chart()
            if chart and chart.chart:
                popular_tracks = chart.chart.tracks[:30]
            
    except Exception as e:
        error = f"Ошибка загрузки музыки: {str(e)}"
        print(f"Music error: {e}")
    
    return templates.TemplateResponse("music.html", {
        "request": request,
        "user_data": user_data,
        "db_user": db_user,
        "tracks": tracks,
        "popular_tracks": popular_tracks,
        "search_info": search_info,
        "error": error,
        "current_page": page
    })

@router.get("/search")
async def search_music(
    query: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    current_user: dict = Depends(get_current_user)
):
    """API для поиска музыки"""
    try:
        if not yandex_client:
            return JSONResponse({"error": "Сервис недоступен"}, status_code=503)
        
        search_result = yandex_client.search(query, type_="track", page=page-1)
        
        if not search_result or not search_result.tracks:
            return {"tracks": [], "total": 0, "page": page}
        
        tracks_data = []
        for track in search_result.tracks.results[:30]:
            track_info = {
                "id": f"{track.id}_{track.albums[0].id}" if track.albums else str(track.id),
                "title": track.title,
                "artists": [artist.name for artist in track.artists],
                "duration": track.duration_ms,
                "cover_uri": f"https://{track.cover_uri.replace('%%', '400x400')}" if track.cover_uri else None,
                "album": track.albums[0].title if track.albums else "Неизвестный альбом"
            }
            tracks_data.append(track_info)
        
        return {
            "tracks": tracks_data,
            "total": search_result.tracks.total,
            "page": page,
            "query": query
        }
        
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@router.get("/popular")
async def get_popular_tracks(current_user: dict = Depends(get_current_user)):
    """API для получения популярных треков"""
    try:
        if not yandex_client:
            return JSONResponse({"error": "Сервис недоступен"}, status_code=503)
        
        chart = yandex_client.chart()
        if not chart or not chart.chart:
            return {"tracks": []}
        
        tracks_data = []
        for track in chart.chart.tracks[:30]:
            track_info = {
                "id": f"{track.id}_{track.albums[0].id}" if track.albums else str(track.id),
                "title": track.title,
                "artists": [artist.name for artist in track.artists],
                "duration": track.duration_ms,
                "cover_uri": f"https://{track.cover_uri.replace('%%', '400x400')}" if track.cover_uri else None,
                "album": track.albums[0].title if track.albums else "Неизвестный альбом"
            }
            tracks_data.append(track_info)
        
        return {"tracks": tracks_data}
        
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@router.get("/track/{track_id}")
async def get_track_url(track_id: str, current_user: dict = Depends(get_current_user)):
    """API для получения URL трека"""
    try:
        if not yandex_client:
            return JSONResponse({"error": "Сервис недоступен"}, status_code=503)
        
        # Разбираем ID трека (формат: trackId_albumId)
        parts = track_id.split('_')
        if len(parts) != 2:
            return JSONResponse({"error": "Неверный формат ID трека"}, status_code=400)
        
        track_id_num = parts[0]
        album_id = parts[1]
        
        # Получаем информацию о треке
        tracks = yandex_client.tracks([f"{track_id_num}:{album_id}"])
        if not tracks:
            return JSONResponse({"error": "Трек не найден"}, status_code=404)
        
        track = tracks[0]
        
        # Получаем ссылку для скачивания/прослушивания
        download_info = track.get_download_info()
        if not download_info:
            return JSONResponse({"error": "Не удалось получить информацию для загрузки"}, status_code=404)
        
        # Берем первую доступную ссылку
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
                "artists": [artist.name for artist in track.artists],
                "duration": track.duration_ms,
                "cover_uri": f"https://{track.cover_uri.replace('%%', '400x400')}" if track.cover_uri else None
            }
        else:
            return JSONResponse({"error": "Нет доступных ссылок для загрузки"}, status_code=404)
            
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)