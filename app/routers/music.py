from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
import yt_dlp
import os
import asyncio
from typing import List, Dict
import aiofiles

router = APIRouter(prefix="/music", tags=["music"])

# Папка для хранения музыки
MUSIC_DIR = "static/music"
os.makedirs(MUSIC_DIR, exist_ok=True)

def search_youtube(query: str) -> List[Dict]:
    """Ищет музыку на YouTube"""
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'extractaudio': True,
        'audioformat': 'mp3',
        'noplaylist': True,
        'default_search': 'ytsearch10:'
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            
            if 'entries' in info:
                results = []
                for entry in info['entries']:
                    if entry:
                        results.append({
                            'id': entry['id'],
                            'title': entry.get('title', 'Unknown'),
                            'artist': entry.get('uploader', 'Unknown'),
                            'duration': entry.get('duration', 0),
                            'thumbnail': entry.get('thumbnail'),
                            'url': entry.get('webpage_url')
                        })
                return results
    except Exception as e:
        print(f"Error searching YouTube: {e}")
        return []

async def download_audio(video_id: str, title: str) -> str:
    """Скачивает аудио с YouTube"""
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    filename = f"{video_id}_{safe_title}.mp3"
    filepath = os.path.join(MUSIC_DIR, filename)
    
    if os.path.exists(filepath):
        return filepath
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': filepath.replace('.mp3', ''),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': False
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f'https://www.youtube.com/watch?v={video_id}'])
        return filepath
    except Exception as e:
        print(f"Error downloading audio: {e}")
        return None

@router.get("/search")
async def search_music(query: str = Query(..., min_length=2)):
    """Поиск музыки"""
    if not query or len(query) < 2:
        raise HTTPException(status_code=400, detail="Query too short")
    
    results = await asyncio.get_event_loop().run_in_executor(
        None, search_youtube, query
    )
    
    return {
        "query": query,
        "results": results[:10],  # первые 10 результатов
        "count": len(results)
    }

@router.get("/stream/{video_id}")
async def stream_music(video_id: str, title: str):
    """Стримит музыку"""
    filepath = await download_audio(video_id, title)
    
    if not filepath or not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Music not found")
    
    return FileResponse(
        filepath,
        media_type="audio/mpeg",
        filename=f"{title}.mp3"
    )

@router.get("/download/{video_id}")
async def download_music(video_id: str, title: str):
    """Скачивает музыку"""
    filepath = await download_audio(video_id, title)
    
    if not filepath or not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Music not found")
    
    return FileResponse(
        filepath,
        media_type="audio/mpeg",
        filename=f"{title}.mp3"
    )