# AGENTS.md — выжимка для агентов

Прочитай перед работой. Подробности для людей — в [README.md](README.md), термины — в [CONTEXT.md](CONTEXT.md), решения — в [docs/decisions.md](docs/decisions.md).

## Что это

**ameri** — сайт на Streamlit для менеджеров по полипропиленовым воздуховодам: чаты с ассистентом на DeepSeek, расчётка воздуховодов (XLSX) через прототип duct-calc, руководитель оценивает и исправляет ответы, из исправлений растёт **харнес** (`harness/`) в git.

- Прод: https://159-194-254-146.sslip.io — VPS Beget `ameri`, `ssh root@159.194.254.146` (только по ключу).
- Ветка: `master` (единственная рабочая; сервер собирается из неё).
- Язык интерфейса, статей, харнеса, docstring-ов и комментариев — русский. Сообщения коммитов — английский, повелительное наклонение.

## Главные инварианты

1. **Модель не калькулятор.** DeepSeek только разбирает текст и отвечает на вопросы; площади, массы и цены считает код. Никогда не заставляй модель считать деньги или геометрию.
2. **Утверждает человек.** Изменение харнеса попадает в `harness/` только после кнопки руководителя; это состояние `feedback.status = applied`, выставляемое кодом. Не делай путей, где модель сама применяет правило.
3. **Порядок промпта стабилен** (`harness.assistant_prompt`): промпт → правила → примеры, без дат и имён. Иначе ломается кэш префикса DeepSeek. Динамику (чат, файлы) — только после системного сообщения.
4. **Данные на сервере не трогаем.** `/srv/ameri/data` (база, файлы, пользователи, ключ) переживает любые обновления. Схему базы меняй только добавлением столбцов/таблиц в `store.SCHEMA` — `Store._migrate` добавит столбцы в существующую базу. Не переименовывай и не удаляй столбцы без явной миграции.
5. **Репозиторий публичный.** Никаких секретов, ключей, паролей, персональных данных клиентов (ФИО, телефоны, почты), цен и шаблона расчётки с ценами. Метаданные файлов-эталонов очищай (автор, компания). Прототип duct-calc в репозиторий не кладём.
6. **Права проверяет код** (`Access.can(user, grant)`) на каждом действии, не только скрытием кнопок.

## Карта кода

```
app/main.py                 вход, навигация по ролям (st.navigation)
app/views/chats.py          чаты: список, переписка, действия, 👍/👎, «Исправить и научить»
app/views/harness_page.py   «Харнес»: утверждение, правила, примеры, промпт, история, обновление
app/views/quality.py        «Качество»: статистика по менеджерам
app/views/onboarding.py     «Новому сотруднику»: чек-лист, учебный чат
app/views/admin.py          «Настройки»: обновление, ключ DeepSeek, пользователи
app/views/updates.py        кнопка «Обновить сайт» и статус обновления
app/views/about.py, howto.py  статьи из docs/site/*.md
src/ameri/store.py          SQLite: chats, messages, attachments, feedback, onboarding; миграции
src/ameri/auth.py           users.toml, scrypt-хэши, save_users
src/ameri/harness.py        access.yaml, assistant_prompt, HarnessRepo (правила, примеры, git commit/pull/push)
src/ameri/llm.py            DeepSeekChat: OpenAI-совместимый API, usage с cache hit, ретрай
src/ameri/actions.py        «Вопрос ассистенту», «Расчётка» (обёртка прототипа), .odt, подключение harness/duct_calc
src/ameri/settings.py       переменные окружения, ключ DeepSeek из env или data/secrets
harness/                    access.yaml, prompts/, rules/, examples/, duct_calc/, evals/
docs/site/*.md              статьи сайта (О проекте, Как работать, Примеры, Новому сотруднику)
deploy/                     Dockerfile, docker-compose.yml, Caddyfile, entrypoint.sh, bootstrap.sh,
                            beget.sh, autoupdate.sh, install-autoupdate.sh, shared-host/ (bishkek)
tools/run_evals.py          прогон эталонов; tools/hash_password.py — хэш пароля
tests/                      pytest
```

## Команды

