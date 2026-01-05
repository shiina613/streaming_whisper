import socket
import subprocess

# Thông số server
HOST = '127.0.0.1'  # hoặc IP server nếu chạy trên máy khác
PORT = 43001        # cổng server SimulStreaming

# Lệnh ffmpeg để lấy audio từ microphone
FFMPEG_CMD = [
    'ffmpeg',
    '-f', 'dshow',
    '-i', 'audio=Microphone Array (Realtek(R) Audio)',
    '-ac', '1',
    '-ar', '16000',
    '-f', 's16le',
    '-'
]

# Kết nối tới server
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    # Chạy ffmpeg và truyền dữ liệu audio tới server
    with subprocess.Popen(FFMPEG_CMD, stdout=subprocess.PIPE) as proc:
        try:
            while True:
                data = proc.stdout.read(4096)
                if not data:
                    break
                s.sendall(data)
        except KeyboardInterrupt:
            print('Dừng ghi âm.')
        finally:
            proc.terminate()
