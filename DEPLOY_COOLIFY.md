# 🚀 Деплой обновлений на VDS через Coolify

## Что нужно сделать

### 1. Обновить зависимости в requirements.txt
Уже сделано! Добавлены:
```
flask
flask-cors
requests
```

### 2. Git push изменений
```bash
cd "D:\desktop\Vse\Rielt bot pdf"

# Добавить все изменения
git add .

# Коммит
git commit -m "Добавлена интеграция с сайтом: web_server.py + обновлен bot.py"

# Пуш на сервер
git push origin main
```

### 3. В Coolify нужно:

#### A. Обновить переменные окружения (если нужно)
В настройках приложения добавьте (если их нет):
```
TELEGRAM_BOT_TOKEN=ваш_токен
ALLOWED_USER_IDS=1652676928,327895912
```

#### B. Запустить ДВА сервиса вместо одного

**ВАЖНО:** Теперь у вас 2 приложения:
1. **Telegram Bot** (bot.py) - уже работает
2. **Web Server** (web_server.py) - НОВЫЙ, нужно добавить

### 4. Настройка в Coolify

#### Вариант 1: Два отдельных сервиса (рекомендуется)

**Сервис 1: Telegram Bot**
- Команда запуска: `python bot.py`
- Порт: не нужен (работает через Telegram API)

**Сервис 2: Web Server**
- Команда запуска: `python web_server.py`
- Порт: `5000`
- Нужен публичный URL для приёма заявок с сайта

#### Вариант 2: Один сервис с supervisor/systemd

Создайте файл `start_production.sh`:
```bash
#!/bin/bash

# Запуск бота в фоне
python bot.py &

# Запуск веб-сервера
python web_server.py
```

Команда запуска в Coolify: `bash start_production.sh`

### 5. Получить публичный URL

После деплоя web_server.py в Coolify:
- Coolify даст вам URL типа: `https://your-app.coolify.io`
- Или настройте свой домен: `https://api.your-domain.com`

### 6. Обновить сайт

В файле `script.js` (строка 88) замените:
```javascript
// Было:
const response = await fetch('http://localhost:5000/api/submit-form', {

// Стало:
const response = await fetch('https://your-app.coolify.io/api/submit-form', {
```

## 📋 Пошаговая инструкция для Coolify

### Шаг 1: Пуш изменений
```bash
cd "D:\desktop\Vse\Rielt bot pdf"
git add .
git commit -m "Add web server integration"
git push
```

### Шаг 2: В Coolify создать новый сервис

1. Зайдите в Coolify
2. Нажмите "New Resource" → "Application"
3. Выберите ваш Git репозиторий
4. Настройте:
   - **Name**: `rielt-web-server`
   - **Build Pack**: Python
   - **Start Command**: `python web_server.py`
   - **Port**: `5000`
   - **Environment Variables**:
     ```
     TELEGRAM_BOT_TOKEN=ваш_токен
     ```

### Шаг 3: Настроить домен

В Coolify:
1. Перейдите в настройки сервиса
2. Domains → Add Domain
3. Укажите домен или используйте автоматический
4. Включите HTTPS (Let's Encrypt)

### Шаг 4: Деплой

1. Нажмите "Deploy"
2. Дождитесь завершения
3. Проверьте логи

### Шаг 5: Проверка

Откройте в браузере:
```
https://your-app.coolify.io/health
```

Должен вернуть: `{"status":"ok"}`

## 🔧 Альтернатива: Один Dockerfile

Если хотите запустить оба сервиса в одном контейнере, создайте:

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Установить supervisor для управления процессами
RUN apt-get update && apt-get install -y supervisor

# Конфиг supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
```

**supervisord.conf:**
```ini
[supervisord]
nodaemon=true

[program:bot]
command=python bot.py
autostart=true
autorestart=true
stderr_logfile=/var/log/bot.err.log
stdout_logfile=/var/log/bot.out.log

[program:webserver]
command=python web_server.py
autostart=true
autorestart=true
stderr_logfile=/var/log/webserver.err.log
stdout_logfile=/var/log/webserver.out.log
```

## ⚡ Быстрый вариант (без второго сервиса)

Если не хотите создавать второй сервис, можно запустить оба в одном:

**start.sh:**
```bash
#!/bin/bash
python bot.py &
python web_server.py
```

В Coolify:
- Start Command: `bash start.sh`
- Port: `5000`

## 🌐 Обновление сайта

После получения URL от Coolify, обновите `script.js`:

```javascript
const response = await fetch('https://ваш-url.coolify.io/api/submit-form', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify(formData)
});
```

## ✅ Чеклист деплоя

- [ ] Git push изменений (bot.py, web_server.py, requirements.txt)
- [ ] Coolify автоматически подтянет изменения
- [ ] Создать новый сервис для web_server.py (или обновить команду запуска)
- [ ] Настроить порт 5000
- [ ] Получить публичный URL
- [ ] Обновить script.js с новым URL
- [ ] Проверить /health endpoint
- [ ] Протестировать отправку заявки с сайта
- [ ] Проверить, что уведомления приходят в Telegram

## 🐛 Проверка логов

В Coolify:
```
Logs → View Logs
```

Должно быть:
```
* Running on http://0.0.0.0:5000
Квиз-бот запущен!
```

## 📞 Тест после деплоя

```bash
# Проверка health
curl https://your-app.coolify.io/health

# Тест отправки заявки
curl -X POST https://your-app.coolify.io/api/submit-form \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","phone":"+79991234567","type":"Купить новостройку"}'
```

Должны прийти уведомления в Telegram!
