#!/bin/bash

# Скрипт для быстрой проверки работы системы после деплоя

echo "════════════════════════════════════════════════════════════"
echo "  ПРОВЕРКА РАБОТЫ СИСТЕМЫ"
echo "════════════════════════════════════════════════════════════"
echo ""

# URL вашего сервера
SERVER_URL="http://qfph8gc0yqqi8ssfe4ovr972.78.109.18.23.sslip.io"

echo "🔍 Шаг 1: Проверка health endpoint..."
HEALTH_RESPONSE=$(curl -s "$SERVER_URL/health")
echo "Ответ: $HEALTH_RESPONSE"

if [[ $HEALTH_RESPONSE == *"ok"* ]]; then
    echo "✅ Веб-сервер работает!"
else
    echo "❌ Веб-сервер не отвечает!"
    exit 1
fi

echo ""
echo "📤 Шаг 2: Отправка тестовой заявки..."

RESPONSE=$(curl -s -X POST "$SERVER_URL/api/submit-form" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Тест '$(date +%H:%M:%S)'",
    "phone": "+7 (999) 123-45-67",
    "type": "Купить новостройку"
  }')

echo "Ответ сервера: $RESPONSE"

if [[ $RESPONSE == *"success"* ]]; then
    echo "✅ Заявка отправлена успешно!"
    echo ""
    echo "📱 Проверьте Telegram:"
    echo "   - Админ 1652676928 должен получить уведомление"
    echo "   - Админ 327895912 должен получить уведомление"
    echo ""
    echo "📊 Проверьте логи в Coolify:"
    echo "   Должны быть записи о отправке сообщений"
else
    echo "❌ Ошибка при отправке заявки!"
    exit 1
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  ПРОВЕРКА ЗАВЕРШЕНА"
echo "════════════════════════════════════════════════════════════"
