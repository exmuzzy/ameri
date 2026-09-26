# Хостинг: выбор сервера в РФ

> **Устарело.** Выбран существующий сервер `bishkek` (Q4 в docs/decisions.md), рекомендация Timeweb отменена. Файл оставлен как история исследования.

Дата исследования: 2026-09-26. Основание: [ADR-0001](adr/0001-pd-stored-in-rf-masked-for-llm.md) (ПД граждан РФ хранятся в РФ, в модель уходят замаскированными), бюджет до 2 000 ₽/мес на сервер (Q11).

> Как собирались данные. Сайты провайдеров и большинство русскоязычных СМИ из среды исследования были недоступны: исходящий прокси их блокирует. Поэтому цены и факты взяты из поисковой выдачи (сниппеты страниц провайдеров, агрегаторов тарифов, Хабра, vc.ru) и из доступных страниц GitHub. Всё, что помечено «проверить», нужно сверить в калькуляторе провайдера перед покупкой.

## 1. Telegram из РФ: состояние на сентябрь 2026

| Когда | Что произошло | Источник |
|---|---|---|
| авг 2025 | РКН ограничивает звонки в Telegram | [kontur.ru](https://kontur.ru/talk/spravka/83517-zamedlenie_telegram_v_rossii) |
| 9–10 фев 2026 | РКН официально подтвердил замедление Telegram по всей стране | [fontanka.ru](https://www.fontanka.ru/2026/03/19/76319254/), [bitrix24](https://www.bitrix24.ru/journal/blokirovka-telegram/) |
| ~16–19 мар 2026 | ТСПУ начали отбрасывать пакеты к `api.telegram.org`, в том числе из ЦОДов (Selectel, Reg.ru и др.). Боты на российских VPS перестали работать. Timeweb ответил: «проблема у большинства провайдеров» | [GitHub zapret#11242](https://github.com/Flowseal/zapret-discord-youtube/issues/11242) (16.03.2026), [vc.ru](https://vc.ru/id5779154/2795944-blokirovka-telegram-api-v-rossii), [PressAff 19.03.2026](https://pressaff.com/tg-news/ru-hostingi-nachali-rezat-vps-s-dostupom-k-telegram-api-nekotorye-rossijskie-hosting-provajdery/), [AffTimes](https://afftimes.com/news/oshibka-504-i-taimauty/) |
| 10 апр 2026 | Уровень блокировки Telegram около 95–100% | [The Moscow Times](https://ru.themoscowtimes.com/2026/04/10/telegram-polnostyu-zablokirovali-vrossii-a192278) |
| апр 2026 | Поправки «Антифрод 2.0»: хостеры обязаны выявлять операторов VPN и отказывать им в обслуживании | [Meduza](https://meduza.io/news/2026/04/17/rossiyskim-provayderam-hostinga-sobirayutsya-zapretit-predostavlyat-vychislitelnye-moschnosti-vladeltsam-vpn), [Коммерсантъ](https://www.kommersant.ru/doc/8590872), [Теплица](https://te-st.org/2026/05/12/hostingrules/) |
| 24 сен 2026 | Timeweb, зона nsk-1: `curl -4 https://api.telegram.org` даёт таймаут, «в РФ IPv4 до Telegram заблокирован». На прошлом хосте бот работал через **IPv6 + NAT66**. В nsk-1 IPv6 нет | [GitHub yummy#87](https://github.com/MelnikovTimofey/yummy/issues/87) |
| 25 сен 2026 | Сбои Telegram в регионах продолжаются | [hi-tech.mail.ru](https://hi-tech.mail.ru/news/145611-chto-segodnya-s-telegram/) |

**Итог.** С российского IPv4 Bot API сейчас недоступен. По свежим отчётам разработчиков, по **IPv6** он пока работает. Это не гарантия: блокировку IPv6 могут включить в любой момент. Замедление Cloudflare (с 9 июня 2025 года пропускаются только первые 16 КБ) на Telegram не влияет, а на `api.deepseek.com` может повлиять (см. раздел 2). Источник: [xakep.ru](https://xakep.ru/2025/06/27/cloudflare-analysis/).

### Обходные пути для бота

| Вариант | Как работает | Плюсы | Минусы и юридические риски |
|---|---|---|---|
| **A. IPv6 напрямую** | На VPS в РФ включён публичный IPv6, aiogram ходит к `api.telegram.org` по IPv6 | Бесплатно, без посредников, ПД не проходят через наши серверы за рубежом | Зависит от того, что IPv6 не блокируют. Нужна зона провайдера с IPv6 |
| **B. Релей за рубежом** | Маленький VPS за рубежом (например, Timeweb ams-1 или fra-1, ~200–400 ₽). Без расшифровки TLS: TCP/SNI-passthrough или SOCKS5 по ключу. Бот указывает прокси в `AiohttpSession(proxy=...)` | Работает при любой блокировке | ПД транзитом идут через зарубежный узел. Если релей расшифровывает TLS (reverse proxy, Caddy), это наша обработка ПД за рубежом: не делать так. Открытый релей можно использовать с чужими токенами, закрывать ключом ([Хабр](https://habr.com/ru/sandbox/288226/)). Российский хостер может принять туннель за VPN (поправки «Антифрод 2.0») |
| **C. Local Bot API server** (`tdlib/telegram-bot-api`) | Свой Bot API на сервере, он ходит к ДЦ Telegram по MTProto | Снимает лимиты на размер файлов | ДЦ Telegram тоже блокируются. Без IPv6 или прокси не поможет |
| **D. Фронт бота за рубежом, ПД в РФ** | Бот работает за рубежом и пишет в БД в РФ | Нет проблем с доступом | **Не подходит.** По ч. 5 ст. 18 152-ФЗ первичная запись и хранение ПД должны быть в БД на территории РФ. Обработка на зарубежном фронте нарушает локализацию или требует сложной схемы «запись в РФ → уже потом за рубеж» |

**Юридический фон.**
- Telegram сам находится за рубежом. Сообщения клиентов в любом случае проходят через его серверы, а юрисдикция Telegram не входит в число «адекватных». Нужно уведомить РКН о трансграничной передаче (ст. 12 152-ФЗ) и включить её в согласие и политику ([law.ru](https://www.law.ru/article/25841-chto-takoe-transgranichnaya-peredacha-personalnyh-dannyh), [lukash.partners](https://lukash.partners/article/personalnie-dannie-telegram)).
- ⚠️ **Проверить юристом.** 41-ФЗ с 1 июня 2025 года запрещает госорганам, банкам, операторам связи, маркетплейсам и др. общаться с клиентами через иностранные мессенджеры. Блоги ([sostav](https://www.sostav.ru/blogs/282100/63047), [itforprof](https://itforprof.com/messendzhery/zapret-messendzherov-2026/)) пишут, что **с сентября 2026 года запрет распространяется на всех операторов ПД**. В первоисточнике (тексте закона) это подтвердить не удалось. Если это так, общение с клиентами через Telegram-бота ставится под вопрос независимо от хостинга. Для внутреннего бота менеджеров (сотрудники, а не клиенты) риск ниже, но тоже требует оценки.

## 2. DeepSeek из РФ

| Вопрос | Факт | Источник |
|---|---|---|
| Доступность `api.deepseek.com` | Нестабильна. В апреле 2025 года IP (Cloudflare, 104.18.26/27.90) попадали в реестр из-за соседства с казино. В мае 2026 года `chat.deepseek.com` лежал из РФ больше 12 часов. В 2026 году DeepSeek в основном доступен без VPN, но страдает от «сопутствующего ущерба» при давлении на Cloudflare | [GitHub V3#840](https://github.com/deepseek-ai/DeepSeek-V3/issues/840), [GitHub R1#846](https://github.com/deepseek-ai/DeepSeek-R1/issues/846), [securitylab](https://www.securitylab.ru/blog/personal/Neurosinaps/361664.php) |
| Оплата | Российские карты (Visa, MC, Мир) **не проходят**. Варианты: зарубежная или виртуальная карта, посредники по пополнению | [РБК Компании](https://companies.rbc.ru/news/0Su2q3GJoP/kak-oplatit-deepseek-api-iz-rossii-v-2026-godu-popolnenie-balansa/), [vc.ru](https://vc.ru/services/2983098-oplata-deepseek-api-iz-rossii) |
| Модели и формат | `deepseek-v4-flash`, `deepseek-v4-pro`. API совместимы с OpenAI и Anthropic. Для Claude Code: `ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic` | [DeepSeek docs: Anthropic API](https://api-docs.deepseek.com/guides/anthropic_api/), [Claude Code integration](https://api-docs.deepseek.com/quick_start/agent_integrations/claude_code/) |
| Агрегаторы в РФ (оплата в ₽, СБП, документы для юрлиц) | Polza.ai, ProxyAPI, provod.ai. Формат OpenAI-совместимый. Данные всё равно уходят к DeepSeek за рубеж | [polza.ai](https://polza.ai/blog/rossiyskiy-api-dlya-neyrosetey-bez-vpn-polnyy-gayd-2026), [proxyapi.ru](https://proxyapi.ru/), [provod.ai](https://provod.ai/ru/blog/deepseek-v-rossii) |

**DeepSeek на российских облаках (данные остаются в РФ):**

| Провайдер | Что есть | Цена (за 1 млн токенов) | Формат |
|---|---|---|---|
| Cloud.ru Evolution Foundation Models | DeepSeek V4 Flash, DeepSeek Chat V3, R1-distill | V4 Flash: 18,5 ₽ вход / 37,1 ₽ выход; V3: 37,3 / 170,9 ₽ | OpenAI-совместимый ([cloud.ru](https://cloud.ru/products/evolution-foundation-models)) |
| Yandex AI Studio | DeepSeek-V3.2, в том числе агенты; кэшированные токены дешевле | точные цифры не найдены, проверить | OpenAI-совместимый (Responses API) ([computerra](https://www.computerra.ru/337807/yandex-ai-studio-predstavila-obnovlenie-s-podderzhkoj-deepseek-v3-2-i-novymi-tarifami/)) |
| Selectel Foundation Models Catalog | deepseek-r1 и др. | проверить | OpenAI-совместимый ([selectel.ru](https://selectel.ru/services/cloud/foundation-models-catalog/)) |

Anthropic-совместимого эндпоинта у российских облаков не найдено. Claude Code к ним подключается только через прослойку [LiteLLM](https://docs.litellm.ai/docs/tutorials/claude_non_anthropic_models) или claude-code-router: Anthropic `/v1/messages` переводится в OpenAI-формат. Это дополнительный процесс на том же VPS, ~200–300 МБ RAM.

## 3. Российские провайдеры (~2 vCPU / 4 ГБ / 40–60 ГБ NVMe)

| Провайдер | Цена VM, ₽/мес | ЦОДы | 152-ФЗ | Managed PG | S3 | Оплата | API / Terraform | IPv6 |
|---|---|---|---|---|---|---|---|---|
| **Timeweb Cloud** | **~1 000–1 100** (2×3,3 ГГц, 4 ГБ, 50 ГБ NVMe; MSK 50 — 1 062 ₽ при оплате за год) ([поиск](https://timeweb.cloud/services/vds-vps), [обзор](https://timeweb.cloud/blog/obzor-tarifov-vps-v-2025-godu)) | Москва, СПб (spb-1/2/3), Новосибирск; за рубежом ams-1, fra-1, Алматы | Отдельное «Облако 152-ФЗ» до УЗ-1, аттестат ФСТЭК ([timeweb.cloud/solutions/152fz](https://timeweb.cloud/solutions/152fz)); цена сегмента — проверить | от ~230 ₽ ([postgresql](https://timeweb.cloud/services/postgresql)) | 10 ГБ — 79 ₽, 100 ГБ — 349 ₽ ([cnews](https://market.cnews.ru/tariff/42605)); ЦОД СПб | РФ-карта, иностранная карта, СБП, счёт для юрлица ([docs](https://timeweb.cloud/docs/service-payments/payment-methods)) | REST API, [Terraform](https://github.com/timeweb-cloud/terraform-provider-timeweb-cloud) | **Бесплатно** в МСК, СПб, AMS, Алматы, до 10 адресов; нет в nsk-1 и в OVN-сетях ([docs](https://timeweb.cloud/docs/public-ip/ipv6-adresa)) |
| **Selectel** | Standard 2 vCPU / 4 ГБ — ~2 856 ₽ ([looking.center](https://looking.center/companies/selectel-ru/virtual-servers/4-gb-2-vcpu-standard)); Shared Line (10/20/50% vCPU) и линейка VPS от 200 ₽ дешевле, проверить | Москва, СПб, Новосибирск, Tier III | Облако 152-ФЗ, УЗ-1, аттестат ФСТЭК ([selectel.ru](https://selectel.ru/services/cloud/servers/152fz/)) | есть, цена в калькуляторе | от 2,29 ₽/ГБ ([storage](https://selectel.ru/services/cloud/storage/)) | карта, СБП, счёт | API, Terraform (`selectel/selectel`) | Публичные IP, в том числе IPv6, от 3,67 ₽/сут ([selectel.ru](https://selectel.ru/services/cloud/servers/)) |
| **Yandex Cloud** | ~3 500–4 500 (100% vCPU); минимум 2×50% / 2 ГБ — от ~1 659 ₽ ([serverscan](https://serverscan.ru/providers/yandexcloud), [pricing](https://yandex.cloud/en/docs/compute/pricing)) | Москва, Владимир, Рязань | УЗ-1 ([блог](https://cloud.yandex.ru/blog/posts/2021/06/accreditation)) | есть, дорого | есть | карта, счёт | API, Terraform | есть |
| **Cloud.ru Evolution** | Free tier: 2 vCPU (доля ≤10%) / 4 ГБ / 30 ГБ NVMe **бесплатно** бессрочно, платный только IP ([cloud.ru/free-tier](https://cloud.ru/offers/free-tier), [kod.ru](https://kod.ru/test-draiv-oblaka-cloud-ru)) | Москва | Облако 152-ФЗ ([cloud.ru](https://cloud.ru/services/oblako-152fz)) | есть | есть, в free tier тоже | карта, счёт | API, Terraform | проверить |
| **VK Cloud** | ~3 200–4 200 ([ip-checker](https://ip-checker.pro/ru/blog/oblachnye-servery-rossiya-2026)) | Москва | 152-ФЗ, аттестат ФСТЭК ([cloud.vk.ru](https://cloud.vk.ru/solutions/152-fz/)) | есть | есть | карта, счёт | API, Terraform (`vk-cs`) | проверить |
| **FirstVDS** | «Разгон» 2 ядра / 4 ГБ — ~909 ₽ (SSD); NVMe дороже; +15% с 01.03.2026 ([firstvds](https://firstvds.ru/blog/all_price_increase_01-03-26)) | Москва | заявлений об аттестации не найдено | нет | нет | карта, СБП | API панели, Terraform нет | проверить |
| **Beget** | 2×4,5 ГГц / 4 ГБ / 50 ГБ NVMe — 2 550 ₽ ([hosting.country](https://hosting.country/companies/beget-com/virtualnye-servery)) | СПб | не найдено | нет | есть | карта, СБП | API | проверить |
| **Рег.облако** | почасовая оплата, скидка 7–10% за месяц; цена 2/4 не найдена ([help.reg.ru](https://help.reg.ru/support/finansovyye-voprosy/oplata-schetov-i-uslug/stoimost-uslug-iaas-v-publichnom-oblake-regru)) | Москва | Облако 152-ФЗ ([reg.cloud](https://reg.cloud/cloud/fz152)) | есть | есть | карта, счёт | OpenStack API, Terraform | проверить |

**Про 152-ФЗ.** Аттестованный сегмент обязателен только для УЗ-1 и УЗ-2 ([cloud4y](https://www.cloud4y.ru/blog/what-is-152-fz-cloud/)). Переписка клиентов с ФИО и телефонами без специальных или биометрических категорий обычно попадает в УЗ-3 или УЗ-4, при УЗ-4 хватает обычного VPS в РФ плюс оргмеры. Уровень защищённости определяет оператор, итог — за юристом. Независимо от хостинга нужны: уведомление РКН об обработке, уведомление о трансграничной передаче (Telegram, DeepSeek), политика обработки ПД и согласия.

## 4. Рекомендация

### Основной вариант: Timeweb Cloud, Москва (msk-1) или СПб, облачный сервер 2 vCPU / 4 ГБ / 50 ГБ NVMe, ~1 000–1 100 ₽/мес

Почему:
- Самый дешёвый крупный облачный провайдер нужной конфигурации с запасом бюджета.
- **Бесплатный публичный IPv6 в МСК и СПб.** Это единственный найденный прямой путь к `api.telegram.org` из РФ.
- В том же аккаунте есть зарубежные зоны (ams-1, fra-1) под запасной релей. Есть S3 и managed PG, если понадобятся. Есть Terraform и API. Оплата СБП и российскими картами.

Состав (итого ~1 100–1 250 ₽/мес):
- Одна VM: aiogram-бот, Claude Code (Node.js), PostgreSQL (сам на VM, бэкапы в S3), файлы на диске.
- S3 10 ГБ за 79 ₽ под бэкапы БД и файлов.
- Managed PG (от ~230 ₽) — опционально, позже.
- Зона **не nsk-1**: там нет IPv6. Сеть без OVN, иначе IPv6 недоступен.

### Запасной вариант: Selectel (Москва или СПб) с публичным IPv6

Облако 152-ФЗ до УЗ-1, если уровень защищённости окажется выше. Standard 2/4 выходит дороже бюджета (~2 850 ₽), поэтому брать Shared Line или линейку VPS; точную цену 2 vCPU / 4 ГБ проверить в калькуляторе. Бесплатный вариант для экспериментов: Cloud.ru free tier (2 vCPU ≤10% / 4 ГБ). Для Claude Code слабоват, для стенда годится.

### Топология: всё в РФ, наружу только замаскированные вызовы

```
[Telegram] ⇄ (IPv6; запасной путь: TCP-релей Timeweb fra-1 без расшифровки TLS)
      ⇅
[VPS Timeweb msk-1] бот aiogram ── PostgreSQL ── файлы/диск ── бэкап → S3 Timeweb (РФ)
      │ маскирование ПД (ADR-0001)
      ▼
[Claude Code] ── ANTHROPIC_BASE_URL → api.deepseek.com/anthropic
                 запасной путь: LiteLLM → Cloud.ru FM / Yandex AI Studio (DeepSeek в РФ)
```
- Разнесённая схема (фронт бота за рубежом) **не рекомендуется**: см. вариант D.
- У Claude Code выставить `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1`, чтобы не было лишних обращений к серверам Anthropic.
- Оплата DeepSeek ($20/мес): зарубежная карта или агрегатор в ₽ (Polza.ai, provod.ai). Если нужна оплата по счёту юрлица и данные в РФ, подойдёт Cloud.ru FM (DeepSeek V4 Flash ~18/37 ₽ за 1 млн токенов) через LiteLLM.

### ⚠️ Блокеры и риски

1. **Telegram по IPv4 из РФ заблокирован** (подтверждено на март–сентябрь 2026). Бот работает только по IPv6 или через зарубежный релей. В первый же день на купленном сервере проверить: `curl -6 -m 10 https://api.telegram.org` и `curl -4 ...`. Если IPv6 не проходит, включить релей и учесть риск «Антифрод 2.0».
2. **Возможная полная блокировка IPv6-пути.** Держать релей готовым: Timeweb fra-1, конфиг в репозитории.
3. **41-ФЗ и операторы ПД с сентября 2026 года** (данные из блогов, не проверены). Если запрет на иностранные мессенджеры для общения с клиентами действительно распространён на всех операторов ПД, сам канал Telegram под вопросом. **Нужна проверка юристом до запуска.**
4. **Доступ к `api.deepseek.com`** нестабилен (Cloudflare), оплата российскими картами невозможна. Запасные пути: российский агрегатор или DeepSeek на Cloud.ru или Yandex через LiteLLM.
5. **Нехватка ресурсов у Timeweb.** 24.09.2026 в msk-1 и spb-* не было свободных нод ([yummy#87](https://github.com/MelnikovTimofey/yummy/issues/87)). Если создать VM не получится, переходить на Selectel.
