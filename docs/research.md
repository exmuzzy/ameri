# Исследование

> Дата исследования: 2026-09-26. Факты проверены веб-поиском. Часть первичных доступов (api-docs.deepseek.com) из среды исследования закрыта egress-прокси, поэтому некоторые факты взяты из выдачи поиска и вторичных источников. Такие места помечены «(вторичный источник)». **Перед реализацией перепроверить помеченное по первоисточнику.**

---

## 1. DeepSeek: Anthropic-совместимый API и запуск Claude Code

**Находки**
- Endpoint: `https://api.deepseek.com/anthropic`. Claude Code подключается через переменные окружения или `~/.claude/settings.json` (блок `env`). Официальная рекомендация DeepSeek:
  ```
  ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
  ANTHROPIC_AUTH_TOKEN=<DeepSeek API key>     # ANTHROPIC_API_KEY не задавать
  ANTHROPIC_MODEL=deepseek-v4-pro
  ANTHROPIC_DEFAULT_OPUS_MODEL=deepseek-v4-pro
  ANTHROPIC_DEFAULT_SONNET_MODEL=deepseek-v4-pro
  ANTHROPIC_DEFAULT_HAIKU_MODEL=deepseek-v4-flash   # теперь алиас → V4.1-Flash, новое имя deepseek-flash
  CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
  CLAUDE_CODE_EFFORT_LEVEL=max
  ```
- Модели (сентябрь 2026):
  - `deepseek-chat` и `deepseek-reasoner` выведены из эксплуатации 2026-07-24;
  - `deepseek-v4-flash` выведена 2026-09-10 и временно перенаправляется на V4.1-Flash. Новое имя — `deepseek-flash`;
  - актуальны `deepseek-flash` (V4.1-Flash) и `deepseek-v4-pro`. Контекст до 1M (в Claude Code встречается суффикс `[1m]`). (вторичный источник)
- Цены за 1M токенов (пиковые часы; в остальное время, включая выходные, цена вдвое ниже) (вторичный источник):
  - **Flash**: вход $0.30, cache hit $0.006, выход $1.20;
  - **V4-Pro**: вход $1.32, cache hit $0.044, выход $3.96 (действуют с 2026-08-16);
  - пик: 01:00–04:00 и 06:00–10:00 UTC, пн–пт. Это примерно 04:00–07:00 и 09:00–13:00 МСК, то есть часть рабочего дня.
- Ограничения совместимости (по таблице DeepSeek в пересказе вторичных источников):
  - **изображения**: с 21.08.2026 есть DeepSeek-V4-Flash-Vision-Exp, а `deepseek-flash` (V4.1 Flash) мультимодальный (JPEG/PNG/GIF/WebP, base64/URL/Files API, до 384 токенов на картинку) — https://api-docs.deepseek.com/news/news260821/ , https://api-docs.deepseek.com/guides/vision/ . Приём изображений через **Anthropic-совместимый** endpoint не подтверждён: раньше картинка в истории сессии Claude Code ломала все следующие запросы (ошибка 400). Проверить в первый день;
  - `cache_control` игнорируется. У DeepSeek своё автоматическое дисковое кэширование префиксов, поэтому cache hit всё равно возможен;
  - `mcp_servers` (серверный MCP) игнорируется, MCP-tool блоки не поддерживаются. Это касается только серверного MCP Anthropic. Локальные MCP-серверы Claude Code работают как обычные tools;
  - обычный tool use (tools, tool_choice) поддерживается. Именно на нём работают встроенные инструменты Claude Code (Read/Edit/Bash) и Skill tool;
  - поля deferred tools (`defer_loading`, `allowed_callers`) отклоняются.
- Известные проблемы Claude Code + DeepSeek:
  - Claude Code 2.1.154–2.1.156 шлёт `role: "system"` внутри `messages` (механизм из Opus 4.8). DeepSeek отвечает 400. Issue открыт; обходной путь — прокси, который сворачивает такие сообщения в top-level `system`;
  - `metadata.user_id` с «лишними» символами отклоняется (Claude Code 2.1.128+). Помогает нормализующий прокси (claude-tap);
  - `GET /v1/models` возвращает 404. Это безвредно;
  - вывод: **версию Claude Code надо закрепить (pin)** и обновлять только после smoke-теста на DeepSeek.
