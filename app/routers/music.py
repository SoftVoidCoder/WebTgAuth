from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
import requests
import asyncio
from typing import List, Dict
import random

router = APIRouter(prefix="/music", tags=["music"])

def search_archive_music(query: str = "", limit: int = 20) -> List[Dict]:
    """Ищет музыку на archive.org"""
    try:
        if query:
            # Поиск по конкретному запросу
            search_query = f'collection:opensource_audio AND ({query})'
        else:
            # Популярная музыка (lofi, chill, ambient)
            search_query = 'collection:opensource_audio AND (lofi OR chill OR ambient OR "lo-fi" OR jazz OR classical)'
        
        url = "https://archive.org/advancedsearch.php"
        params = {
            'q': search_query,
            'fl[]': ['identifier', 'title', 'creator', 'description', 'downloads'],
            'sort[]': 'downloads desc',
            'rows': limit,
            'page': 1,
            'output': 'json'
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        results = []
        for item in data.get('response', {}).get('docs', []):
            item_id = item['identifier']
            
            # Получаем детальную информацию о item
            try:
                item_url = f"https://archive.org/metadata/{item_id}"
                item_response = requests.get(item_url)
                item_data = item_response.json()
                
                # Ищем аудио файлы
                audio_files = []
                if 'files' in item_data:
                    for file_name, file_info in item_data['files'].items():
                        if file_info.get('format', '').lower() in ['mp3', 'vbr mp3', 'ogg vorbis']:
                            audio_files.append({
                                'name': file_name,
                                'url': f"https://archive.org/download/{item_id}/{file_name}",
                                'size': file_info.get('size', 0)
                            })
                
                # Берем самый большой MP3 файл (скорее всего это полный трек)
                if audio_files:
                    # Сортируем по размеру (больший = полный трек)
                    audio_files.sort(key=lambda x: x['size'], reverse=True)
                    best_audio = audio_files[0]
                    
                    # Получаем название и артиста
                    title = item.get('title', 'Unknown')
                    if isinstance(title, list):
                        title = title[0]
                    
                    artist = item.get('creator', 'Unknown Artist')
                    if isinstance(artist, list):
                        artist = artist[0]
                    
                    # Получаем обложку если есть
                    thumbnail = None
                    for file_name in ['cover.jpg', 'thumb.jpg', '__ia_thumb.jpg']:
                        if file_name in item_data.get('files', {}):
                            thumbnail = f"https://archive.org/download/{item_id}/{file_name}"
                            break
                    
                    results.append({
                        'id': item_id,
                        'title': title,
                        'artist': artist,
                        'duration': 0,  # archive.org не всегда дает длительность
                        'thumbnail': thumbnail,
                        'stream_url': best_audio['url'],
                        'file_size': best_audio['size'],
                        'downloads': item.get('downloads', 0)
                    })
                    
            except Exception as e:
                print(f"Error processing item {item_id}: {e}")
                continue
        
        return results[:limit]  # Ограничиваем количество
        
    except Exception as e:
        print(f"Archive.org search error: {e}")
        return []

def get_archive_popular() -> List[Dict]:
    """Получает популярную музыку с archive.org"""
    # Популярные жанры для главной страницы
    popular_genres = ['lofi', 'chill', 'ambient', 'jazz', 'classical']
    genre = random.choice(popular_genres)
    return search_archive_music(genre, 25)

@router.get("/search")
async def search_music(query: str = Query(..., min_length=1)):
    """Поиск музыки через archive.org"""
    results = await asyncio.get_event_loop().run_in_executor(
        None, search_archive_music, query, 20
    )
    
    return {
        "query": query, 
        "results": results,
        "count": len(results)
    }

@router.get("/popular")
async def get_popular_music():
    """Популярная музыка для главной страницы"""
    results = await asyncio.get_event_loop().run_in_executor(
        None, get_archive_popular
    )
    
    return {
        "results": results,
        "count": len(results)
    }

@router.get("/stream/{item_id}")
async def stream_music(item_id: str):
    """Стримит полные треки с archive.org"""
    try:
        # Получаем информацию о item
        item_url = f"https://archive.org/metadata/{item_id}"
        item_response = requests.get(item_url)
        item_data = item_response.json()
        
        # Ищем самый большой MP3 файл
        stream_url = None
        if 'files' in item_data:
            audio_files = []
            for file_name, file_info in item_data['files'].items():
                if file_info.get('format', '').lower() in ['mp3', 'vbr mp3']:
                    audio_files.append({
                        'name': file_name,
                        'url': f"https://archive.org/download/{item_id}/{file_name}",
                        'size': file_info.get('size', 0)
                    })
            
            if audio_files:
                # Берем самый большой файл (скорее всего полный трек)
                audio_files.sort(key=lambda x: x['size'], reverse=True)
                stream_url = audio_files[0]['url']
        
        if not stream_url:
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        # Проксируем стрим
        audio_response = requests.get(stream_url, stream=True)
        
        return StreamingResponse(
            audio_response.iter_content(chunk_size=8192),
            media_type="audio/mpeg",
            headers={
                "Content-Type": "audio/mpeg", 
                "Cache-Control": "no-cache",
                "Accept-Ranges": "bytes"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stream error: {str(e)}")