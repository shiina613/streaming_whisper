import sys
import platform
import pkg_resources

def check_versions():
    # Danh sách các thư viện từ requirements.txt của bạn
    libraries = [
        "torch", 
        "torchaudio", 
        "librosa", 
        "tqdm", 
        "tiktoken", 
        "triton"
    ]

    print("-" * 60)
    print(f"Hệ điều hành: {platform.system()} {platform.release()}")
    print(f"Phiên bản Python: {sys.version.split()[0]}")
    print("-" * 60)
    print(f"{'Thư viện':<20} | {'Phiên bản hiện tại':<20}")
    print("-" * 60)

    for lib in libraries:
        try:
            version = pkg_resources.get_distribution(lib).version
            print(f"{lib:<20} | {version:<20}")
        except pkg_resources.DistributionNotFound:
            print(f"{lib:<20} | Chưa được cài đặt")

    print("-" * 60)
    # Kiểm tra CUDA - Rất quan trọng cho Torch trên Linux
    try:
        import torch
        if torch.cuda.is_available():
            print(f"CUDA Khả dụng: Có (GPU: {torch.cuda.get_device_name(0)})")
            print(f"Phiên bản CUDA của Torch: {torch.version.cuda}")
        else:
            print("CUDA Khả dụng: Không (Đang dùng CPU)")
    except ImportError:
        pass
    print("-" * 60)

if __name__ == "__main__":
    check_versions()