import logging
from constant import arcade_maps, GAMEID_API_URL
from curl_cffi import AsyncSession
import asyncio
import os
logger = logging.getLogger(__name__)

# 使用一个简单的字典作为内存缓存
# 格式: { "arcade_name": count }
_cache = {}

def get_last_reported_count(arcade_name: str) -> int | None:
    """获取指定机厅最后一次上报的人数"""
    return _cache.get(arcade_name)

def update_last_reported_count(arcade_name: str, count: int):
    """更新指定机厅最后一次上报的人数"""
    _cache[arcade_name] = count
    logger.info(f"缓存已更新：'{arcade_name}' 人数设置为 {count}")

def is_report_needed(arcade_name: str, current_count: int) -> bool:
    """检查是否需要上报"""
    last_count = get_last_reported_count(arcade_name)
    if last_count is not None and last_count == current_count:
        logger.info(f"机厅 '{arcade_name}' 人数 ({current_count}) 未发生变化，跳过上报。")
        return False
    return True

_cache_gameid = {}

async def clear_gameid_cache_periodically():
    """定期清空 gameid 缓存"""
    # 默认12小时 (12 * 60 * 60 = 43200秒)
    clear_interval_seconds = int(os.getenv("GAMEID_CACHE_CLEAR_INTERVAL", 43200))
    logger.info(f"GameID 缓存将每 {clear_interval_seconds} 秒清空一次。")
    while True:
        await asyncio.sleep(clear_interval_seconds)
        _cache_gameid.clear()
        logger.info("GameID 缓存已清空。")

async def get_gameid(arcade_name: str) -> int | None:
    """根据机厅名称获取游戏 ID，优先从 API 获取，失败则回退到本地常量"""
    if arcade_name in _cache_gameid:
        return _cache_gameid[arcade_name]

    if arcade_name not in arcade_maps:
        raise ValueError(f"未知的机厅名称: {arcade_name}")

    path = arcade_maps[arcade_name]["path"]
    url = GAMEID_API_URL.format(path=path)

    try:
        async with AsyncSession() as session:
            response = await session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json().get("shop", {})
            games = data.get("games", [])
            if games:
                min_title_id = min((game["titleId"] for game in games), default=None)
                games_with_min_title = [g for g in games if g["titleId"] == min_title_id]
                min_gameid = min((g["gameId"] for g in games_with_min_title), default=None)

                if min_gameid is not None:
                    _cache_gameid[arcade_name] = min_gameid
                    logger.info(f"成功从 API 获取机厅 '{arcade_name}' 的 gameid: {min_gameid}")
                    return min_gameid
            else:
                logger.warning(f"机厅 '{arcade_name}' 的 API 响应中没有找到游戏信息。")
    except Exception as e:
        logger.error(f"从 API 获取机厅 '{arcade_name}' 的 gameid 失败: {e}，将使用备用 gameid。")

    # 如果 API 请求失败或未找到 gameid，则使用备用 gameid
    fallback_gameid = arcade_maps[arcade_name].get("gameid")
    if fallback_gameid:
        logger.warning(f"机厅 '{arcade_name}' 使用备用 gameid: {fallback_gameid} (本次不缓存)")
        return fallback_gameid

    raise ValueError(f"无法为机厅 '{arcade_name}' 获取 gameid")
