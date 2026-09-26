# claude-ds

`claude-ds` — это Claude Code, подключённый к модели DeepSeek. Им пользуются разработчики. Руководитель работает в ZCode или Cursor.

## Установка

Добавьте функцию в `~/.zshenv` (или `~/.bashrc`):

```zsh
claude-ds() {
  ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic \
  ANTHROPIC_AUTH_TOKEN="$DEEPSEEK_API_KEY" \
  ANTHROPIC_MODEL="deepseek-flash[1m]" \
  ANTHROPIC_DEFAULT_OPUS_MODEL="deepseek-flash[1m]" \
  ANTHROPIC_DEFAULT_SONNET_MODEL="deepseek-flash[1m]" \
  ANTHROPIC_DEFAULT_HAIKU_MODEL="deepseek-flash" \
  CLAUDE_CODE_SUBAGENT_MODEL="deepseek-flash" \
  API_TIMEOUT_MS=3000000 \
  CLAUDE_CODE_EFFORT_LEVEL=max \
  CLAUDE_CODE_AUTO_COMPACT_WINDOW=786432 \
  CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 \
  command claude "$@"
}
```

Ключ DeepSeek задаётся отдельно в переменной окружения `DEEPSEEK_API_KEY` и в репозиторий не попадает.

## Что делает каждая переменная

| Переменная | Значение |
|---|---|
| `ANTHROPIC_BASE_URL` | Anthropic-совместимый endpoint DeepSeek |
| `ANTHROPIC_AUTH_TOKEN` | Ключ DeepSeek из `DEEPSEEK_API_KEY` |
| `ANTHROPIC_MODEL`, `ANTHROPIC_DEFAULT_OPUS_MODEL`, `ANTHROPIC_DEFAULT_SONNET_MODEL` | Основная модель — `deepseek-flash` с контекстом 1M (`[1m]`) |
| `ANTHROPIC_DEFAULT_HAIKU_MODEL`, `CLAUDE_CODE_SUBAGENT_MODEL` | `deepseek-flash` для лёгких задач и субагентов |
| `API_TIMEOUT_MS` | Таймаут запроса 50 минут: длинные ответы с `max` effort |
| `CLAUDE_CODE_EFFORT_LEVEL` | Максимальная глубина рассуждений |
| `CLAUDE_CODE_AUTO_COMPACT_WINDOW` | Автосжатие контекста при ~768K токенов, с запасом до лимита 1M |
| `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` | Не отправлять телеметрию и прочие необязательные запросы |

## Использование

```bash
cd ameri        # копия этого репозитория
claude-ds       # интерактивная сессия; скиллы из .claude/skills подхватываются
claude-ds -p "что делал Менеджер А сегодня?"   # разовый запрос без интерактива
```

## Известные ограничения

Подробности — в [исследовании](research.md), раздел 1.

- Версию Claude Code нужно закрепить и обновлять только после проверки на DeepSeek: отдельные версии ломали совместимость.
- Стоимость, которую показывает Claude Code, посчитана по ценам Anthropic и для DeepSeek неверна.
- Работу с изображениями через этот endpoint нужно проверить отдельно.
