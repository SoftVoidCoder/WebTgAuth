from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
import requests
import asyncio
from typing import List, Dict

router = APIRouter(prefix="/music", tags=["music"])

def search_deezer_music(query: str = "", limit: int = 25) -> List[Dict]:
    """Ищет музыку в Deezer"""
    try:
        url = "https://api.deezer.com/search"
        params = {
            'q': query,
            'limit': limit
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        results = []
        for track in data.get('data', []):
            # Deezer дает 30-секундные превью бесплатно
            if track.get('preview'):
                results.append({
                    'id': track['id'],
                    'title': track.get('title', 'Unknown'),
                    'artist': track['artist'].get('name', 'Unknown Artist'),
                    'duration': track.get('duration', 0),
                    'thumbnail': track['album'].get('cover_medium'),
                    'preview_url': track.get('preview'),  # 30-секундный превью
                    'full_url': track.get('link'),
                    'album': track['album'].get('title', 'Unknown Album')
                })
        
        return results
        
    except Exception as e:
        print(f"Deezer search error: {e}")
        return []

def get_deezer_popular() -> List[Dict]:
    """Получает популярную музыку с Deezer"""
    try:
        # Чарт Deezer
        url = "https://api.deezer.com/chart/0/tracks"
        params = {'limit': 20}
        
        response = requests.get(url, params=params)
        data = response.json()
        
        results = []
        for track in data.get('data', []):
            if track.get('preview'):
                results.append({
                    'id': track['id'],
                    'title': track.get('title', 'Unknown'),
                    'artist': track['artist'].get('name', 'Unknown Artist'),
                    'duration': track.get('duration', 0),
                    'thumbnail': track['album'].get('cover_medium'),
                    'preview_url': track.get('preview'),
                    'full_url': track.get('link'),
                    'album': track['album'].get('title', 'Unknown Album')
                })
        
        return results
        
    except Exception as e:
        print(f"Deezer popular error: {e}")
        return []

@router.get("/search")
async def search_music(query: str = Query(..., min_length=1)):
    """Поиск музыки через Deezer"""
    results = search_deezer_music(query, 20)
    
    return {
        "query": query, 
        "results": results,
        "count": len(results)
    }

@router.get("/popular")
async def get_popular_music():
    """Популярная музыка для главной страницы"""
    results = get_deezer_popular()
    
    return {
        "results": results,
        "count": len(results)
    }

@router.get("/stream/{track_id}")
async def stream_music(track_id: str):
    """Стримит 30-секундный превью с Deezer"""
    try:
        # Получаем информацию о треке
        url = f"https://api.deezer.com/track/{track_id}"
        response = requests.get(url)
        track_data = response.json()
        
        preview_url = track_data.get('preview')
        if not preview_url:
            raise HTTPException(status_code=404, detail="Preview not available")
        
        # Проксируем стрим превью
        audio_response = requests.get(preview_url, stream=True)
        
        return StreamingResponse(
            audio_response.iter_content(chunk_size=8192),
            media_type="audio/mpeg",
            headers={
                "Content-Type": "audio/mpeg",
                "Cache-Control": "no-cache"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stream error: {str(e)}")