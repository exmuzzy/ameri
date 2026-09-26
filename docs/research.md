# Исследование индустрии (Шаг 1)

> Дата исследования: 2026-09-26. Факты проверены веб-поиском. Часть первичных доступов (api-docs.deepseek.com, core.telegram.org, t.me) из среды исследования закрыта egress-прокси, поэтому некоторые факты взяты из выдачи поиска и вторичных источников. Такие места помечены «(вторичный источник)». **Перед реализацией перепроверить помеченное по первоисточнику.**

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
- `AskUserQuestion` в `-p` без хоста не работает. Значит, «вопрос пользователю» в Telegram должен реализовывать **бот**: конечный автомат, раунд за раундом, а агент возвращает структуру раунда.
- SIGTERM прерывает ход (код 143), и незавершённый ход не записывается. Таймауты делать через SIGINT или `interrupt()` в SDK.
- **Claude Agent SDK** (`pip install claude-agent-sdk`, `npm i @anthropic-ai/claude-agent-sdk`) — библиотека, запускающая бинарник Claude Code. Опции:
  - `cwd`, `allowed_tools`, `permission_mode`, `max_turns`, `resume`;
  - `setting_sources=["project"]` — загружать ли `.claude/` (skills, CLAUDE.md);
  - `skills=[...]` — allowlist скиллов;
  - `can_use_tool` — callback для решения по каждому инструменту;
  - hooks как Python-функции, собственные tools через in-process MCP, `agents` (subagents).
- Лицензия SDK — Commercial Terms Anthropic. Логин claude.ai в сторонних продуктах запрещён; нам это не мешает, авторизация идёт ключом DeepSeek.

**Вывод для проекта:** для Python-бота использовать **Claude Agent SDK (Python)** в отдельном воркере: `cwd` = рабочая копия репо харнеса, `setting_sources=["project"]`, явный allowlist tools и skills, `permission_mode="dontAsk"`. `session_id` хранить в БД, чтобы продолжать опрос через `resume`. Подтверждение и сохранение делает код бота, а не агент.

**Ссылки**
- https://code.claude.com/docs/en/headless
- https://code.claude.com/docs/en/agent-sdk/overview
- https://code.claude.com/docs/en/agent-sdk/skills
- https://code.claude.com/docs/en/permission-modes
- https://code.claude.com/docs/en/cli-reference

---

## 3. Telegram: группы, права, темы, файлы

**Создание группы**
- **Bot API не умеет создавать группы и супергруппы.** В changelog 9.x–10.x такого метода нет. Появились Managed Bots (бот создаёт ботов, 9.5–9.6) и bot-to-bot сообщения (10.0), но не создание чатов. (вторичный источник)
- Варианты:
  - (а) **Руководитель создаёт группу вручную и добавляет бота.** Бот получает update `my_chat_member` (смена его статуса member → administrator) и регистрирует `chat_id`.
  - (в) **Deep link** `https://t.me/<bot>?startgroup=<payload>&admin=<rights>`. Telegram показывает выбор группы и сразу запрашивает перечисленные права администратора (например `admin=delete_messages+pin_messages+manage_topics+invite_users`). `payload` приходит боту как `/start <payload>` в группе, и через него связывается одноразовый код руководителя. Группу всё равно создаёт человек, но это одна кнопка «создать группу» в диалоге выбора.
  - (б) **MTProto userbot** (Telethon/Pyrogram): `channels.CreateChannelRequest(megagroup=True)`, затем `InviteToChannelRequest` для бота и `EditAdminRequest` для прав бота. Минусы:
    - нужен отдельный пользовательский аккаунт (номер телефона) и хранение его сессии — это полный доступ к аккаунту;
    - риск флуд-лимитов и бана;
    - ещё один секрет, который надо защищать.
- Связанные updates: `my_chat_member` (статус бота) и `chat_member` (статусы участников, приходит только если бот админ и `chat_member` явно указан в `allowed_updates`).

