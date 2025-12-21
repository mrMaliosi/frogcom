# FrogCom - API для генерации текста с оркестрацией LLM

FrogCom - это REST API для генерации текста с использованием двух LLM моделей. Основная модель генерирует первичный ответ, а вторая модель анализирует его и предлагает уточнения для улучшения качества.

## Основные возможности

- **Оркестрация двух LLM**: Взаимодействие между основной и второй моделью для улучшения ответов
- **Настраиваемые раунды коммуникации**: Контроль количества итераций между моделями
- **Трассировка взаимодействий**: Подробное логирование всех шагов оркестрации
- **Гибкая конфигурация**: Настройка моделей и параметров через API или переменные окружения
- **OpenAI-совместимый API**: Стандартные эндпоинты для интеграции

## Быстрый старт

### Запуск

```bash
# Установка зависимостей
uv sync

# Запуск с настройками по умолчанию
uv run python -m frogcom.main

# Запуск с переменными окружения
LLM_MODEL=facebook/opt-350m COMMUNICATION_ROUNDS=2 uv run python -m frogcom.main
```

### Пример использования

```bash
# Генерация текста с оркестрацией
curl -X POST "http://localhost:8888/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Tell me about blockchain",
    "max_tokens": 400,
    "temperature": 0.7
  }'

curl -X POST "http://localhost:8888/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Создайте русскоязычную документацию для функции. Формат документации должен соответствовать стандартам языка программирования:\n- Python: Google-style Docstring.\n- Go: GoDoc.\n- Java: JavaDoc.\n- JavaScript: JSDoc.\n- C#: XML-документация.\n\nФункция:\n@Override\n    @Transactional\n    public OperatingSystemDTO editPartOfEntity(Integer operatingSystemId, OperatingSystemDTO operatingSystemDTO) {\n        var persistentOperatingSystem = getPersistentEntityById(operatingSystemId);\n        nullableMapper.map(operatingSystemDTO, persistentOperatingSystem);\n        operatingSystemRepository.save(persistentOperatingSystem);\n        return mapper.map(persistentOperatingSystem, OperatingSystemDTO.class);\n    }\n\nВыведите только готовый блок документации. Никаких пояснений, комментариев или дополнительного текста добавлять не нужно.",
    "max_tokens": 512
  }'


# Настройка оркестрации
curl -X PUT "http://localhost:8888/config/orchestration" \
  -H "Content-Type: application/json" \
  -d '{
    "communication_rounds": 2,
    "secondary_goal_prompt": "Найди неточности и предложи улучшения"
  }'
```

## Документация

- [Руководство разработчика](DEVELOPER_GUIDE.md) - Архитектура и стандарты разработки
- [Руководство по оркестрации](ORCHESTRATION_GUIDE.md) - Настройка и использование двух моделей
- [Руководство по Middleware](MIDDLEWARE_GUIDE.md) - Безопасность, мониторинг и обработка запросов
- [Примеры API](API_EXAMPLES.md) - Подробные примеры использования

## API Эндпоинты

- `POST /generate` - Генерация текста с оркестрацией
- `GET /health` - Проверка здоровья сервиса
- `GET /config/llm` - Получение конфигурации LLM
- `PUT /config/llm` - Обновление конфигурации LLM
- `GET /config/orchestration` - Получение конфигурации оркестрации
- `PUT /config/orchestration` - Обновление конфигурации оркестрации

## Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `LLM_MODEL` | Основная модель | `facebook/opt-125m` |
| `LLM_MODEL_SECONDARY` | Вторая модель | `facebook/opt-125m` |
| `COMMUNICATION_ROUNDS` | Количество раундов общения | `1` |
| `ORCHESTRATION_ENABLED` | Включить оркестрацию | `true` |
| `API_HOST` | Хост API | `0.0.0.0` |
| `API_PORT` | Порт API | `8888` |
| `API_RATE_LIMIT` | Лимит запросов в минуту | `60` |
| `API_KEY` | API ключ для аутентификации | `None` |
| `API_CORS_ORIGINS` | Разрешенные CORS origins | `*` |

## Разработка

### Проверка кода

```bash
# Проверка типов
uv run mypy src/frogcom/

# Проверка линтером
uv run ruff check src/frogcom/

# Автоформатирование
uv run ruff format src/frogcom/
```

### Структура проекта

```
src/frogcom/
├── api/                     # API слой
├── services/                # Сервисный слой
│   ├── llm_service.py       # Управление LLM
│   ├── orchestrator_service.py  # Оркестрация моделей
│   ├── tracing_service.py   # Трассировка взаимодействий
│   └── ...
├── config.py                # Конфигурация
├── models.py                # Pydantic модели
└── app.py                   # FastAPI приложение
```

## Логирование

- `logs/requests.log` - HTTP запросы и ответы
- `logs/orchestration_trace.log` - Трассировка взаимодействий между моделями

## Middleware

FrogCom включает набор middleware для обеспечения безопасности и мониторинга:

- **ErrorHandlingMiddleware** - Глобальная обработка ошибок
- **MonitoringMiddleware** - Мониторинг производительности
- **RateLimitMiddleware** - Ограничение скорости запросов
- **AuthenticationMiddleware** - Аутентификация через API ключ (опционально)
- **SecurityMiddleware** - Безопасность и защита от атак
- **LoggingMiddleware** - Логирование запросов и ответов
- **CORSMiddleware** - Обработка CORS

Подробнее см. [Руководство по Middleware](MIDDLEWARE_GUIDE.md).

## Лицензия

[Укажите лицензию]