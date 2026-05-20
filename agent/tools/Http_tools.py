import httpx
import os
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("MAAT_ENDPOINT")


async def post(url, payload):
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        return response.json()