**Privacy mode**
- По умолчанию включён. Бот в группе видит только команды `/cmd`, ответы на свои сообщения и упоминания.
- **Бот-администратор получает все сообщения независимо от privacy mode.** Альтернатива — `/setprivacy` → Disable в @BotFather.
- После смены режима бота нужно удалить из группы и добавить заново.

**Topics (форумы)**
- Супергруппа с включёнными темами. Методы `createForumTopic`, `editForumTopic`, `closeForumTopic` и т. д. требуют у бота права `can_manage_topics`. В сообщениях есть `message_thread_id` и `is_topic_message`.
- С Bot API 9.3 темы возможны и **в личном чате с ботом**: включаются в @BotFather (Threaded Mode), поле `User.has_topics_enabled`, работает `createForumTopic` в личке. Так в личке с руководителем можно держать отдельную тему «Настройка».
- Bot API 9.5: `sendMessageDraft` — потоковый вывод ответа (стриминг) во всех типах чатов.
- Актуальная версия Bot API — 10.x (10.0 от 2026-05-08, 10.1–10.2 далее).

**Файлы**
- Облачный Bot API: скачивание через `getFile` до **20 MB**, загрузка до **50 MB** (фото до 10 MB).
- **Local Bot API server** (`tdlib/telegram-bot-api`, Docker): загрузка до **2000 MB**, скачивание без лимита. Файл отдаётся локальным путём, webhook может работать по HTTP.

**Кнопки и голос**
- Inline keyboard: `callback_data` не длиннее **64 байт**, поэтому в кнопке передаётся короткий ID, а не текст ответа.
- Голосовые приходят как `voice` (OGG/Opus). Распознавание делается отдельно, например `faster-whisper` на CPU (русский поддерживается). У DeepSeek распознавания речи нет.

**Вывод для проекта:**
- Рекомендуется вариант **(а)+(в)**: deep link `startgroup` с `admin=`, привязка через одноразовый код, фиксация по `my_chat_member`. Вариант (б) отложить.
- Бот обязан быть администратором (privacy mode тогда не мешает) с `can_manage_topics`.
- Для файлов больше 20 MB поднять local Bot API server (можно в v1).
- Голос — через `faster-whisper`.

**Ссылки**
- https://core.telegram.org/bots/features (privacy mode, deep links)
- https://core.telegram.org/api/links (startgroup/admin)
- https://core.telegram.org/bots/api и https://core.telegram.org/bots/api-changelog
- https://core.telegram.org/bots/faq
- https://github.com/python-telegram-bot/python-telegram-bot/issues/5077 (Bot API 9.3, темы в личке)
- https://github.com/go-telegram/bot/issues/280 (Bot API 10.0)
- https://docs.aiogram.dev/en/latest/utils/deep_linking.html
- https://github.com/tdlib/telegram-bot-api
- https://bigmike.help/en/devops/local-telegram-bot-api-advantages-limitations-of-the-standard-api-and-set-eb4a3b/
- https://docs.telethon.dev/en/stable/examples/chats-and-channels.html
- https://tl.telethon.dev/methods/channels/create_channel.html
- https://github.com/stder/telegram-voice-to-text-bot (faster-whisper + Telegram)

---

## 4. Фреймворки Telegram-ботов

**Находки**
- **aiogram 3** (Python, asyncio; актуальная ветка 3.2x, документация 3.25):
  - встроенный FSM (`StatesGroup`) с хранилищами Memory, Redis, Mongo (motor/pymongo); ключ состояния настраивается (chat, user, thread);
  - Router, middleware, фильтры, утилиты deep linking;
  - webhook через aiohttp и long polling;
  - быстро поддерживает новые версии Bot API;
  - в русскоязычной среде самый распространённый.
- **python-telegram-bot 22.x** (Python):
  - `ConversationHandler` с `persistent=True`; persistence через Pickle/Dict или собственный `BasePersistence`, например на PostgreSQL;
  - webhook и polling;
  - на нём сделан готовый проект claude-code-telegram;
  - FSM менее гибкий: ConversationHandler удобен для линейных сценариев.
