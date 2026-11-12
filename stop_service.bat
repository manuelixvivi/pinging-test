@echo off
echo Menghentikan service background AI Browser Assistant (pythonw.exe)...
taskkill /F /FI "IMAGENAME eq pythonw.exe" 2>nul
echo Selesai. Service telah dihentikan.
timeout /t 3
