import os
import hmac
import hashlib
import json
import time
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request, Response, Cookie, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

app = FastAPI(title="Telegram Auth Example")

# Конфигурация
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
BOT_USERNAME = os.getenv("BOT_USERNAME", "YOUR_BOT_USERNAME_HERE")

class TelegramUser(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    auth_date: int
    hash: str

def verify_telegram_auth(auth_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Проверка авторизации Telegram
    """
    try:
        # Извлекаем хэш и удаляем его из данных для проверки
        check_hash = auth_data.pop('hash')
        
        # Создаем строку для проверки
        data_check_arr = []
        for key, value in sorted(auth_data.items()):
            if value is not None:
                data_check_arr.append(f"{key}={value}")
        
        data_check_string = "\n".join(data_check_arr)
        
        # Создаем секретный ключ
        secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
        
        # Вычисляем HMAC
        computed_hash = hmac.new(
            secret_key, 
            data_check_string.encode(), 
            hashlib.sha256
        ).hexdigest()
        
        # Проверяем хэш
        if not hmac.compare_digest(computed_hash, check_hash):
            raise ValueError("Invalid hash")
        
        # Проверяем время (данные не старше 1 дня)
        if (time.time() - int(auth_data['auth_date'])) > 86400:
            raise ValueError("Data is outdated")
        
        return auth_data
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authorization failed: {str(e)}")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, tg_user: Optional[str] = Cookie(None)):
    """
    Главная страница с виджетом Telegram
    """
    if tg_user:
        try:
            user_data = json.loads(tg_user)
            first_name = user_data.get('first_name', '')
            last_name = user_data.get('last_name', '')
            username = user_data.get('username', '')
            photo_url = user_data.get('photo_url', '')
            
            if username:
                user_html = f"""
                <h1>Hello, <a href="https://t.me/{username}" target="_blank">{first_name} {last_name}</a>!</h1>
                """
            else:
                user_html = f"<h1>Hello, {first_name} {last_name}!</h1>"
            
            if photo_url:
                user_html += f'<img src="{photo_url}" alt="Profile Photo" style="border-radius: 50%; width: 100px; height: 100px; margin: 10px;">'
            
            user_html += '<p><a href="/logout">Log out</a></p>'
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Telegram Auth Example</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; text-align: center; }}
                    .container {{ max-width: 600px; margin: 0 auto; }}
                    img {{ border-radius: 50%; }}
                    a {{ color: #0088cc; text-decoration: none; }}
                    a:hover {{ text-decoration: underline; }}
                </style>
            </head>
            <body>
                <div class="container">
                    {user_html}
                </div>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content)
            
        except json.JSONDecodeError:
            # Если кука повреждена, удаляем её
            response = RedirectResponse(url="/")
            response.delete_cookie("tg_user")
            return response
    
    # Показываем виджет для неавторизованных пользователей
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Telegram Auth Example</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; text-align: center; }}
            .container {{ max-width: 600px; margin: 0 auto; }}
            h1 {{ color: #333; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Hello, anonymous!</h1>
            <p>Please authorize via Telegram:</p>
            <script async 
                src="https://telegram.org/js/telegram-widget.js?22" 
                data-telegram-login="{BOT_USERNAME}" 
                data-size="large" 
                data-auth-url="/auth/telegram"
                data-request-access="write">
            </script>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/auth/telegram")
async def auth_telegram(
    request: Request,
    id: int,
    first_name: str,
    auth_date: int,
    hash: str,
    last_name: Optional[str] = None,
    username: Optional[str] = None,
    photo_url: Optional[str] = None
):
    """
    Обработка callback от Telegram Widget
    """
    # Собираем все параметры
    auth_data = {
        'id': id,
        'first_name': first_name,
        'auth_date': auth_date,
        'hash': hash,
        'last_name': last_name,
        'username': username,
        'photo_url': photo_url
    }
    
    # Проверяем авторизацию
    try:
        verified_data = verify_telegram_auth(auth_data.copy())
        
        # Сохраняем данные пользователя в куки
        response = RedirectResponse(url="/")
        response.set_cookie(
            key="tg_user",
            value=json.dumps(verified_data),
            httponly=True,
            max_age=86400,  # 1 день
            secure=True,    # Для production используйте True
            samesite="lax"
        )
        
        return response
        
    except HTTPException as e:
        return HTMLResponse(content=f"<h1>Error: {e.detail}</h1>")

@app.get("/logout")
async def logout():
    """
    Выход из системы
    """
    response = RedirectResponse(url="/")
    response.delete_cookie("tg_user")
    return response

@app.get("/api/user")
async def get_current_user(tg_user: Optional[str] = Cookie(None)):
    """
    API endpoint для получения данных текущего пользователя
    """
    if not tg_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        user_data = json.loads(tg_user)
        return user_data
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid user data")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)