```bash
pip install -r requirements.txt
python -m pytest -q                        # обязательно перед каждым push
streamlit run app/main.py                  # нужен var/users.toml (см. README → Локальная разработка)
DEEPSEEK_API_KEY=... AMERI_DUCT_CALC_DIR=/путь/к/duct-calc python tools/run_evals.py   # при изменении harness/duct_calc
```

Переменные: `AMERI_DATA_DIR` (по умолчанию `var/`), `AMERI_USERS_FILE`, `AMERI_HARNESS_DIR`, `AMERI_SITE_DIR`, `AMERI_DUCT_CALC_DIR`, `DEEPSEEK_API_KEY` / `DEEPSEEK_API_KEY_FILE`, `DEEPSEEK_MODEL` (`deepseek-flash`), `AMERI_GIT_URL`, `AMERI_GIT_PUSH`.

## Типовые задачи

- **Новое правило ассистента** — файл `harness/rules/<дата>-<slug>.md` с заголовком `### ...`, одно правило на файл. Проверь, нет ли похожего.
- **Правило разбора спецификаций** — абзац в `harness/duct_calc/parse_rules.md` (дописывается к промпту прототипа через `actions._install_harness`); ключевые слова покупных позиций, решёток, клапанов — `harness/duct_calc/params.yaml`. Затем `tools/run_evals.py` и сравнение с `--no-harness`.
- **Новый эталон** — `harness/evals/<имя>/spec.*` (реальный файл без персональных данных, метаданные очищены) + `expected.yaml` (`line`, `type`, `red`). См. `harness/evals/README.md`.
- **Новая статья** — `docs/site/<имя>.md` + `st.Page` в `app/main.py` (функция-рендер в `app/views/howto.py`).
- **Новое действие в чате** — функция в `src/ameri/actions.py`, возвращающая `ActionResult`; пункт в `app/views/chats.py` (`options`, `_run_action`); грант в `harness/access.yaml`.
- **Новая колонка в базе** — добавь в `SCHEMA` (с `DEFAULT`, если NOT NULL), миграция применится сама; тест на старую базу — по образцу `test_migration_adds_new_columns_and_keeps_data`.
- **Выкатить** — push в `master`, затем на сайте «Обновить сайт» (или `ssh root@159.194.254.146 /srv/ameri/app/deploy/autoupdate.sh`). Харнес и `docs/` — без перезапуска; код — пересборка с копией базы.

## Сервер (VPS Beget)

- `/srv/ameri/app` — клон репозитория; `/srv/ameri/data` — данные (база `ameri.sqlite3`, `files/`, `users.toml`, `secrets/`, `repo/` — рабочая копия харнеса и статей, из которой читает сайт); `/srv/ameri/duct-calc` — прототип; `/srv/ameri/backups` — копии.
- Docker compose проект `ameri` в `deploy/`: `app` (Streamlit :8501) + `caddy` (80/443). Обновление — systemd `ameri-update.path` → `deploy/autoupdate.sh`, журнал `/var/log/ameri-update.log`, статус `data/update-status.json`.
- Не запускай `docker system prune`, не удаляй `/srv/ameri/data`, не меняй файрвол без просьбы.

## Подводные камни

- Streamlit: `st.switch_page` теряет `st.query_params` — передавай `query_params=` аргументом.
- В контейнере нет `.git` в `/app`: харнес читается из `/data/repo` (клонирует `deploy/entrypoint.sh`). Коммиты харнеса с сайта идут туда; в GitHub — только с токеном (`AMERI_GIT_PUSH=1`).
- Прототип duct-calc подключается через `sys.path` и monkeypatch-ит `pipeline.build_system_prompt` и списки ключевых слов (`_install_harness`) — не правь его код из ameri, а расширяй через `harness/duct_calc/`.
- `.odt` прототип не читает: `actions.odt_text` превращает его в Markdown.
- DeepSeek: для ответов в чате `thinking` выключен (иначе `temperature` игнорируется); `total_cost` не считаем по ценам Anthropic — только по `usage`.
- Открытые вопросы по правилам расчёта — Q37–Q41 в `docs/decisions.md`; не реализуй их догадкой.
