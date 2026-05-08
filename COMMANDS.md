# Быстрые команды для проверки

## 1. Проверка health
```bash
curl http://qfph8gc0yqqi8ssfe4ovr972.78.109.18.23.sslip.io/health
```
Ожидается: `{"status":"ok"}`

## 2. Отправка тестовой заявки
```bash
curl -X POST http://qfph8gc0yqqi8ssfe4ovr972.78.109.18.23.sslip.io/api/submit-form \
  -H "Content-Type: application/json" \
  -d '{"name":"Тест","phone":"+79991234567","type":"Купить новостройку"}'
```
Ожидается: `{"success":true,"message":"Заявка успешно отправлена!"}`

## 3. Git команды для деплоя
```bash
cd "D:\desktop\Vse\Rielt bot pdf"
git add .
git commit -m "Fix telegram notifications"
git push origin main
```

## 4. Проверка логов в Coolify
После отправки заявки ищите в логах:
- `Получен запрос на /api/submit-form`
- `✅ Заявка успешно отправлена админу`

## 5. Проверка в Telegram
Отправьте боту: `/admin`
Нажмите: `🌐 Заявки с сайта`

## Важные URL:
- Health: http://qfph8gc0yqqi8ssfe4ovr972.78.109.18.23.sslip.io/health
- API: http://qfph8gc0yqqi8ssfe4ovr972.78.109.18.23.sslip.io/api/submit-form
- Coolify: (ваш URL Coolify)

## Если не работает:
1. Проверьте переменные окружения в Coolify
2. Убедитесь, что оба админа запустили бота (/start)
3. Проверьте логи на ошибки
4. Убедитесь, что порт 5000 открыт
