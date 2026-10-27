"""Клиент DeepSeek для свободных вопросов в Чате (OpenAI-совместимый API)."""

from __future__ import annotations

import httpx

from .store import Usage


class LlmError(RuntimeError):
    """Понятная пользователю ошибка обращения к модели."""


NO_CONNECTION_MESSAGE = "Нет связи с DeepSeek, попробуйте позже."

# Зависшее соединение (с сервера до DeepSeek оно рвётся на установке TLS) видно через 15 с;
# ответ модели ждём до 2 минут. Так же — для расчётки.
DEEPSEEK_TIMEOUT = httpx.Timeout(120, connect=15)


class NoConnectionError(LlmError):
    """DeepSeek не ответил: нет соединения, истекло ожидание или API перегружен (5xx, 429)."""

    def __init__(self) -> None:
        super().__init__(NO_CONNECTION_MESSAGE)


BAD_KEY_MESSAGE = (
    "Ключ DeepSeek на сервере содержит недопустимые символы (кириллицу или пробелы): "
    "Администратору нужно заново вставить ключ в «Настройках»."
)


def key_problem(api_key: str) -> str | None:
    """Почему ключ нельзя отправить в заголовке HTTP (там допустим только ASCII без пробелов)."""

    if not api_key:
        return "Ключ DeepSeek не задан: Администратору нужно добавить его на сервер."
    if not api_key.isascii() or any(ch.isspace() for ch in api_key):
        return BAD_KEY_MESSAGE
    return None


class DeepSeekChat:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout: httpx.Timeout = DEEPSEEK_TIMEOUT,
        http_client: httpx.Client | None = None,
    ) -> None:
        problem = key_problem(api_key)
        if problem:
            raise LlmError(problem)
        self.endpoint = base_url.rstrip("/") + "/chat/completions"
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self._http = http_client or httpx.Client()

    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> tuple[str, Usage]:
        """Ответ модели и расход токенов (включая попадания в кэш префикса DeepSeek)."""

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
                    timeout=self.timeout,
                )
            except httpx.HTTPError:
                continue
            if response.status_code >= 500 or response.status_code == 429:
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
        raise NoConnectionError()
