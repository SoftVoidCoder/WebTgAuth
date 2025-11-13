from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
import yt_dlp
import requests
import asyncio
from typing import List, Dict

router = APIRouter(prefix="/music", tags=["music"])

def search_youtube_music(query: str, limit: int = 20) -> List[Dict]:
    """Ищет музыку на YouTube"""
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'extractaudio': True,
            'audioformat': 'mp3', 
            'noplaylist': True,
            'default_search': f'ytsearch{limit}:'
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            
            results = []
            entries = info['entries'] if 'entries' in info else [info]
            
            for entry in entries:
                if entry:
                    results.append({
                        'id': entry['id'],
                        'title': entry.get('title', 'Unknown'),
                        'artist': entry.get('uploader', 'Unknown Artist'),
                        'duration': entry.get('duration', 0),
                        'thumbnail': entry.get('thumbnail'),
                        'view_count': entry.get('view_count', 0)
                    })
            
            return results[:limit]
            
    except Exception as e:
        print(f"YouTube search error: {e}")
        return []

@router.get("/search")
async def search_music(query: str = Query(..., min_length=2)):
    """Поиск музыки"""
    results = await asyncio.get_event_loop().run_in_executor(
        None, search_youtube_music, query
    )
    
    return {
        "query": query, 
        "results": results,
        "count": len(results)
    }

@router.get("/stream/{video_id}")
async def stream_music(video_id: str):
    """Стримит музыку напрямую с YouTube"""
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
        }
        
        def get_stream_url():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                return info['url']
        
        stream_url = await asyncio.get_event_loop().run_in_executor(None, get_stream_url)
        
        # Проксируем стрим
        response = requests.get(stream_url, stream=True)
        
        return StreamingResponse(
            response.iter_content(chunk_size=8192),
            media_type="audio/mpeg",
            headers={"Cache-Control": "no-cache"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stream error: {str(e)}")