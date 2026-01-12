# Simple WebSocket server for SimulStreaming
# Use: python websocket_server.py
#
# This server maintains a SINGLE TCP connection to SimulStreaming server
# All WebSocket clients share the same TCP connection.
# Each client gets its own ffmpeg process for audio decoding.

import asyncio
import websockets

SIMUL_HOST = '127.0.0.1'
SIMUL_PORT = 43001
MAX_RETRY = 5
RETRY_DELAY = 2  # seconds

# Global state - shared across all WebSocket clients
connected = set()
tcp_reader = None
tcp_writer = None
tcp_connected = False
broadcast_enabled = True  # Control whether to broadcast results
read_task = None  # Task đọc kết quả từ TCP


async def disconnect_tcp():
    """Đóng TCP connection hiện tại"""
    global tcp_reader, tcp_writer, tcp_connected, read_task
    
    tcp_connected = False
    
    # Cancel read task
    if read_task:
        read_task.cancel()
        try:
            await read_task
        except asyncio.CancelledError:
            pass
        read_task = None
    
    # Đóng TCP connection
    if tcp_writer:
        try:
            tcp_writer.close()
            await tcp_writer.wait_closed()
        except:
            pass
        tcp_writer = None
    tcp_reader = None
    print(f"[INFO] TCP connection closed")


async def connect_to_simulstreaming():
    """Kết nối TCP tới SimulStreaming server"""
    global tcp_reader, tcp_writer, tcp_connected, read_task
    
    for attempt in range(MAX_RETRY):
        try:
            tcp_reader, tcp_writer = await asyncio.open_connection(SIMUL_HOST, SIMUL_PORT)
            tcp_connected = True
            print(f"[OK] Connected to SimulStreaming server at {SIMUL_HOST}:{SIMUL_PORT}")
            
            # Khởi động task đọc kết quả từ TCP
            read_task = asyncio.create_task(read_tcp_results())
            return True
        except ConnectionRefusedError:
            print(f"[WARNING] SimulStreaming server not available, retrying ({attempt + 1}/{MAX_RETRY})...")
            await asyncio.sleep(RETRY_DELAY)
    
    print(f"[ERROR] Cannot connect to SimulStreaming server at {SIMUL_HOST}:{SIMUL_PORT}")
    print(f"[ERROR] Make sure 'python simulstreaming_whisper_server.py' is running first!")
    return False


async def reconnect_tcp():
    """Đóng và mở lại TCP connection để reset buffer tại SimulStreaming server"""
    global broadcast_enabled
    
    broadcast_enabled = False
    await disconnect_tcp()
    
    # Đợi một chút để SimulStreaming server cleanup
    await asyncio.sleep(0.3)
    
    success = await connect_to_simulstreaming()
    broadcast_enabled = True
    
    return success


async def create_ffmpeg_process():
    """Tạo ffmpeg process mới để decode webm -> PCM"""
    ffmpeg_cmd = [
        'ffmpeg',
        '-i', 'pipe:0',
        '-f', 's16le',
        '-acodec', 'pcm_s16le',
        '-ac', '1',
        '-ar', '16000',
        'pipe:1'
    ]
    proc = await asyncio.create_subprocess_exec(
        *ffmpeg_cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL
    )
    return proc


async def read_tcp_results():
    """Đọc kết quả text từ SimulStreaming server và broadcast tới WebSocket clients"""
    global tcp_reader, tcp_connected, broadcast_enabled
    
    while tcp_connected and tcp_reader:
        try:
            data = await asyncio.wait_for(tcp_reader.read(4096), timeout=0.1)
            if data and broadcast_enabled:
                text = data.decode(errors='ignore')
                await broadcast(text)
        except asyncio.TimeoutError:
            continue
        except Exception as e:
            print(f"[ERROR] read_tcp_results: {e}")
            break


async def broadcast(text):
    """Gửi text tới tất cả WebSocket clients"""
    if not connected:
        return
    
    # Copy set để tránh lỗi khi iterate
    clients = list(connected)
    for ws in clients:
        try:
            await ws.send(text)
        except:
            pass


