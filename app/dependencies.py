import json
from fastapi import Request, Cookie, HTTPException
from sqlalchemy.orm import Session
from . import crud

def get_current_user(
    request: Request,
    tg_user: str = Cookie(None),
    db: Session = None
):
    if not tg_user or not db:
        return None
    
    try:
        telegram_data = json.loads(tg_user)
        db_user = crud.get_user_by_telegram_id(db, telegram_data['id'])
        return {
            "telegram_data": telegram_data,
            "db_user": db_user
        }
    except json.JSONDecodeError:
        return None