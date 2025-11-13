import json
from fastapi import Request, Cookie, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import crud

def get_current_user(
    request: Request,
    tg_user: str = Cookie(None),
    db: Session = Depends(get_db)
):
    if not tg_user:
        return None
    
    try:
        telegram_data = json.loads(tg_user)
        db_user = crud.get_user_by_telegram_id(db, telegram_data['id'])
        
        # Если пользователя нет в БД, создаем его
        if not db_user:
            db_user = crud.create_user(db, telegram_data)
        
        return {
            "telegram_data": telegram_data,
            "db_user": db_user
        }
    except (json.JSONDecodeError, Exception) as e:
        print(f"Error in get_current_user: {e}")
        return None