from sqlalchemy.orm import Session
from datetime import datetime
from . import models

# Находит пользователя в БД по telegram_id
def get_user_by_telegram_id(db: Session, telegram_id: int):
    return db.query(models.User).filter(models.User.telegram_id == telegram_id).first()

# Создает нового пользователя в БД
def create_user(db: Session, telegram_data: dict):
    db_user = models.User(
        telegram_id=telegram_data['id'],
        first_name=telegram_data['first_name'],
        last_name=telegram_data.get('last_name'),
        username=telegram_data.get('username'),
        photo_url=telegram_data.get('photo_url')
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Обновляет данные существующего пользователя
def update_user(db: Session, db_user: models.User, telegram_data: dict):
    db_user.first_name = telegram_data['first_name']
    db_user.last_name = telegram_data.get('last_name')
    db_user.username = telegram_data.get('username')
    db_user.photo_url = telegram_data.get('photo_url')
    db_user.updated_at = datetime.utcnow()  # Обновляем время изменения
    db.commit()
    db.refresh(db_user)
    return db_user

# Основная функция: находит пользователя или создает нового
def get_or_create_user(db: Session, telegram_data: dict):
    # Ищем пользователя в БД
    db_user = get_user_by_telegram_id(db, telegram_data['id'])
    
    if db_user:
        # Если нашли - обновляем данные
        return update_user(db, db_user, telegram_data)
    else:
        # Если не нашли - создаем нового
        return create_user(db, telegram_data)
    


def get_liked_tracks(db: Session, user_id: int):
    print(f"🟢 GET_LIKED_TRACKS - user_id: {user_id}")
    
    tracks = db.query(models.LikedTrack).filter(
        models.LikedTrack.user_id == user_id
    ).all()
    
    print(f"🟢 Found {len(tracks)} liked tracks in DB")
    
    for track in tracks:
        print(f"🟢 Track: {track.track_id} - {track.track_title}")
    
    return tracks
def add_liked_track(db: Session, user_id: int, track_data: dict):
    # Проверяем нет ли уже этого трека в лайках
    existing = db.query(models.LikedTrack).filter(
        models.LikedTrack.user_id == user_id,
        models.LikedTrack.track_id == track_data['id']
    ).first()
    
    if existing:
        return existing  # Уже есть в лайках
    
    # ПРОБЛЕМА: track_data['artists'] может быть строкой или массивом
    artists_str = ''
    if isinstance(track_data['artists'], list):
        artists_str = ','.join(track_data['artists'])
    elif isinstance(track_data['artists'], str):
        artists_str = track_data['artists']
    else:
        artists_str = str(track_data['artists'])
    
    liked_track = models.LikedTrack(
        user_id=user_id,
        track_id=track_data['id'],
        track_title=track_data['title'],
        track_artists=artists_str,  # Исправлено
        track_cover_uri=track_data.get('cover_uri'),
        track_album=track_data.get('album', 'Неизвестный альбом')
    )
    db.add(liked_track)
    db.commit()
    db.refresh(liked_track)
    return liked_track

def remove_liked_track(db: Session, user_id: int, track_id: str):
    liked_track = db.query(models.LikedTrack).filter(
        models.LikedTrack.user_id == user_id,
        models.LikedTrack.track_id == track_id
    ).first()
    
    if liked_track:
        db.delete(liked_track)
        db.commit()
        return True
    return False

def is_track_liked(db: Session, user_id: int, track_id: str):
    return db.query(models.LikedTrack).filter(
        models.LikedTrack.user_id == user_id,
        models.LikedTrack.track_id == track_id
    ).first() is not None

