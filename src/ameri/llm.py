"""Клиент DeepSeek для свободных вопросов в Чате (OpenAI-совместимый API)."""

from __future__ import annotations

import httpx

from .store import Usage


class LlmError(RuntimeError):
    """Понятная пользователю ошибка обращения к модели."""


class DeepSeekChat:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float = 180,
        http_client: httpx.Client | None = None,
    ) -> None:
        if not api_key:
            raise LlmError("Ключ DeepSeek не задан: Администратору нужно добавить его на сервер.")
        self.endpoint = base_url.rstrip("/") + "/chat/completions"
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self._http = http_client or httpx.Client()

    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> tuple[str, Usage]:
        """Ответ модели и расход токенов (включая попадания в кэш префикса DeepSeek)."""

        last_error: Exception | None = None
        for _attempt in range(2):  # одна повторная попытка при сетевом сбое или 5xx
            try:
                response = self._http.post(
                    self.endpoint,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.model,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "stream": False,
                        # В режиме рассуждений temperature игнорируется; для ответов в Чате он не нужен.
                        "thinking": {"type": "disabled"},
                    },
                    timeout=self.timeout_seconds,
                )
            except httpx.HTTPError as error:
                last_error = LlmError(f"DeepSeek недоступен: {error.__class__.__name__}")
                continue
            if response.status_code >= 500 or response.status_code == 429:
                last_error = LlmError(f"DeepSeek временно недоступен ({response.status_code})")
                continue
            if response.status_code != 200:
                raise LlmError(f"DeepSeek ответил ошибкой {response.status_code}")
            try:
                data = response.json()
                text = data["choices"][0]["message"]["content"].strip()
            except (KeyError, IndexError, TypeError, ValueError) as error:
                raise LlmError("DeepSeek вернул ответ в неожиданном формате") from error
            usage = data.get("usage") or {}
            return text, Usage(
                prompt_tokens=int(usage.get("prompt_tokens") or 0),
                completion_tokens=int(usage.get("completion_tokens") or 0),
                cache_hit_tokens=int(usage.get("prompt_cache_hit_tokens") or 0),
            )
        raise last_error or LlmError("DeepSeek недоступен")
