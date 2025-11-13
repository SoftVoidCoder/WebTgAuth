import json
from fastapi import Request, Cookie, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import crud

# Зависимость для получения текущего пользователя
def get_current_user(
    request: Request,
    tg_user: str = Cookie(None),  # Берем куку tg_user
    db: Session = Depends(get_db)  # Получаем сессию БД
):
    # Если нет куки - пользователь не авторизован
    if not tg_user:
        return None
    
    try:
        # Парсим данные из куки
        telegram_data = json.loads(tg_user)
        # Ищем пользователя в БД
        db_user = crud.get_user_by_telegram_id(db, telegram_data['id'])
        
        # Если пользователя нет в БД - создаем
        if not db_user:
            db_user = crud.create_user(db, telegram_data)
        
        # Возвращаем данные для шаблонов
        return {
            "telegram_data": telegram_data,  # Данные из Telegram
            "db_user": db_user               # Данные из БД
        }
    except (json.JSONDecodeError, Exception) as e:
        print(f"Error in get_current_user: {e}")
        return None