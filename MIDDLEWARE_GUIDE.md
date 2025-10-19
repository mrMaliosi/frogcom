# Руководство по Middleware FrogCom

## Обзор

FrogCom использует набор middleware для обеспечения безопасности, мониторинга, логирования и обработки запросов. Middleware выполняются в определенном порядке для обеспечения корректной работы приложения.

## Архитектура Middleware

```
Запрос → CORS → Логирование → Безопасность → Аутентификация → Rate Limit → Мониторинг → Обработка ошибок → Приложение
```

### Порядок выполнения

1. **ErrorHandlingMiddleware** - Обработка ошибок (первый)
2. **MonitoringMiddleware** - Мониторинг производительности
3. **RateLimitMiddleware** - Ограничение скорости запросов
4. **AuthenticationMiddleware** - Аутентификация (опционально)
5. **SecurityMiddleware** - Безопасность
6. **LoggingMiddleware** - Логирование
7. **CORSMiddleware** - CORS (последний)

## Описание Middleware

### 1. ErrorHandlingMiddleware

**Назначение**: Глобальная обработка ошибок и исключений.

**Функциональность**:
- Перехватывает все необработанные исключения
- Логирует ошибки с контекстом
- Возвращает стандартизированные ответы об ошибках
- Предотвращает утечку внутренней информации

**Пример ответа**:
```json
{
  "error": "Internal server error",
  "type": "ValueError",
  "message": "Invalid parameter value"
}
```

### 2. MonitoringMiddleware

**Назначение**: Мониторинг производительности и метрик.

**Функциональность**:
- Подсчет общего количества запросов
- Измерение времени обработки
- Вычисление среднего времени ответа
- Добавление метрик в заголовки ответов

**Заголовки ответов**:
- `X-Request-Count`: Общее количество запросов
- `X-Average-Response-Time`: Среднее время ответа

### 3. RateLimitMiddleware

**Назначение**: Ограничение скорости запросов для предотвращения злоупотреблений.

**Функциональность**:
- Ограничение количества запросов в минуту на IP
- Автоматическая очистка старых записей
- Настраиваемый лимит через конфигурацию

**Пример ответа при превышении лимита**:
```json
{
  "error": "Rate limit exceeded",
  "limit": 60,
  "window": "1 minute"
}
```

**Конфигурация**:
```bash
API_RATE_LIMIT=60  # запросов в минуту
```

### 4. AuthenticationMiddleware

**Назначение**: Базовая аутентификация через API ключ (опционально).

**Функциональность**:
- Проверка Bearer токена в заголовке Authorization
- Пропуск аутентификации для публичных эндпоинтов
- Настраиваемые пути для пропуска

**Публичные пути** (по умолчанию):
- `/health`
- `/docs`
- `/redoc`
- `/openapi.json`

**Пример использования**:
```bash
curl -H "Authorization: Bearer your-api-key" http://localhost:8888/generate
```

**Конфигурация**:
```bash
API_KEY=your-secret-api-key  # Если не указан, аутентификация отключена
```

### 5. SecurityMiddleware

**Назначение**: Базовая безопасность и защита от атак.

**Функциональность**:
- Проверка размера тела запроса
- Добавление security headers
- Защита от XSS, clickjacking и других атак

