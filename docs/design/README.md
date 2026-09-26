# Оформление ameri

## Решение и реализация

Направление — **инженерный журнал**: спокойный рабочий интерфейс, читаемая переписка, файлы и числа без декоративных экранов. Нативные светлая и тёмная темы заданы в [`.streamlit/config.toml`](../../.streamlit/config.toml); Streamlit ограничен версией `>=1.64,<2`. Там же настроены IBM Plex Sans и IBM Plex Mono через Google Fonts, радиусы, цвета фона, текста, границ и основного действия.

[`app/static/style.css`](../../app/static/style.css) дополняет нативные компоненты: типографика, отступы, границы, фокус, карточки метрик, чаты и адаптивные колонки до 767 px. Стили привязаны к `data-testid`; сообщения различаются по вложенным аватарам. Для длинного чата в [`app/views/chats.py`](../../app/views/chats.py) история помещена в `st.container(height=520, border=False)` с прокруткой; поле ввода остаётся нативным. Локальный CSS загружается через `apply_theme()`, статьи оформляются через `article()` в `app/views/theme.py`. Брендовые SVG используются локально.

**Важная особенность Streamlit 1.64:** на основном приложении нет гарантированно доступных CSS-переменных `--text-color`, `--background-color`, `--secondary-background-color` и `--primary-color`. Поэтому рабочий цвет заголовков — `currentColor`, подписи наследуют цвет, панели прозрачны; текст и поверхности фактически задаёт нативная тема Streamlit. `--am-line` смешивает `currentColor` с прозрачностью. В CSS остались ссылки на `--primary-color` и `--text-color` с запасными значениями: **их нельзя считать надёжным отражением выбранной темы**. Семантические CSS-токены не задают цвета штатных статусов: `st.error`, `st.warning`, `st.success` и другие оповещения раскрашивает сам Streamlit. `--am-success` используется только для левой обводки сообщения с пользовательским аватаром; другие семантические значения не являются реализованной палитрой статусов.

## Фактически настроенная палитра и контраст

| Параметр конфигурации | Светлая | Тёмная |
|---|---|---|
| Основное действие (`primaryColor`) | `#176F78` | `#70C5C8` |
| Фон (`backgroundColor`) | `#F6F8F7` | `#142328` |
| Вторичный фон (`secondaryBackgroundColor`) | `#EAF0F0` | `#243A40` |
| Текст (`textColor`) | `#21343A` | `#E4EDED` |
| Граница (`borderColor`) | `#CBD8D9` | `#415B61` |

Расчёт WCAG по sRGB: отношение `(Lсветлый + 0.05) / (Lтёмный + 0.05)`. Это **контраст указанных HEX-пар**, а не измерение всех итоговых цветов виджетов.

| Пара | Контраст |
|---|---:|
| Светлая: `#21343A` / `#F6F8F7` (текст / фон) | 12.18:1 |
| Тёмная: `#E4EDED` / `#142328` (текст / фон) | 13.56:1 |
| Светлая: `#FFFFFF` / `#176F78` (белый текст / основной цвет кнопки) | 5.86:1 |
| Тёмная: `#142328` / `#70C5C8` (тёмный текст / основной цвет кнопки) | 8.08:1 |

Последние две строки оценивают **возможные пары цветов кнопок**, но не подтверждают конкретный цвет текста, выбранный Streamlit в каждом состоянии. Для нативного красного оповещения здесь нет установленного HEX: его контраст не проверялся и не заявляется. На контраст реального виджета также влияют состояния и оформление Streamlit.

## Скриншоты «до / после»

Снимки сделаны на Streamlit 1.64: «до» — локальная исходная версия кода на той же 1.64, «после» — итоговый интерфейс; данные синтетические. Для **каждой** страницы ниже сохранены обе темы и обе ширины (1440 и 375 px), без исключений. В ячейках — прямые ссылки на соответствующую пару файлов.

