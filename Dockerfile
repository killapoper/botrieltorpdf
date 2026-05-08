FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

# Создание папки для данных
RUN mkdir -p data

# Создание папок для логов supervisor
RUN mkdir -p /var/log/supervisor

# Копирование конфига supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Открытие порта для веб-сервера
EXPOSE 5000

# Запуск supervisor (управляет ботом и веб-сервером)
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]    