from sqlalchemy.orm import Session
from datetime import datetime
from . import models

def get_user_by_telegram_id(db: Session, telegram_id: int):
    """Находит пользователя в БД по telegram_id"""
    return db.query(models.User).filter(models.User.telegram_id == telegram_id).first()

def create_user(db: Session, telegram_data: dict):
    """Создает нового пользователя в БД"""
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

def update_user(db: Session, db_user: models.User, telegram_data: dict):
    """Обновляет данные существующего пользователя"""
    db_user.first_name = telegram_data['first_name']
    db_user.last_name = telegram_data.get('last_name')
    db_user.username = telegram_data.get('username')
    db_user.photo_url = telegram_data.get('photo_url')
    db_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_user)
    return db_user

def get_or_create_user(db: Session, telegram_data: dict):
    """Находит пользователя или создает нового"""
    db_user = get_user_by_telegram_id(db, telegram_data['id'])
    
    if db_user:
        return update_user(db, db_user, telegram_data)
    else:
        return create_user(db, telegram_data)

def get_user_gifts(db: Session, user_id: int):
    """Получает все подарки пользователя"""
    return db.query(models.Gift).filter(models.Gift.seller_id == user_id).all()

def create_gift(db: Session, gift_data: dict):
    """Создает новый подарок"""
    db_gift = models.Gift(**gift_data)
    db.add(db_gift)
    db.commit()
    db.refresh(db_gift)
    return db_gift