@echo off
echo ========================================
echo Запуск Telegram бота и веб-сервера
echo ========================================
echo.

echo Установка зависимостей...
pip install -r requirements.txt
echo.

echo Запуск веб-сервера для приема заявок с сайта...
start "Web Server" cmd /k python web_server.py
timeout /t 3 /nobreak >nul

echo Запуск Telegram бота...
start "Telegram Bot" cmd /k python bot.py

echo.
echo ========================================
echo Оба сервиса запущены!
echo ========================================
echo Web Server: http://localhost:5000
echo Telegram Bot: Работает
echo.
echo Для остановки закройте оба окна
echo ========================================
pause
