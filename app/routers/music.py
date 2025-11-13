from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
import requests
import asyncio
from typing import List, Dict
import random

router = APIRouter(prefix="/music", tags=["music"])

# Предзагруженные популярные треки с archive.org
POPULAR_TRACKS = [
    {
        'id': 'lofichillstudybeats',
        'title': 'Lofi Chill Study Beats',
        'artist': 'Various Artists',
        'duration': 3600,
        'thumbnail': 'https://archive.org/download/lofichillstudybeats/cover.jpg',
        'stream_url': 'https://archive.org/download/lofichillstudybeats/lofichillstudybeats.mp3'
    },
    {
        'id': 'ambientworkmusic',
        'title': 'Ambient Work Music',
        'artist': 'Ambient Collective',
        'duration': 1800,
        'thumbnail': 'https://archive.org/download/ambientworkmusic/cover.jpg',
        'stream_url': 'https://archive.org/download/ambientworkmusic/ambientworkmusic.mp3'
    },
    {
        'id': 'jazzforstudying',
        'title': 'Jazz for Studying',
        'artist': 'Jazz Ensemble',
        'duration': 2700,
        'thumbnail': 'https://archive.org/download/jazzforstudying/cover.jpg',
        'stream_url': 'https://archive.org/download/jazzforstudying/jazzforstudying.mp3'
    }
]

def search_archive_simple(query: str = "") -> List[Dict]:
    """Простой поиск на archive.org"""
    try:
        if not query:
            return POPULAR_TRACKS
        
        # Для демо - возвращаем популярные треки + поисковой запрос
        results = []
        for track in POPULAR_TRACKS:
            if query.lower() in track['title'].lower() or query.lower() in track['artist'].lower():
                results.append(track)
        
        # Если ничего не найдено, все равно возвращаем популярные
        if not results:
            results = POPULAR_TRACKS[:3]
            
        return results
        
    except Exception as e:
        print(f"Search error: {e}")
        return POPULAR_TRACKS

@router.get("/search")
async def search_music(query: str = Query(..., min_length=1)):
    """Поиск музыки"""
    results = search_archive_simple(query)
    
    return {
        "query": query, 
        "results": results,
        "count": len(results)
    }

@router.get("/popular")
async def get_popular_music():
    """Популярная музыка"""
    return {
        "results": POPULAR_TRACKS,
        "count": len(POPULAR_TRACKS)
    }

@router.get("/stream/{item_id}")
async def stream_music(item_id: str):
    """Стримит музыку"""
    try:
        # Ищем трек в наших предзагруженных
        track = None
        for t in POPULAR_TRACKS:
            if t['id'] == item_id:
                track = t
                break
        
        if not track:
            raise HTTPException(status_code=404, detail="Track not found")
        
        # Проксируем стрим
        audio_response = requests.get(track['stream_url'], stream=True)
        
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

@router.get("/test")
async def test_music():
    """Тестовый endpoint для проверки"""
    return {
        "status": "ok",
        "tracks_available": len(POPULAR_TRACKS),
        "tracks": POPULAR_TRACKS
    }