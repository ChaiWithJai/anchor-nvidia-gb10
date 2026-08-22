"""OpenAI-compatible client for the local NVIDIA Nemotron vLLM service."""

import json
import os

import httpx

BASE_URL = os.environ.get("CARELINE_LLM_BASE_URL", "http://nemotron:8000/v1")
MODEL = os.environ.get(
    "CARELINE_LLM_MODEL", "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4"
)
TURN_MAX_TOKENS = int(os.environ.get("CARELINE_LLM_MAX_TOKENS", "120"))


async def chat(
    messages: list[dict],
    temperature: float = 0.6,
    strong: bool = False,
    reasoning_budget: int | None = None,
) -> str:
    del reasoning_budget
    max_tokens = 240 if strong else TURN_MAX_TOKENS
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    async with httpx.AsyncClient(timeout=180) as client:
        response = await client.post(f"{BASE_URL}/chat/completions", json=payload)
        response.raise_for_status()
    content = response.json()["choices"][0]["message"].get("content")
    if not content or not content.strip():
        raise RuntimeError("Nemotron returned an empty spoken response")
    return content.strip()


def _extract_json(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1].removeprefix("json").strip()
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        start, end = raw.find("{"), raw.rfind("}")
        if start >= 0 and end > start:
            try:
                value = json.loads(raw[start : end + 1])
                return value if isinstance(value, dict) else {}
            except json.JSONDecodeError:
                pass
    return {}


async def chat_json(messages: list[dict], strong: bool = False) -> dict:
    return _extract_json(await chat(messages, temperature=0.1, strong=strong))


async def ready() -> bool:
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            response = await client.get(f"{BASE_URL}/models")
            response.raise_for_status()
        return any(model.get("id") == MODEL for model in response.json().get("data", []))
    except (httpx.HTTPError, KeyError, TypeError):
        return False