- Доступ из РФ: API доступен, проблема только в оплате (Visa/MC/МИР не принимаются, UnionPay ненадёжна). Оплата идёт через посредников или зарубежную карту.

**Вывод для проекта:** связка Claude Code + DeepSeek рабочая для текстовых агентных задач со skills и tools. Нужно:
- закрепить версию CLI;
- **изображения**: если Anthropic-совместимый endpoint принимает картинки для `deepseek-flash` — передавать их модели напрямую; если нет — вызывать vision через OpenAI-совместимый endpoint отдельным шагом и передавать агенту текстовое описание;
- заложить smoke-тест совместимости в CI и бюджет с учётом пиковых часов;
- использовать Flash по умолчанию, Pro — для опроса и генерации харнеса.

**Ссылки**
- https://api-docs.deepseek.com/guides/anthropic_api/
- https://api-docs.deepseek.com/quick_start/agent_integrations/claude_code/
- https://github.com/deepseek-ai/awesome-deepseek-agent/blob/main/docs/claude_code.md
- https://github.com/liaohch3/claude-tap/blob/main/docs/guides/deepseek-claude-code.md
- https://github.com/deepseek-ai/awesome-deepseek-integration/issues/639
- https://github.com/deepseek-ai/DeepSeek-V3/issues/1026 (изображения)
- https://github.com/Alishahryar1/free-claude-code/issues/359 (изображение «ломает» сессию)
- https://www.deepseek.com/en/news/deepseek-v4-1-flash/
- https://api-docs.deepseek.com/updates/
- https://benchlm.ai/deepseek/api-pricing
- https://www.nxcode.io/resources/news/deepseek-api-pricing-complete-guide-2026
- https://habr.com/ru/companies/oplatym/articles/1083764/ (оплата из РФ)

---

## 2. Claude Code headless и Claude Agent SDK

**Находки**
- `claude -p "<prompt>"` — неинтерактивный режим. Ключевые флаги:
  - `--output-format text|json|stream-json`. В JSON есть `result`, `session_id`, `usage`, `total_cost_usd` (оценка по ценам Anthropic, для DeepSeek она неверна — считать самим по `usage`);
  - `--json-schema '<schema>'` — структурированный ответ в поле `structured_output`. Удобно для опросника: следующий раунд вопросов возвращается как JSON;
  - `--resume <session_id>` / `--continue` — продолжение сессии. Сессия ищется по ID в любом проекте на машине; можно передать и путь к `.jsonl`-транскрипту;
  - `--allowedTools "Read,Edit,Bash(git diff *)"` — пред-одобрение по синтаксису правил, `--disallowedTools` — запрет;
  - `--permission-mode`: `dontAsk` запрещает всё, что потребовало бы подтверждения, и подходит для закрытых запусков; кроме него есть `acceptEdits` и `auto`. `--permission-prompts none` (v2.1.259+) убирает `AskUserQuestion` и запрещает всё неразрешённое;
  - `--append-system-prompt(-file)`, `--system-prompt`, `--max-turns`, `--settings`, `--mcp-config`, `--add-dir`.
- Загрузка контекста в `-p`:
  - без `--bare` загружается то же, что в интерактивном режиме: CLAUDE.md, `.claude/skills`, hooks, `.mcp.json` из cwd и `~/.claude`, **без диалога доверия**. Поэтому cwd агента должен быть доверенным каталогом;
  - `--bare` ничего не автообнаруживает (рекомендуется для скриптов, станет дефолтом). Skills подгружаются только из каталогов, переданных через `--add-dir`;
  - skills вызываются и моделью, и явно: `/skill-name` в тексте промпта.
- `AskUserQuestion` в `-p` без хоста не работает. Значит, раунды вопросов Руководителю реализует **приложение**: конечный автомат, раунд за раундом, а агент возвращает структуру раунда.
- SIGTERM прерывает ход (код 143), и незавершённый ход не записывается. Таймауты делать через SIGINT или `interrupt()` в SDK.
- **Claude Agent SDK** (`pip install claude-agent-sdk`, `npm i @anthropic-ai/claude-agent-sdk`) — библиотека, запускающая бинарник Claude Code. Опции:
  - `cwd`, `allowed_tools`, `permission_mode`, `max_turns`, `resume`;
  - `setting_sources=["project"]` — загружать ли `.claude/` (skills, CLAUDE.md);
  - `skills=[...]` — allowlist скиллов;
  - `can_use_tool` — callback для решения по каждому инструменту;
  - hooks как Python-функции, собственные tools через in-process MCP, `agents` (subagents).
