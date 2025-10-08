import asyncio
from curl_cffi import AsyncSession
from curl_cffi.requests import Response
from constant import API_URL, arcade_maps
import os
import logging
from typing import cast

logger = logging.getLogger(__name__)
API_KEY = os.getenv("API_KEY", "")

async def upload(arcades_data: list[tuple[str, int]]):
    async with AsyncSession(impersonate="chrome") as s:
        tasks = []
        for arcade, count in arcades_data:
            arcade_info = arcade_maps.get(arcade)
            if not arcade_info:
                logger.warning(f"未找到机厅 '{arcade}' 的配置信息，已跳过。")
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
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            arcade_name = arcades_data[i][0]
            if isinstance(result, Exception):
                logger.error(f"上传机厅 '{arcade_name}' 数据失败: {result}")
            else:
                # Explicitly cast the type to silence Pylance warnings
                response = cast(Response, result)
                if response.status_code >= 400:
                    logger.error(f"上传机厅 '{arcade_name}' 数据失败，状态码: {response.status_code}, 响应: {response.text}")
                else:
                    try:
                        data = response.json()
                        if data.get("success"):
                            logger.info(f"成功上传机厅 '{arcade_name}' 的数据。")
                        else:
                            logger.error(f"上传机厅 '{arcade_name}' 数据失败，API返回失败状态, 响应: {response.text}")
                    except Exception:
                        logger.error(f"上传机厅 '{arcade_name}' 数据失败，无法解析响应JSON, 状态码: {response.status_code}, 响应: {response.text}")
