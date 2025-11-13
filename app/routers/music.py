from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from yandex_music import Client
from app.dependencies import get_current_user

router = APIRouter(prefix="/music", tags=["music"])
templates = Jinja2Templates(directory="templates")

YANDEX_MUSIC_TOKEN = "y0__xCq06KNAxje-AYgtsC_khWI-0_xZL5Ctrii1vxK_bVg6w2MHA"

try:
    yandex_client = Client(YANDEX_MUSIC_TOKEN).init()
    print("✅ Яндекс.Музыка клиент успешно инициализирован")
except Exception as e:
    print(f"❌ Ошибка инициализации Яндекс.Музыка: {e}")
    yandex_client = None

@router.get("/listen", response_class=HTMLResponse)
async def listen_music(
    request: Request, 
    current_user: dict = Depends(get_current_user)
):
    user_data = current_user["telegram_data"] if current_user else None
    db_user = current_user["db_user"] if current_user else None
    
    popular_tracks = []
    
    try:
        if yandex_client:
            chart = yandex_client.chart()
            if chart and chart.chart:
                popular_tracks = chart.chart.tracks[:20]
    except Exception as e:
        print(f"Music error: {e}")
    
    return templates.TemplateResponse("listen.html", {
        "request": request,
        "user_data": user_data,
        "db_user": db_user,
        "popular_tracks": popular_tracks
    })

@router.get("/search", response_class=HTMLResponse)
async def search_music(
    request: Request,
    current_user: dict = Depends(get_current_user),
    query: str = Query(None)
):
    user_data = current_user["telegram_data"] if current_user else None
    db_user = current_user["db_user"] if current_user else None
    
    tracks = []
    artists = []
    
    try:
        if yandex_client and query:
            search_result = yandex_client.search(query)
            if search_result:
                if search_result.tracks:
                    tracks = search_result.tracks.results[:30]
                if search_result.artists:
                    artists = search_result.artists.results[:20]
    except Exception as e:
        print(f"Search error: {e}")
    
    return templates.TemplateResponse("search.html", {
        "request": request,
        "user_data": user_data,
        "db_user": db_user,
        "tracks": tracks,
        "artists": artists,
        "search_query": query
    })

@router.get("/track/{track_id}")
async def get_track_url(track_id: str, current_user: dict = Depends(get_current_user)):
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

@router.get("/artist/{artist_id}")
async def get_artist_tracks(artist_id: str, current_user: dict = Depends(get_current_user)):
    try:
        if not yandex_client:
            return {"error": "Сервис недоступен"}
        
        artist = yandex_client.artists(artist_id)
        if not artist:
            return {"error": "Исполнитель не найден"}
        
        tracks = yandex_client.artists_tracks(artist_id, page_size=20)
        
        artist_data = {
            "id": artist.id,
            "name": artist.name,
            "cover": f"https://{artist.cover.uri.replace('%%', '300x300')}" if artist.cover else None,
            "tracks": []
        }
        
        if tracks:
            for track in tracks:
                track_info = {
                    "id": f"{track.id}_{track.albums[0].id}" if track.albums else str(track.id),
                    "title": track.title,
                    "cover_uri": f"https://{track.cover_uri.replace('%%', '300x300')}" if track.cover_uri else None
                }
                artist_data["tracks"].append(track_info)
        
        return artist_data
        
    except Exception as e:
        return {"error": str(e)}