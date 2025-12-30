# Simple WebSocket server for SimulStreaming
# Use: python websocket_server.py

import asyncio
import websockets
import socket
import subprocess

SIMUL_HOST = 'localhost'
SIMUL_PORT = 43001

connected = set()

async def handler(websocket):
    connected.add(websocket)
    tcp_writer = None
    tcp_reader = None
    ffmpeg_proc = None
    try:
        # Kết nối TCP tới SimulStreaming server
        loop = asyncio.get_event_loop()
        tcp_reader, tcp_writer = await asyncio.open_connection(SIMUL_HOST, SIMUL_PORT)
        # Khởi động ffmpeg để decode webm -> PCM
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', 'pipe:0',
            '-f', 's16le',
            '-acodec', 'pcm_s16le',
            '-ac', '1',
            '-ar', '16000',
            'pipe:1'
        ]
        ffmpeg_proc = await asyncio.create_subprocess_exec(
            *ffmpeg_cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL
        )

        async def forward_pcm_to_tcp():
            while True:
                pcm = await ffmpeg_proc.stdout.read(4096)
                if not pcm:
                    break
                tcp_writer.write(pcm)
                await tcp_writer.drain()

        forward_task = asyncio.create_task(forward_pcm_to_tcp())

        async for message in websocket:
            # message là audio/webm chunk từ client
            if isinstance(message, str):
                continue  # bỏ qua text message
            # Gửi chunk webm vào ffmpeg stdin
            ffmpeg_proc.stdin.write(message)
            await ffmpeg_proc.stdin.drain()
            # Đọc kết quả text từ SimulStreaming server (nếu có)
            try:
                data = await asyncio.wait_for(tcp_reader.read(4096), timeout=0.1)
                if data:
                    # Gửi kết quả text cho tất cả client
                    await broadcast(data.decode(errors='ignore'))
            except asyncio.TimeoutError:
                pass

        await forward_task
    finally:
        connected.remove(websocket)
        if ffmpeg_proc:
            ffmpeg_proc.kill()
        if tcp_writer:
            tcp_writer.close()
            await tcp_writer.wait_closed()

async def broadcast(text):
    for ws in connected:
        try:
            await ws.send(text)
        except:
            pass

async def main():
    async with websockets.serve(handler, "127.0.0.1", 8765, max_size=10*1024*1024):
        print("WebSocket server started on ws://127.0.0.1:8765")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())