- Лицензия SDK — Commercial Terms Anthropic. Логин claude.ai в сторонних продуктах запрещён; нам это не мешает, авторизация идёт ключом DeepSeek.

**Вывод для проекта:** если приложению понадобится агент, использовать **Claude Agent SDK (Python)** в отдельном воркере: `cwd` = рабочая копия репо харнеса, `setting_sources=["project"]`, явный allowlist tools и skills, `permission_mode="dontAsk"`. `session_id` хранить в БД, чтобы продолжать опрос через `resume`. Подтверждение и сохранение делает код приложения, а не агент.

**Ссылки**
- https://code.claude.com/docs/en/headless
- https://code.claude.com/docs/en/agent-sdk/overview
- https://code.claude.com/docs/en/agent-sdk/skills
- https://code.claude.com/docs/en/permission-modes
- https://code.claude.com/docs/en/cli-reference

---

## 3. Альтернативные агентные рантаймы

**Находки**
- **OpenCode**:
  - нативный провайдер DeepSeek, без Anthropic-прослойки;
  - `opencode run -m deepseek/deepseek-v4-pro` — одноразовый запуск;
  - `opencode serve` — headless HTTP-сервер с OpenAPI и SDK `@opencode-ai/sdk`;
  - DeepSeek официально описывает интеграцию с ним.
- **Aider** — ориентирован на правку кода, для диалоговых сценариев подходит хуже.
- **Собственный цикл tool-calling** поверх DeepSeek API (OpenAI-формат) или LangGraph: полный контроль и нет зависимости от версии CLI, но skills, subagents и управление контекстом придётся писать самим.
- **DeepSeek Harness** — собственный агент DeepSeek (2026), молодой.

**Вывод для проекта:** Claude Code остаётся основной гипотезой: skills (`grilling`) в формате SKILL.md работают из коробки, есть SDK, sessions и hooks. Запасной вариант — OpenCode serve с тем же каталогом skills (формат SKILL.md он тоже читает) или собственный цикл. Вызов агента нужно спрятать за интерфейс `AgentRunner`, чтобы рантайм можно было заменить.

**Ссылки**
- https://api-docs.deepseek.com/quick_start/agent_integrations/opencode/
- https://open-code.ai/en/docs/providers
- https://deepakness.com/blog/deepseek-harness/

---

## 4. Самообучающийся харнес, память, eval

**Находки**
- Rule files:
  - `CLAUDE.md` — иерархический: корень, подкаталоги, `~/.claude`;
  - `.claude/rules/` — правила, привязанные к путям;
  - `AGENTS.md` — кросс-инструментальный стандарт под Agentic AI Foundation (Linux Foundation). С Claude Code 2.1.277 он читается как fallback, если нет CLAUDE.md;
  - `.cursor/rules` — аналог у Cursor.
- Память в репо. Распространённый паттерн: журнал наблюдений (`MEMORY.md` или `learnings/`) → поднятие проверенного в правила (CLAUDE.md, rules) → повторяющееся в skills. У Anthropic есть «Dreaming» — консолидация памяти по прошлым сессиям. Есть готовые skills «self-improving-agent» (коррекция → правило/чек-лист).
- Human-in-the-loop: исправление человеком → черновик правила → ревью (коммит или PR) → eval → включение. Git даёт версионирование, diff, blame и откат бесплатно.
- Eval:
  - **promptfoo** — декларативный YAML, CLI, матрица сравнения, red-team (prompt injection), легко встроить в CI;
  - **DeepEval** — pytest-native, GEval (LLM-as-judge), DAG-метрики, удобен для регрессий;
  - LLM-as-judge ошибается, поэтому нужны и детерминированные проверки: наличие или отсутствие фраз, формат.