- **grammY** (TypeScript/Deno):
  - плагин `conversations` (сценарии как код) и `sessions` с адаптерами хранения (Redis, Postgres, файлы и др.);
  - хорошая документация;
  - удобен, если воркер на TS SDK.
- **Telegraf** (TS) — старше grammY, развивается медленнее.
- **Webhook vs long polling.** Webhook требует публичный HTTPS на портах 443/80/88/8443 и домен или IP с сертификатом. Polling проще, не нужны домен и входящие порты — достаточно для одного сервера и MVP. На webhook переходят при масштабировании. Несколько ботов в одном процессе поддерживают все фреймворки (aiogram: один Dispatcher, несколько Bot).

**Вывод для проекта:**
- Рекомендуется **aiogram 3 + Python Claude Agent SDK**: один язык, FSM с хранилищем в Redis или Postgres, поддержка нескольких ботов.
- Состояние опроса держать не только в FSM, но и в собственной таблице БД: дерево решений, ответы, `session_id`.
- Для MVP — long polling, webhook — опция.

**Ссылки**
- https://docs.aiogram.dev/en/latest/dispatcher/finite_state_machine/storages.html
- https://docs.python-telegram-bot.org/en/stable/telegram.ext.conversationhandler.html
- https://github.com/python-telegram-bot/python-telegram-bot/wiki/Making-your-bot-persistent
- https://grammy.dev/plugins/conversations
- https://grammy.dev/plugins/session

---

## 5. Альтернативные агентные рантаймы

**Находки**
- **OpenCode**:
  - нативный провайдер DeepSeek, без Anthropic-прослойки;
  - `opencode run -m deepseek/deepseek-v4-pro` — одноразовый запуск;
  - `opencode serve` — headless HTTP-сервер с OpenAPI и SDK `@opencode-ai/sdk`;
  - DeepSeek официально описывает интеграцию с ним.
- **Aider** — ориентирован на правку кода, для диалоговых сценариев с ботом подходит хуже.
- **Собственный цикл tool-calling** поверх DeepSeek API (OpenAI-формат) или LangGraph: полный контроль и нет зависимости от версии CLI, но skills, subagents и управление контекстом придётся писать самим.
- **DeepSeek Harness** — собственный агент DeepSeek (2026), молодой.

**Вывод для проекта:** Claude Code остаётся основной гипотезой: skills (`grilling`) в формате SKILL.md работают из коробки, есть SDK, sessions и hooks. Запасной вариант — OpenCode serve с тем же каталогом skills (формат SKILL.md он тоже читает) или собственный цикл. Вызов агента нужно спрятать за интерфейс `AgentRunner`, чтобы рантайм можно было заменить.

**Ссылки**
- https://api-docs.deepseek.com/quick_start/agent_integrations/opencode/
- https://open-code.ai/en/docs/providers
- https://deepakness.com/blog/deepseek-harness/

---

## 6. Самообучающийся харнес, память, eval

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
- Похожие open-source проекты:
  - **claude-code-telegram** (RichardAtCT): python-telegram-bot, Claude SDK с CLI-fallback, SQLite (сессии, аудит, стоимость), whitelist ID, изоляция каталогов, темы-проекты по YAML-реестру, лимит стоимости на пользователя;
  - **telegramcode**: одна тема на проект;
  - **OpenClaw** и **Hermes Agent** (NousResearch): персональные агенты с Telegram-каналом, памятью, skills и голосом.
  - Можно позаимствовать: YAML-реестр тем, лимиты стоимости, аудит в SQLite, «тема = контекст/сессия».

**Вывод для проекта:**
- Харнес строить как набор файлов в git: `harness/rules/*.md` с front-matter (scope, статус, автор, дата) и `CLAUDE.md`, который их собирает.
- Жизненный цикл правила: proposed → draft → approved → deprecated.
- Каждое изменение — коммит от имени бота с ID руководителя в trailer.
- Регрессию гонять через promptfoo (YAML, проще для не-разработчика) на `evals/`.
- В каждом ответе бота логировать SHA харнеса.

