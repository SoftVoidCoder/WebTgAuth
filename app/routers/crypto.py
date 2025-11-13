from fastapi import APIRouter, HTTPException
import aiohttp
import asyncio
from typing import List, Dict, Any

router = APIRouter(prefix="/crypto", tags=["crypto"])

# ID топовых криптовалют для CoinGecko API
TOP_CRYPTO_IDS = ["bitcoin", "ethereum", "toncoin"]

async def fetch_crypto_data(session: aiohttp.ClientSession, crypto_id: str) -> Dict[str, Any]:
    """Получает данные одной криптовалюты с CoinGecko API"""
    url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}"
    
    try:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return {
                    "id": crypto_id,
                    "name": data.get("name", ""),
                    "symbol": data.get("symbol", "").upper(),
                    "current_price": data["market_data"]["current_price"]["usd"],
                    "price_change_24h": data["market_data"]["price_change_24h"],
                    "price_change_percentage_24h": data["market_data"]["price_change_percentage_24h"],
                    "market_cap": data["market_data"]["market_cap"]["usd"],
                    "image": data["image"]["large"]
                }
            else:
                return {"id": crypto_id, "error": "Failed to fetch data"}
    except Exception as e:
        return {"id": crypto_id, "error": str(e)}

@router.get("/prices")
async def get_crypto_prices():
    """Возвращает данные топовых криптовалют"""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_crypto_data(session, crypto_id) for crypto_id in TOP_CRYPTO_IDS]
        results = await asyncio.gather(*tasks)
        
        # Фильтруем успешные результаты
        successful_results = [result for result in results if "error" not in result]
        
        return {
            "cryptos": successful_results,
            "count": len(successful_results)
        }

@router.get("/price/{crypto_id}")
async def get_single_crypto_price(crypto_id: str):
    """Возвращает данные одной криптовалюты"""
    async with aiohttp.ClientSession() as session:
        data = await fetch_crypto_data(session, crypto_id.lower())
        
        if "error" in data:
            raise HTTPException(status_code=404, detail=f"Crypto {crypto_id} not found")
        
        return data