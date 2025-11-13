import os
import hmac
import hashlib
import json
import time
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request, Cookie, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="TG Music")
BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_USERNAME = os.getenv("BOT_USERNAME")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def verify_telegram_auth(auth_data: Dict[str, Any]) -> Dict[str, Any]:
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

@app.get("/")
async def home(request: Request, tg_user: Optional[str] = Cookie(None)):
    user_data = json.loads(tg_user) if tg_user else None
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user_data": user_data,
        "bot_username": BOT_USERNAME
    })

@app.get("/profile")
async def profile(request: Request, tg_user: Optional[str] = Cookie(None)):
    if not tg_user:
        return RedirectResponse(url="/")
    user_data = json.loads(tg_user)
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user_data": user_data
    })

@app.get("/auth/telegram")
async def auth_telegram(request: Request, id: int, first_name: str, auth_date: int, hash: str,
                       last_name: Optional[str] = None, username: Optional[str] = None, 
                       photo_url: Optional[str] = None):
    auth_data = {k: v for k, v in locals().items() if k != 'request' and v is not None}
    
    try:
        verified_data = verify_telegram_auth(auth_data.copy())
        response = RedirectResponse(url="/")
        response.set_cookie("tg_user", json.dumps(verified_data), httponly=True, max_age=86400)
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("tg_user")
    return response