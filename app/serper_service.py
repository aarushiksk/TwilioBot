import aiohttp
from fastapi import HTTPException
import httpx
import json

FACT_CHECK_API_URL = "https://google.serper.dev/search"
FACT_CHECK_API_KEY = "ebd6d582bd89fb117c402dde2ebb4c83a3d60749"
async def fetch_serper_fact_check(text: str):
    async with aiohttp.ClientSession() as session:
        headers = {"X-API-KEY": FACT_CHECK_API_KEY, "Content-Type": "application/json"}
        payload = {"q": text, "gl": "in"}
        async with session.post(FACT_CHECK_API_URL, headers=headers, json=payload, ssl=False) as response:
            if response.status != 200:
                raise HTTPException(status_code=response.status, detail="Error from Serper")
            return await response.json()