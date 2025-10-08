import asyncio
from curl_cffi import AsyncSession
from curl_cffi.requests import Response
from constant import API_URL, arcade_maps
from cache import is_report_needed, update_last_reported_count
import os
import logging

logger = logging.getLogger(__name__)
API_KEY = os.getenv("API_KEY", "")

async def upload(arcades_data: list[tuple[str, int]]):
    async with AsyncSession(impersonate="chrome") as s:
        tasks = []
        upload_attempts = []
        for arcade, count in arcades_data:
            if not is_report_needed(arcade, count):
                continue

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
            upload_attempts.append((arcade, count))

        if not tasks:
            logger.info("没有需要更新的数据。")
            return

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            arcade_name, count = upload_attempts[i]
            if isinstance(result, Exception):
                logger.error(f"上传机厅 '{arcade_name}' 数据失败: {result}")
            else:
                # Assert the type for both static analysis and runtime safety
                assert isinstance(result, Response)
                if result.status_code >= 400:
                    if "Shop is currently closed" in result.text:
                        logger.warning(f"机厅 '{arcade_name}' 已打烊，本次未更新。")
                    else:
                        logger.error(f"上传机厅 '{arcade_name}' 数据失败，状态码: {result.status_code}, 响应: {result.text}")
                else:
                    try:
                        data = result.json()
                        if data.get("success"):
                            logger.info(f"成功上传机厅 '{arcade_name}' 的数据。")
                            update_last_reported_count(arcade_name, count)
                        else:
                            logger.error(f"上传机厅 '{arcade_name}' 数据失败，API返回失败状态, 响应: {result.text}")
                    except Exception:
                        logger.error(f"上传机厅 '{arcade_name}' 数据失败，无法解析响应JSON, 状态码: {result.status_code}, 响应: {result.text}")