- Промпт-версионирование: промпты лежат как файлы в git, в логах ответа хранится хеш коммита харнеса. Так каждый ответ можно воспроизвести.
**Вывод для проекта:**
- Харнес строить как набор файлов в git: `harness/rules/*.md` с front-matter (scope, статус, автор, дата) и `CLAUDE.md`, который их собирает.
- Жизненный цикл правила: proposed → draft → approved → deprecated.
- Каждое изменение — коммит от имени приложения с логином Руководителя в trailer.
- Регрессию гонять через promptfoo (YAML, проще для не-разработчика) на `evals/`.
- В каждом запуске логировать SHA харнеса.

**Ссылки**
- https://www.morphllm.com/agents-md-guide
- https://devops.com/claude-code-adds-agents-md-fallback-cutting-instruction-file-sprawl/
- https://code.claude.com/docs/en/memory
- https://www.mindstudio.ai/blog/what-is-claude-dreaming-anthropic-agent-memory
- https://www.promptfoo.dev/docs/intro/
- https://deepeval.com/blog/llm-as-a-judge
- https://qaskills.sh/blog/promptfoo-vs-deepeval-2026

---

## 5. RBAC, аудит, ПДн (152-ФЗ)

**Находки: 152-ФЗ**
- **Локализация (ч. 5 ст. 18).** При сборе ПДн граждан РФ запись, систематизация, накопление, хранение, уточнение и извлечение ведутся в БД на территории РФ. С **1 июля 2025** (23-ФЗ) прямо запрещён сбор с использованием баз данных за пределами РФ.
- **Трансграничная передача (ст. 12)** данных, ранее собранных в РФ-базу, допустима после уведомления Роскомнадзора. Китай (DeepSeek) входит в перечень стран с «адекватной» защитой.
- Для проекта это не применяется: клиентских ПДн в приложении нет (ADR-0002). Если они появятся, решение пересматривается целиком.

**Находки: права и аудит**
- Гранты — декларативно в YAML в git: история коммитов — это аудит изменений прав.
- Таблица `audit_event` в БД — для runtime-событий: кто что запустил, отказы по правам.
- Проверка прав — в коде приложения до вызова модели, а не в промпте.

**Вывод для проекта:** Гранты в `harness/access.yaml`, runtime-аудит в БД, проверка прав в ядре приложения. Предупреждать при загрузке, если похоже на клиентские ПДн.

**Ссылки**
- https://normativ.kontur.ru/document?moduleId=1&documentId=501173 (152-ФЗ)
- https://www.birchlegal.ru/legal_alerts/2235/
- https://b-152.ru/hranenie-personalnyh-dannyh-za-granicej
- https://www.consultant.ru/document/cons_doc_LAW_426970/4ce70334b68f94e273fa4657be175cddca82dfe5/ (перечень «адекватных» стран)

---

## 6. Метод интервью: grilling

**Находки**
- В репозитории лежат skills Мэтта Покока: `.claude/skills/grilling`, `grill-me`, `grill-with-docs`, `domain-modeling`, `to-questionnaire` (лицензия — `LICENSE-mattpocock-skills`).
- `grilling`:
  - дерево решений и фронтир решений, чьи предпосылки уже закрыты;
  - раунды пронумерованных вопросов `❓ **Qn**` с рекомендацией `➡️`;
  - после ответов дерево пересчитывается.
- `domain-modeling` ведёт `CONTEXT.md` и ADR.

**Вывод для проекта:** grilling — выбранный метод и для стартового интервью, и для Опроса настройки в приложении. Модель используется как «генератор раундов» и возвращает JSON раунда (structured output). Раунды, выбор ответов и **подтверждение сохранения** реализует конечный автомат приложения.

---

## Сводка ключевых рисков

1. Совместимость Claude Code ↔ DeepSeek ломается при обновлениях CLI (system-сообщения, metadata). Меры: pin версии, smoke-тест.
2. Изображения через Anthropic-совместимый endpoint DeepSeek раньше ломали сессию агента. `deepseek-flash` мультимодальный; работу через этот endpoint проверить в первый день.
3. `total_cost_usd` Claude Code не отражает цены DeepSeek. Мера: считать стоимость самостоятельно по `usage`.
