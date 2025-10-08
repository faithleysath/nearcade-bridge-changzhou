#!/usr/bin/env python

import asyncio
import signal
from websockets.asyncio.server import serve, ServerConnection
from websockets.exceptions import ConnectionClosed

global_websocket: ServerConnection | None = None

async def handler(websocket: ServerConnection):
    global global_websocket
    global_websocket = websocket
    print(f"Client connected from {websocket.remote_address}")
    async for message in websocket:
        print(f"Received message: {message}")
    print(f"Client disconnected from {websocket.remote_address}")


async def main():
    loop = asyncio.get_running_loop()
    stop = loop.create_future()
    loop.add_signal_handler(signal.SIGINT, stop.set_result, None)

    async with serve(handler, "0.0.0.0", 9999):
        print("Server started on ws://0.0.0.0:9999. Press Ctrl+C to exit.")
        await stop

if __name__ == "__main__":
    print("Starting server...")
    asyncio.run(main())
    print("Server shut down gracefully.")
