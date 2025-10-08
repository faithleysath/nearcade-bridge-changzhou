#!/usr/bin/env python

import asyncio
import signal
from websockets.asyncio.server import serve, ServerConnection
import logging
from constant import arcade_maps, listen_qq_group, listen_qq_id, arcade_names
from extract import extract_ordered_tuples
from upload import upload
from cache import clear_gameid_cache_periodically
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def handler(websocket: ServerConnection):
    logger.info(f"Client connected from {websocket.remote_address}")
    async for message in websocket:
        logger.debug(f"Received message: {message}")
        try:
            data: dict = json.loads(message)
            if data.get("group_id") == listen_qq_group and data.get("user_id") == listen_qq_id:
                text = data.get("raw_message", "")
                results = extract_ordered_tuples(arcade_names, text)
                if results:
                    logger.info(f"Extracted data: {results}")
                    asyncio.create_task(upload(results))
        except json.JSONDecodeError:
            logger.error("Failed to decode JSON message")
    logger.info(f"Client disconnected from {websocket.remote_address}")


async def main():
    loop = asyncio.get_running_loop()
    stop = loop.create_future()
    loop.add_signal_handler(signal.SIGINT, stop.set_result, None)

    # 启动后台缓存清理任务
    asyncio.create_task(clear_gameid_cache_periodically())

    async with serve(handler, "0.0.0.0", 9999):
        logger.info("Server started on ws://0.0.0.0:9999. Press Ctrl+C to exit.")
        await stop

if __name__ == "__main__":
    logger.info("Starting server...")
    asyncio.run(main())
    logger.info("Server shut down gracefully.")
