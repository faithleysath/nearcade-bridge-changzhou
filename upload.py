import asyncio
from curl_cffi import AsyncSession
from constant import API_URL, arcade_maps
import os

API_KEY = os.getenv("API_KEY", "")

async def upload(arcades_data: list[tuple[str, int]]):
    async with AsyncSession() as s:
        tasks = []
        for arcade, count in arcades_data:
            arcade_info = arcade_maps.get(arcade)
            if not arcade_info:
                continue
            url = API_URL.format(path=arcade_info["path"])
            payload = {
                "games": [
                    {
                        "id": arcade_info["gameid"],
                        "currentAttendances": count
                    }
                ]
            }
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                'Content-Type': 'application/json'
            }
            task = s.post(url, json=payload, headers=headers, timeout=10)
            tasks.append(task)
        results = await asyncio.gather(*tasks, return_exceptions=False)