**Ссылки**
- https://www.morphllm.com/agents-md-guide
- https://devops.com/claude-code-adds-agents-md-fallback-cutting-instruction-file-sprawl/
- https://code.claude.com/docs/en/memory
- https://www.mindstudio.ai/blog/what-is-claude-dreaming-anthropic-agent-memory
- https://www.promptfoo.dev/docs/intro/
- https://deepeval.com/blog/llm-as-a-judge
- https://qaskills.sh/blog/promptfoo-vs-deepeval-2026
- https://github.com/RichardAtCT/claude-code-telegram
- https://github.com/olosegres/telegramcode
- https://hermes-agent.nousresearch.com/docs/user-guide/features/tts

---

## 7. RBAC, аудит, ПДн (152-ФЗ), хостинг

**Находки: 152-ФЗ**
- **Локализация (ч. 5 ст. 18).** При сборе ПДн граждан РФ запись, систематизация, накопление, хранение, уточнение и извлечение ведутся в БД на территории РФ. С **1 июля 2025** (23-ФЗ) прямо запрещён сбор с использованием баз данных за пределами РФ. Первичный сбор напрямую в зарубежную систему — административное правонарушение, штрафы выросли (закон 2024 г. об оборотных штрафах).
- **Трансграничная передача (ст. 12)** данных, ранее собранных в РФ-базу, допустима. Нужно уведомить Роскомнадзор до начала передачи. **Китай входит в перечень стран с «адекватной» защитой** (приказ РКН, с 2023-03-01), поэтому передача в DeepSeek идёт по упрощённому порядку: уведомление, без ожидания 10 рабочих дней. Также нужны:
  - согласие субъекта или иное правовое основание;
  - уведомление об обработке ПДн;
  - политика обработки;
  - модель угроз и меры защиты по ПП-1119.
- **Иностранные мессенджеры.** С 2023-03-01 (584-ФЗ) и с 2025-06-01 (41-ФЗ) части организаций запрещено использовать иностранные мессенджеры, включая Telegram, для передачи ПДн и платёжных документов и для общения с клиентами. Под запрет попадают госорганы, банки, некредитные финансовые организации, операторы связи, маркетплейсы, соцсети и др. Для обычной коммерческой компании прямого запрета нет, но ПДн клиентов в Telegram — зона риска.
- **Блокировка Telegram в РФ.** С 2026-02-10 РКН официально замедлял Telegram. С середины/конца марта 2026 провайдеры в РФ блокируют его: доступность без VPN в начале апреля около 5%. Пользователи работают через VPN или прокси. Сервер бота **в РФ** не сможет надёжно ходить к `api.telegram.org` без прокси.

**Находки: хостинг**
- DeepSeek API доступен и из РФ, и из-за рубежа.
- Telegram API надёжно доступен только с зарубежного сервера (или через прокси из РФ).
- Архитектурные варианты:
  - (1) всё на зарубежном VPS (Финляндия, Нидерланды, Казахстан и т. п.). Проще всего, но нарушает локализацию, если в системе ПДн граждан РФ;
  - (2) гибрид: «ПДн-ядро» (БД, файлы, репо истории) на VPS в РФ, а тонкий Telegram-шлюз и/или прокси — за рубежом. Первичная запись идёт в РФ-базу, агентный воркер тоже в РФ и ходит в DeepSeek (трансграничная передача с уведомлением);
  - (3) минимизация: в DeepSeek и в git-репо не отправлять ПДн (маскирование ФИО, телефонов, e-mail перед вызовом модели).
- Практика для RBAC и аудита:
  - гранты декларативно в YAML в git, где история — это аудит изменений прав;
  - плюс таблица `audit_event` в БД для runtime-событий: кто вызвал действие, отказ по правам;
  - проверка прав — в коде бота до вызова модели, а не в промпте.

