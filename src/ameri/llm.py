"""Клиент DeepSeek для свободных вопросов в Чате (OpenAI-совместимый API)."""

from __future__ import annotations

import httpx


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

    def complete(self, messages: list[dict[str, str]], *, max_tokens: int = 8192) -> str:
        try:
            response = self._http.post(
                self.endpoint,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "stream": False,
                },
                timeout=self.timeout_seconds,
            )
        except httpx.HTTPError as error:
            raise LlmError(f"DeepSeek недоступен: {error.__class__.__name__}") from error
        if response.status_code != 200:
            raise LlmError(f"DeepSeek ответил ошибкой {response.status_code}")
        try:
            return response.json()["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError, ValueError) as error:
            raise LlmError("DeepSeek вернул ответ в неожиданном формате") from error