async def handler(websocket):
    """Xử lý mỗi WebSocket connection từ browser"""
    global tcp_writer, tcp_connected, broadcast_enabled
    
    connected.add(websocket)
    print(f"[INFO] WebSocket client connected. Total clients: {len(connected)}")
    
    if not tcp_connected:
        await websocket.send("[ERROR] SimulStreaming server not connected. Please restart the server.")
        connected.discard(websocket)
        return
    
    ffmpeg_proc = None
    forward_task = None
    
    async def cleanup_ffmpeg():
        """Dọn dẹp ffmpeg process hiện tại"""
        nonlocal ffmpeg_proc, forward_task
        if forward_task:
            forward_task.cancel()
            try:
                await forward_task
            except asyncio.CancelledError:
                pass
            forward_task = None
        if ffmpeg_proc:
            ffmpeg_proc.kill()
            await ffmpeg_proc.wait()
            ffmpeg_proc = None
    
    async def start_ffmpeg():
        """Khởi động ffmpeg process mới"""
        nonlocal ffmpeg_proc, forward_task
        
        ffmpeg_proc = await create_ffmpeg_process()
        print(f"[INFO] ffmpeg process created")
        
        # Task forward PCM từ ffmpeg tới TCP
        async def forward_pcm():
            while ffmpeg_proc and not ffmpeg_proc.stdout.at_eof():
                try:
                    pcm = await ffmpeg_proc.stdout.read(4096)
                    if pcm and tcp_writer and not tcp_writer.is_closing():
                        tcp_writer.write(pcm)
                        await tcp_writer.drain()
                except Exception as e:
                    print(f"[ERROR] forward_pcm: {e}")
                    break
        
        forward_task = asyncio.create_task(forward_pcm())
    
    try:
        async for message in websocket:
            # Xử lý text message (commands)
            if isinstance(message, str):
                if message == "NEW_MEETING":
                    # Cuộc họp mới - reconnect TCP để reset buffer hoàn toàn tại SimulStreaming server
                    await cleanup_ffmpeg()
                    
                    # Reconnect TCP - tạo online processor mới tại SimulStreaming server
                    if await reconnect_tcp():
                        await start_ffmpeg()
                        print(f"[INFO] New meeting started - TCP reconnected, buffer fully cleared")
                    else:
                        await websocket.send("[ERROR] Cannot reconnect to SimulStreaming server")
                        print(f"[ERROR] Failed to reconnect TCP for new meeting")
                    
                elif message == "END_MEETING":
                    # Kết thúc cuộc họp - cleanup ffmpeg, giữ TCP connection
                    await cleanup_ffmpeg()
                    print(f"[INFO] Meeting ended")
                    
                elif message == "MIC_ON":
                    # Bật mic - đảm bảo có ffmpeg process
                    if not ffmpeg_proc or ffmpeg_proc.returncode is not None:
                        await start_ffmpeg()
                    print(f"[INFO] Mic ON")
                    
                # Không có MIC_OFF - khi tắt mic, audio tồn đọng vẫn được xử lý
                    
                continue
            
            # message là audio/webm chunk từ browser
            if ffmpeg_proc and ffmpeg_proc.stdin and not ffmpeg_proc.stdin.is_closing():
                try:
                    ffmpeg_proc.stdin.write(message)
                    await ffmpeg_proc.stdin.drain()
                except Exception as e:
                    print(f"[ERROR] Writing to ffmpeg: {e}")
                    
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        # Cleanup khi client disconnect
        await cleanup_ffmpeg()
        connected.discard(websocket)
        print(f"[INFO] WebSocket client disconnected. Total clients: {len(connected)}")


async def main():
    global tcp_connected
    
    # 1. Kết nối tới SimulStreaming server trước
    if not await connect_to_simulstreaming():
        print("[FATAL] Exiting because SimulStreaming server is not available.")
        return
    
    # 2. read_task đã được tạo trong connect_to_simulstreaming()
    
    # 3. Khởi động WebSocket server
    print("=" * 60)
    print("WebSocket server started on ws://127.0.0.1:8765")
    print("Open ccpage.html in browser to start")
    print("=" * 60)
    
    async with websockets.serve(handler, "127.0.0.1", 8765, max_size=10*1024*1024):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[INFO] Server stopped by user")