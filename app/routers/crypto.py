from fastapi import APIRouter, HTTPException
import aiohttp
import asyncio
from typing import List, Dict, Any
import os

router = APIRouter(prefix="/crypto", tags=["crypto"])

COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")

async def fetch_crypto_data(session: aiohttp.ClientSession, crypto_id: str) -> Dict[str, Any]:
    """Получает данные одной криптовалюты с CoinGecko API"""
    url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}"
    
    headers = {}
    if COINGECKO_API_KEY:
        headers["x-cg-demo-api-key"] = COINGECKO_API_KEY
    
    try:
        async with session.get(url, headers=headers) as response:
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

async def fetch_chart_data(session: aiohttp.ClientSession, crypto_id: str, days: int = 7):
    """Получает данные для графика"""
    url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}/market_chart"
    
    headers = {}
    if COINGECKO_API_KEY:
        headers["x-cg-demo-api-key"] = COINGECKO_API_KEY
    
    params = {
        "vs_currency": "usd",
        "days": days,
        "interval": "daily"
    }
    
    try:
        async with session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return {
                    "prices": data["prices"],
                    "market_caps": data["market_caps"],
                    "total_volumes": data["total_volumes"]
                }
            else:
                return {"error": "Failed to fetch chart data"}
    except Exception as e:
        return {"error": str(e)}

@router.get("/prices")
async def get_crypto_prices():
    """Возвращает данные топовых криптовалют"""
    crypto_ids = ["bitcoin", "ethereum", "toncoin", "binancecoin", "solana", "ripple"]
    
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_crypto_data(session, crypto_id) for crypto_id in crypto_ids]
        results = await asyncio.gather(*tasks)
        
        successful_results = [result for result in results if "error" not in result]
        
        return {
            "cryptos": successful_results,
            "count": len(successful_results)
        }

@router.get("/chart/{crypto_id}")
async def get_crypto_chart(crypto_id: str, days: int = 7):
    """Возвращает данные для графика"""
    async with aiohttp.ClientSession() as session:
        chart_data = await fetch_chart_data(session, crypto_id.lower(), days)
        
        if "error" in chart_data:
            raise HTTPException(status_code=404, detail=f"Chart data for {crypto_id} not found")
        
        return chart_data