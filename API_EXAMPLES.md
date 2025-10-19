# Примеры использования API FrogCom

## Запуск сервера

```bash
# Запуск с настройками по умолчанию
uv run python -m frogcom.main

# Запуск с переменными окружения
LLM_MODEL=facebook/opt-350m TEMPERATURE=0.8 uv run python -m frogcom.main
```

## Проверка здоровья сервиса

```bash
curl -X GET "http://localhost:8888/health"
```

Ответ:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "version": "0.1.0",
  "model_loaded": true
}
```

## Генерация текста

### Простой промпт

```bash
curl -X POST "http://localhost:8888/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Расскажи короткую историю про кота",
    "max_tokens": 100,
    "temperature": 0.7
  }'
```

### Промпт с сообщениями (чат формат)

```bash
curl -X POST "http://localhost:8888/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Привет! Как дела?"}
    ],
    "max_tokens": 50,
    "temperature": 0.8
  }'
```

### Сложный диалог

```bash
curl -X POST "http://localhost:8888/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "system", "content": "Ты - полезный ассистент"},
      {"role": "user", "content": "Объясни квантовую физику простыми словами"},
      {"role": "assistant", "content": "Квантовая физика изучает поведение частиц на очень маленьких масштабах..."},
      {"role": "user", "content": "А что такое суперпозиция?"}
    ],
    "max_tokens": 200,
    "temperature": 0.6
  }'
```

## Управление конфигурацией LLM

### Получение текущей конфигурации

```bash
curl -X GET "http://localhost:8888/config/llm"
```

Ответ:
```json
{
  "model_name": "facebook/opt-125m",
  "gpu_memory_utilization": 0.5,
  "disable_log_stats": false,
  "max_tokens": 256,
  "temperature": 0.7,
  "top_p": 0.9,
  "stop": null,
  "seed": null,
  "status": "loaded"
}
```

### Изменение параметров генерации

```bash
curl -X PUT "http://localhost:8888/config/llm" \
  -H "Content-Type: application/json" \
  -d '{
    "temperature": 0.9,
    "max_tokens": 512,
    "top_p": 0.95
  }'
```

### Смена модели

```bash
curl -X PUT "http://localhost:8888/config/llm" \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "facebook/opt-350m",
    "gpu_memory_utilization": 0.7
  }'
```

### Полная конфигурация

```bash
curl -X PUT "http://localhost:8888/config/llm" \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "facebook/opt-350m",
    "gpu_memory_utilization": 0.8,
    "disable_log_stats": false,
    "max_tokens": 1024,
    "temperature": 0.8,
    "top_p": 0.9,
    "stop": ["\n\n", "###"],
    "seed": 42
  }'
```

## Примеры с Python

### Использование requests

```python
import requests
import json

# Базовый URL
BASE_URL = "http://localhost:8888"

# Генерация текста
def generate_text(prompt, max_tokens=100, temperature=0.7):
    response = requests.post(
        f"{BASE_URL}/generate",
        json={
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
    )
    return response.json()

# Получение конфигурации
def get_config():
    response = requests.get(f"{BASE_URL}/config/llm")
    return response.json()

# Обновление конфигурации
def update_config(**kwargs):
    response = requests.put(
        f"{BASE_URL}/config/llm",
        json=kwargs
    )
    return response.json()

# Примеры использования
if __name__ == "__main__":
    # Генерируем текст
    result = generate_text("Напиши стихотворение про весну", max_tokens=150)
    print("Сгенерированный текст:", result["choices"][0]["message"]["content"])
    
    # Получаем текущую конфигурацию
    config = get_config()
    print("Текущая модель:", config["model_name"])
    
    # Меняем температуру
    update_config(temperature=0.9)
    print("Температура изменена на 0.9")
```

### Использование httpx (асинхронно)

```python
import httpx
import asyncio

async def generate_text_async(prompt, max_tokens=100):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8888/generate",
            json={
                "prompt": prompt,
                "max_tokens": max_tokens
            }
        )
        return response.json()

# Использование
async def main():
    result = await generate_text_async("Привет, мир!")
    print(result["choices"][0]["message"]["content"])

asyncio.run(main())
```

## Примеры с JavaScript/Node.js

```javascript
const axios = require('axios');

const BASE_URL = 'http://localhost:8888';

// Генерация текста
async function generateText(prompt, maxTokens = 100) {
    try {
        const response = await axios.post(`${BASE_URL}/generate`, {
            prompt: prompt,
            max_tokens: maxTokens,
            temperature: 0.7
        });
        return response.data;
    } catch (error) {
        console.error('Ошибка генерации:', error.response?.data || error.message);
    }
}

// Получение конфигурации
async function getConfig() {
    try {
        const response = await axios.get(`${BASE_URL}/config/llm`);
        return response.data;
    } catch (error) {
        console.error('Ошибка получения конфигурации:', error.response?.data || error.message);
    }
}

// Обновление конфигурации
async function updateConfig(config) {
    try {
        const response = await axios.put(`${BASE_URL}/config/llm`, config);
        return response.data;
    } catch (error) {
        console.error('Ошибка обновления конфигурации:', error.response?.data || error.message);
    }
}

// Пример использования
async function main() {
    // Генерируем текст
    const result = await generateText("Расскажи анекдот");
    console.log('Результат:', result.choices[0].message.content);
    
    // Получаем конфигурацию
    const config = await getConfig();
    console.log('Текущая модель:', config.model_name);
    
    // Меняем настройки
    await updateConfig({ temperature: 0.9, max_tokens: 200 });
    console.log('Конфигурация обновлена');
}

main();
```

## Обработка ошибок

### Пример ответа с ошибкой

```json
{
  "detail": "Ошибка генерации текста: LLM не инициализирован"
}
```

### Проверка статуса ответа

```python
import requests

def safe_generate(prompt):
    try:
        response = requests.post(
            "http://localhost:8888/generate",
            json={"prompt": prompt}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Ошибка {response.status_code}: {response.json()}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Ошибка сети: {e}")
        return None
```

## Мониторинг и логи

### Просмотр логов

```bash
# Просмотр последних запросов
tail -f logs/requests.log

# Поиск ошибок
grep "ERROR" logs/requests.log

# Поиск конкретного запроса
grep "frogcom-1234567890" logs/requests.log
```

### Структура лог файла

```
[2024-01-15T10:30:00.000Z] REQUEST
{
  "url": "http://localhost:8888/generate",
  "method": "POST",
  "headers": {...},
  "body_json": {
    "prompt": "Привет",
    "max_tokens": 50
  }
}
============================================================

[2024-01-15T10:30:01.000Z] RESPONSE
{
  "status_code": 200,
  "headers": {...}
}
============================================================
```

## Переменные окружения

### .env файл

```bash
# LLM настройки
LLM_MODEL=facebook/opt-350m
GPU_MEMORY_UTILIZATION=0.7
MAX_TOKENS=512
TEMPERATURE=0.8
TOP_P=0.9

# API настройки
API_HOST=0.0.0.0
API_PORT=8888
API_RELOAD=true

# Логирование
LOG_DIR=logs
MAX_LOG_SIZE_MB=100
LOG_TTL_DAYS=7
```

### Запуск с .env файлом

```bash
uv run --env-file .env python -m frogcom.main
```
