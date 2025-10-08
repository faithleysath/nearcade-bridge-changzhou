import logging

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
