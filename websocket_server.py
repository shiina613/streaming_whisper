# Simple WebSocket server for SimulStreaming
# Use: python websocket_server.py

import asyncio
import websockets

connected = set()

async def handler(websocket):
    connected.add(websocket)
    try:
        async for message in websocket:
            # Khi nhận được message từ client (simul_whisper), broadcast cho các web client
            await broadcast(message)
    finally:
        connected.remove(websocket)

async def broadcast(text):
    for ws in connected:
        try:
            await ws.send(text)
        except:
            pass

async def main():
    async with websockets.serve(handler, "127.0.0.1", 8765):
        print("WebSocket server started on ws://127.0.0.1:8765")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())