**Security Headers**:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`

**Конфигурация**:
```bash
API_MAX_REQUEST_SIZE=10485760  # 10MB в байтах
```

### 6. LoggingMiddleware

**Назначение**: Логирование всех HTTP запросов и ответов.

**Функциональность**:
- Логирование входящих запросов с полным контекстом
- Логирование ответов с метаданными
- Измерение времени обработки
- Добавление заголовка с временем обработки

**Логируемые данные**:
- URL и метод запроса
- Заголовки запроса
- Тело запроса (JSON и raw)
- IP адрес клиента
- User-Agent
- Время обработки
- Статус код ответа

**Заголовок ответа**:
- `X-Process-Time`: Время обработки в секундах

### 7. CORSMiddleware

**Назначение**: Обработка Cross-Origin Resource Sharing.

**Функциональность**:
- Настройка разрешенных origins
- Обработка preflight запросов
- Настройка разрешенных методов и заголовков

**Конфигурация**:
```bash
API_CORS_ORIGINS=http://localhost:3000,https://myapp.com  # Разделенные запятыми
```

## Конфигурация

### Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `API_RATE_LIMIT` | Лимит запросов в минуту | `60` |
| `API_KEY` | API ключ для аутентификации | `None` (отключено) |
| `API_MAX_REQUEST_SIZE` | Максимальный размер запроса (байты) | `10485760` (10MB) |
| `API_CORS_ORIGINS` | Разрешенные CORS origins | `*` |

### Пример .env файла

```bash
# Middleware настройки
API_RATE_LIMIT=100
API_KEY=your-secret-api-key-here
API_MAX_REQUEST_SIZE=20971520  # 20MB
API_CORS_ORIGINS=http://localhost:3000,https://myapp.com

# Основные настройки
API_HOST=0.0.0.0
API_PORT=8888
```

## Мониторинг и отладка

### Просмотр метрик

```bash
# Просмотр заголовков ответа для получения метрик
curl -I http://localhost:8888/health

# Ответ будет содержать:
# X-Request-Count: 42
# X-Average-Response-Time: 0.123
# X-Process-Time: 0.045
```

### Логирование

Все запросы логируются в `logs/requests.log`:

```json
{
  "url": "http://localhost:8888/generate",
  "method": "POST",
  "headers": {...},
  "client_ip": "127.0.0.1",
  "user_agent": "curl/7.68.0",
  "body_json": {...},
  "process_time": 0.123
}
```

### Отладка Rate Limiting

```bash
# Проверка текущих лимитов
for i in {1..65}; do
  curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8888/health
done

# После 60 запросов должен вернуться 429
```

## Безопасность

### Рекомендации для продакшена

1. **Настройте API ключ**:
   ```bash
   API_KEY=$(openssl rand -hex 32)
   ```

2. **Ограничьте CORS origins**:
   ```bash
   API_CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
   ```

3. **Настройте разумные лимиты**:
   ```bash
   API_RATE_LIMIT=30  # Для более строгого контроля
   ```

4. **Используйте HTTPS** в продакшене для работы HSTS заголовков

5. **Мониторьте логи** на предмет подозрительной активности

### Тестирование безопасности

```bash
# Тест на превышение размера запроса
curl -X POST http://localhost:8888/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "'$(python3 -c "print('x' * 11000000)")'"}'

# Должен вернуться 413 Payload Too Large

# Тест аутентификации
curl -X POST http://localhost:8888/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test"}'

# Если API_KEY настроен, должен вернуться 401 Unauthorized
```

## Кастомизация

### Добавление нового middleware

1. Создайте класс middleware в `api/middleware.py`:
```python
class CustomMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, custom_param: str):
        super().__init__(app)
        self.custom_param = custom_param
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Ваша логика
        response = await call_next(request)
        return response
```

2. Добавьте в `app.py`:
```python
app.add_middleware(CustomMiddleware, custom_param="value")
```

### Отключение middleware

Для отключения middleware закомментируйте соответствующую строку в `app.py`:

```python
# app.add_middleware(RateLimitMiddleware, requests_per_minute=config.api.rate_limit)
```

## Troubleshooting

### Проблема: 429 Too Many Requests
**Решение**: Увеличьте `API_RATE_LIMIT` или проверьте на спам-запросы

### Проблема: 413 Payload Too Large
**Решение**: Увеличьте `API_MAX_REQUEST_SIZE` или уменьшите размер запроса

### Проблема: 401 Unauthorized
**Решение**: Проверьте `API_KEY` или добавьте правильный заголовок Authorization

### Проблема: CORS ошибки
**Решение**: Настройте `API_CORS_ORIGINS` для вашего домена

### Проблема: Медленные ответы
**Решение**: Проверьте метрики в заголовках `X-Process-Time` и `X-Average-Response-Time`