| Страница | Светлая 1440 | Светлая 375 | Тёмная 1440 | Тёмная 375 |
|---|---|---|---|---|
| Вход | [до](before/login-light-1440.png) / [после](after/login-light-1440.png) | [до](before/login-light-375.png) / [после](after/login-light-375.png) | [до](before/login-dark-1440.png) / [после](after/login-dark-1440.png) | [до](before/login-dark-375.png) / [после](after/login-dark-375.png) |
| Менеджер: чаты | [до](before/manager-chats-light-1440.png) / [после](after/manager-chats-light-1440.png) | [до](before/manager-chats-light-375.png) / [после](after/manager-chats-light-375.png) | [до](before/manager-chats-dark-1440.png) / [после](after/manager-chats-dark-1440.png) | [до](before/manager-chats-dark-375.png) / [после](after/manager-chats-dark-375.png) |
| Менеджер: онбординг | [до](before/manager-onboarding-light-1440.png) / [после](after/manager-onboarding-light-1440.png) | [до](before/manager-onboarding-light-375.png) / [после](after/manager-onboarding-light-375.png) | [до](before/manager-onboarding-dark-1440.png) / [после](after/manager-onboarding-dark-1440.png) | [до](before/manager-onboarding-dark-375.png) / [после](after/manager-onboarding-dark-375.png) |
| Менеджер: примеры | [до](before/manager-examples-light-1440.png) / [после](after/manager-examples-light-1440.png) | [до](before/manager-examples-light-375.png) / [после](after/manager-examples-light-375.png) | [до](before/manager-examples-dark-1440.png) / [после](after/manager-examples-dark-1440.png) | [до](before/manager-examples-dark-375.png) / [после](after/manager-examples-dark-375.png) |
| Менеджер: инструкция | [до](before/manager-howto-light-1440.png) / [после](after/manager-howto-light-1440.png) | [до](before/manager-howto-light-375.png) / [после](after/manager-howto-light-375.png) | [до](before/manager-howto-dark-1440.png) / [после](after/manager-howto-dark-1440.png) | [до](before/manager-howto-dark-375.png) / [после](after/manager-howto-dark-375.png) |
| Менеджер: о проекте | [до](before/manager-about-light-1440.png) / [после](after/manager-about-light-1440.png) | [до](before/manager-about-light-375.png) / [после](after/manager-about-light-375.png) | [до](before/manager-about-dark-1440.png) / [после](after/manager-about-dark-1440.png) | [до](before/manager-about-dark-375.png) / [после](after/manager-about-dark-375.png) |
| Руководитель: чаты | [до](before/leader-chats-light-1440.png) / [после](after/leader-chats-light-1440.png) | [до](before/leader-chats-light-375.png) / [после](after/leader-chats-light-375.png) | [до](before/leader-chats-dark-1440.png) / [после](after/leader-chats-dark-1440.png) | [до](before/leader-chats-dark-375.png) / [после](after/leader-chats-dark-375.png) |
| Руководитель: качество | [до](before/leader-quality-light-1440.png) / [после](after/leader-quality-light-1440.png) | [до](before/leader-quality-light-375.png) / [после](after/leader-quality-light-375.png) | [до](before/leader-quality-dark-1440.png) / [после](after/leader-quality-dark-1440.png) | [до](before/leader-quality-dark-375.png) / [после](after/leader-quality-dark-375.png) |
| Руководитель: харнес | [до](before/leader-harness-light-1440.png) / [после](after/leader-harness-light-1440.png) | [до](before/leader-harness-light-375.png) / [после](after/leader-harness-light-375.png) | [до](before/leader-harness-dark-1440.png) / [после](after/leader-harness-dark-1440.png) | [до](before/leader-harness-dark-375.png) / [после](after/leader-harness-dark-375.png) |
| Руководитель: онбординг | [до](before/leader-onboarding-light-1440.png) / [после](after/leader-onboarding-light-1440.png) | [до](before/leader-onboarding-light-375.png) / [после](after/leader-onboarding-light-375.png) | [до](before/leader-onboarding-dark-1440.png) / [после](after/leader-onboarding-dark-1440.png) | [до](before/leader-onboarding-dark-375.png) / [после](after/leader-onboarding-dark-375.png) |
| Руководитель: примеры | [до](before/leader-examples-light-1440.png) / [после](after/leader-examples-light-1440.png) | [до](before/leader-examples-light-375.png) / [после](after/leader-examples-light-375.png) | [до](before/leader-examples-dark-1440.png) / [после](after/leader-examples-dark-1440.png) | [до](before/leader-examples-dark-375.png) / [после](after/leader-examples-dark-375.png) |
| Руководитель: инструкция | [до](before/leader-howto-light-1440.png) / [после](after/leader-howto-light-1440.png) | [до](before/leader-howto-light-375.png) / [после](after/leader-howto-light-375.png) | [до](before/leader-howto-dark-1440.png) / [после](after/leader-howto-dark-1440.png) | [до](before/leader-howto-dark-375.png) / [после](after/leader-howto-dark-375.png) |
| Руководитель: о проекте | [до](before/leader-about-light-1440.png) / [после](after/leader-about-light-1440.png) | [до](before/leader-about-light-375.png) / [после](after/leader-about-light-375.png) | [до](before/leader-about-dark-1440.png) / [после](after/leader-about-dark-1440.png) | [до](before/leader-about-dark-375.png) / [после](after/leader-about-dark-375.png) |
| Администратор: настройки | [до](before/admin-settings-light-1440.png) / [после](after/admin-settings-light-1440.png) | [до](before/admin-settings-light-375.png) / [после](after/admin-settings-light-375.png) | [до](before/admin-settings-dark-1440.png) / [после](after/admin-settings-dark-1440.png) | [до](before/admin-settings-dark-375.png) / [после](after/admin-settings-dark-375.png) |

Визуальная проверка проведена для всех этих страниц, тем и ширин; переполнение страниц не обнаружено. `pytest`: **19 тестов прошли**. Реальные вызовы DeepSeek и `duct_calc` не тестировались: ключей и рабочего прототипа для такой проверки не было. Снимки не подтверждают работу внешних интеграций или поведение на физическом телефоне.