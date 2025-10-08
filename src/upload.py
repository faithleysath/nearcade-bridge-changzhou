import asyncio
from curl_cffi import AsyncSession
from curl_cffi.requests import Response
from constant import API_URL, arcade_maps
from cache import is_report_needed, update_last_reported_count, get_gameid
import os
import logging
import json

logger = logging.getLogger(__name__)
API_KEY = os.getenv("API_KEY", "")

async def upload(arcades_data: list[tuple[str, int]]):
    # 筛选需要上报的机厅
    arcades_to_report = []
    for arcade, count in arcades_data:
        if not is_report_needed(arcade, count):
            continue
        
        arcade_info = arcade_maps.get(arcade)
        if not arcade_info:
            logger.warning(f"未找到机厅 '{arcade}' 的配置信息，已跳过。")
            continue
        
        arcades_to_report.append({"arcade": arcade, "count": count, "info": arcade_info})

    if not arcades_to_report:
        logger.info("没有需要更新的数据。")
        return

    # 并发获取 game_id
    game_id_tasks = [get_gameid(data["arcade"]) for data in arcades_to_report]
    results = await asyncio.gather(*game_id_tasks, return_exceptions=True)

    upload_payloads = []
    for i, result in enumerate(results):
        arcade_data = arcades_to_report[i]
        arcade = arcade_data["arcade"]
        count = arcade_data["count"]
        arcade_info = arcade_data["info"]

        if isinstance(result, Exception) or result is None:
            logger.error(f"无法获取机厅 '{arcade}' 的 gameid，已跳过。原因: {result}")
            continue

        upload_payloads.append({
            "arcade": arcade,
            "count": count,
            "url": API_URL.format(path=arcade_info["path"]),
            "payload": {
                "games": [{"id": result, "currentAttendances": count}]
            }
        })

    if not upload_payloads:
        logger.info("所有机厅都因无法获取 gameid 而跳过。")
        return

    async with AsyncSession(impersonate="chrome") as s:
        tasks = []
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            'Content-Type': 'application/json'
        }
        for data in upload_payloads:
            task = s.post(data["url"], json=data["payload"], headers=headers, timeout=10)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            arcade_name = upload_payloads[i]["arcade"]
            count = upload_payloads[i]["count"]
            if isinstance(result, Exception):
                logger.error(f"上传机厅 '{arcade_name}' 数据失败: {result}")
            else:
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
                    except json.JSONDecodeError:
                        logger.error(f"上传机厅 '{arcade_name}' 数据失败，无法解析响应JSON, 状态码: {result.status_code}, 响应: {result.text}")
