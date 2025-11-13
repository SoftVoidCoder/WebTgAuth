import hmac
import hashlib
import json
import time
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os

from app.database import get_db
from app import crud

load_dotenv()

router = APIRouter(prefix="/auth", tags=["auth"])  

BOT_TOKEN = os.getenv("BOT_TOKEN")

def verify_telegram_auth(auth_data: dict) -> dict:
    check_hash = auth_data.pop('hash')
    data_check_arr = [f"{k}={v}" for k, v in sorted(auth_data.items()) if v is not None]
    data_check_string = "\n".join(data_check_arr)
    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    
    if not hmac.compare_digest(computed_hash, check_hash):
        raise ValueError("Invalid hash")
    if (time.time() - int(auth_data['auth_date'])) > 86400:
        raise ValueError("Data is outdated")
    return auth_data

@router.get("/telegram")
async def auth_telegram(
    request: Request,
    id: int,
    first_name: str,
    auth_date: int,
    hash: str,
    db: Session = Depends(get_db),
    last_name: str = None,
    username: str = None,
    photo_url: str = None
):
    auth_data = {
        'id': id,
        'first_name': first_name,
        'auth_date': auth_date,
        'hash': hash,
        'last_name': last_name,
        'username': username,
        'photo_url': photo_url
    }
    
    try:
        verified_data = verify_telegram_auth(auth_data.copy())
        db_user = crud.get_or_create_user(db, verified_data)
        
        response = RedirectResponse(url="/")
        response.set_cookie(
            "tg_user",
            json.dumps(verified_data),
            httponly=True,
            max_age=86400,
            secure=True,
            samesite="lax"
        )
        return response
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("tg_user")
    return response