import json
import os
import shutil
from datetime import datetime, timedelta
from fastapi import FastAPI, Request
from pydantic import BaseModel
from frogcom import generate_text

# === Настройки логов ===
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "requests.log")
os.makedirs(LOG_DIR, exist_ok=True)

MAX_LOG_SIZE_MB = 100
LOG_TTL_DAYS = 7


def log_to_file(data: dict):
    """Пишет логи в файл с отметкой времени"""
    if os.path.exists(LOG_FILE):
        size_mb = os.path.getsize(LOG_FILE) / (1024 * 1024)
        mtime = datetime.fromtimestamp(os.path.getmtime(LOG_FILE))
        if size_mb > MAX_LOG_SIZE_MB or datetime.now() - mtime > timedelta(days=LOG_TTL_DAYS):
            backup = LOG_FILE.replace(".log", f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
            shutil.move(LOG_FILE, backup)

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n[{datetime.now().isoformat()}]\n")
        f.write(json.dumps(data, ensure_ascii=False, indent=2))
        f.write("\n" + "=" * 60 + "\n")


# === FastAPI ===
app = FastAPI()


@app.middleware("http")
async def log_requests(request: Request, call_next):
    body = await request.body()
    log_data = {
        "url": str(request.url),
        "method": request.method,
        "headers": dict(request.headers),
        "body_raw": body.decode("utf-8", errors="replace"),
    }
    try:
        log_data["body_json"] = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        pass
    log_to_file(log_data)
    response = await call_next(request)
    return response


# === Вспомогательная функция: эвристика для извлечения промпта ===
def extract_prompt(data: dict) -> str:
    """
    Универсальный парсер промпта из JSON-запросов разных форматов:
    - {"prompt": "text"}
    - {"inputs": "..."}
    - {"messages": [{"role": "user", "content": "..."}]}
    """
    if "messages" in data:
        # OpenAI-style chat completion
        for msg in reversed(data["messages"]):
            if msg.get("role") == "user":
                return msg.get("content", "")
        return data["messages"][-1].get("content", "")

    if "prompt" in data:
        return data["prompt"]

    if "inputs" in data:
        return data["inputs"]

    # Fallback: взять всё тело как строку
    return json.dumps(data, ensure_ascii=False)


# === Модель запроса ===
class GenerateRequest(BaseModel):
    prompt: str | None = None
    messages: list[dict] | None = None
    max_tokens: int | None = None
    temperature: float | None = None
    top_p: float | None = None
    stop: list[str] | None = None
    seed: int | None = None


# === Основной эндпоинт ===
@app.post("/generate")
async def generate(request: Request, req: GenerateRequest):
    """
    Гибкий endpoint для взаимодействия с lm-evaluation-harness.
    Принимает разные форматы JSON и возвращает OpenAI-совместимый ответ.
    """
    try:
        data = req.dict(exclude_unset=True)
        prompt = extract_prompt(data)

        output = generate_text(
            [prompt],
            max_tokens=data.get("max_tokens", 256),
            temperature=data.get("temperature", 0.7),
            top_p=data.get("top_p", 0.9),
        )

        result = {
            "id": f"frogcom-{datetime.now().timestamp()}",
            "object": "text_completion",
            "created": int(datetime.now().timestamp()),
            "model": data.get("model", "my-local-llm"),
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": output[0]},
                    "finish_reason": "stop",
                }
            ],
        }

        log_to_file({"response": result})
        return result

    except Exception as e:
        err = {"error": str(e), "type": type(e).__name__}
        log_to_file({"error": err})
        return {"error": err}
