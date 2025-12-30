import sounddevice as sd

def list_input_devices():
    # Lấy danh sách tất cả thiết bị
    devices = sd.query_devices()
    
    print(f"{'ID':<5} | {'Tên Thiết Bị Input':<45} | {'Số Kênh Thu'}")
    print("-" * 65)
    
    found = False
    for i, dev in enumerate(devices):
        # Chỉ lọc những thiết bị có số kênh đầu vào (max_input_channels) lớn hơn 0
        if dev['max_input_channels'] > 0:
            name = dev['name']
            channels = dev['max_input_channels']
            print(f"{i:<5} | {name:<45} | {channels}")
            found = True
            
    if not found:
        print("Không tìm thấy micro nào!")

if __name__ == "__main__":
    list_input_devices()