**Вывод для проекта:**
- Решение по ПДн и хостингу **блокирующее** и принимается заказчиком в стартовом интервью.
- Если в переписке есть ПДн граждан РФ, то по умолчанию:
  - гибрид — хранилище в РФ, Telegram-шлюз или прокси вне РФ;
  - маскирование ПДн перед DeepSeek;
  - уведомления в РКН (обработка + трансграничная передача в КНР);
  - сырые сообщения и файлы в БД/S3 в РФ, в git — только конфиги и правила без ПДн.
- Если ПДн нет или компания не подпадает под ограничения (решает заказчик с юристом), допустим один зарубежный VPS.
- Всем участникам нужен рабочий доступ к Telegram (VPN) — это операционный риск проекта.

**Ссылки**
- https://normativ.kontur.ru/document?moduleId=1&documentId=501173 (152-ФЗ)
- https://www.birchlegal.ru/legal_alerts/2235/
- https://comply.ru/tpost/c43ezsout1-lokalizatsiya-i-transgranichnaya-peredac
- https://b-152.ru/hranenie-personalnyh-dannyh-za-granicej
- https://www.consultant.ru/document/cons_doc_LAW_426970/4ce70334b68f94e273fa4657be175cddca82dfe5/ (перечень «адекватных» стран)
- https://www.vedomosti.ru/technology/articles/2022/07/19/932115-kitai-indiyu-nadezhnih
- https://kontur.ru/talk/spravka/44920-pravda_chto_v_rossii_zapretili_inostr_messendzhery
- https://www.jivo.ru/blog/tutorials-jivo/zapret-inostrannyh-messendzherov.html
- https://www.rbc.ru/technology_and_media/10/02/2026/698afe729a79470c08a17b91
- https://meduza.io/en/feature/2026/03/17/russia-was-expected-to-block-telegram-in-april-it-appears-to-have-done-it-two-weeks-early
- https://explorer.ooni.org/findings/2026-russia-blocked-telegram
- https://www.osw.waw.pl/en/publikacje/analyses/2026-04-17/russia-blocks-telegram-and-cracks-down-vpns

---

## 8. Метод интервью: grilling

**Находки**
- В репозитории лежат skills Мэтта Покока: `.claude/skills/grilling`, `grill-me`, `grill-with-docs`, `domain-modeling`, `to-questionnaire` (лицензия — `LICENSE-mattpocock-skills`).
- `grilling`:
  - дерево решений и фронтир решений, чьи предпосылки уже закрыты;
  - раунды пронумерованных вопросов `❓ **Qn**` с рекомендацией `➡️`;
  - после ответов дерево пересчитывается.
- `domain-modeling` ведёт `CONTEXT.md` и ADR.

**Вывод для проекта:** grilling — выбранный метод и для стартового интервью, и для опроса руководителя в Telegram. В боте skill используется как «генератор раундов»: агент возвращает JSON раунда (`--json-schema` / structured output). Раунды, кнопки, приём ответов и **подтверждение сохранения** реализует FSM бота.

---

## Сводка ключевых рисков

1. Совместимость Claude Code ↔ DeepSeek ломается при обновлениях CLI (system-сообщения, metadata). Меры: pin версии, smoke-тест, при необходимости нормализующий прокси.
2. Изображения ломают сессию агента на DeepSeek. Меры: OCR/описание вне агента, в агент передаётся только текст.
3. Telegram заблокирован в РФ. Меры: сервер-шлюз вне РФ, у пользователей VPN.
4. 152-ФЗ: локализация первичного сбора ПДн плюс трансграничная передача в КНР (уведомление в РКН).
5. Лимит 20 MB на скачивание файлов в облачном Bot API. Мера: local Bot API server.
6. `total_cost_usd` Claude Code не отражает цены DeepSeek. Мера: считать стоимость самостоятельно по `usage`.
