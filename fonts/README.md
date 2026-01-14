# Font tiếng Việt cho PDF

Để hỗ trợ hiển thị tiếng Việt trong file PDF, hãy tải font DejaVu Sans:

1. Tải font từ: https://dejavu-fonts.github.io/Download.html
2. Giải nén và copy các file sau vào thư mục này:
   - DejaVuSans.ttf
   - DejaVuSans-Bold.ttf

Hoặc sử dụng PowerShell để tải tự động:
```powershell
# Tải và giải nén font DejaVu
Invoke-WebRequest -Uri "https://github.com/dejavu-fonts/dejavu-fonts/releases/download/version_2_37/dejavu-fonts-ttf-2.37.zip" -OutFile "dejavu.zip"
Expand-Archive -Path "dejavu.zip" -DestinationPath "." -Force
Copy-Item "dejavu-fonts-ttf-2.37/ttf/DejaVuSans.ttf" "."
Copy-Item "dejavu-fonts-ttf-2.37/ttf/DejaVuSans-Bold.ttf" "."
Remove-Item "dejavu.zip"
Remove-Item "dejavu-fonts-ttf-2.37" -Recurse
```
