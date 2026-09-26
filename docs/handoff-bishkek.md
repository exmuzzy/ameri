# Хендовер: развернуть ameri на сервере `bishkek`, не мешая тому, что там уже работает

> Этот файл — задание для агента (claude-ds, Claude Code, ZCode, Cursor), запущенного **на компьютере заказчика**, где работает `ssh bishkek`. Скопируйте его целиком в агента или скажите: «выполни docs/handoff-bishkek.md».

## Цель

Поднять на существующем сервере `bishkek` сайт **ameri** из этого репозитория (`github.com/exmuzzy/ameri`, ветка `master`) и выдать заказчику рабочую ссылку и пароль администратора.

**ameri** — это сайт на Streamlit. Что на нём есть:
- вход по логину и паролю;
- страницы «О проекте» и «Как работать»;
- «Чаты»: история с поиском, новый чат, вложения;
- ассистент на DeepSeek;
- расчётка воздуховодов через прототип duct-calc;
- страница «Настройки» для администратора: ключ DeepSeek и пользователи.

Код лежит в `app/` и `src/ameri/`, описание — в `README.md`.

## Главное правило: ничего не сломать

На `bishkek` уже работает другой сервис (бот) заказчика. Всё, что там есть, должно работать так же, как до тебя.

**Нельзя без явного «да» заказчика в чате:**
- останавливать, перезапускать, обновлять или удалять **чужие** контейнеры, compose-проекты, systemd-службы и процессы;
- выполнять `docker system prune`, `docker network prune`, `docker volume prune`, `docker compose down` в чужих каталогах;
- менять конфиги чужих сервисов: nginx, caddy, traefik, apache, их vhost-ы, `/etc/hosts`, cron других пользователей;
- включать или менять файрвол (`ufw`, `iptables`, `nftables`): можно отрезать чужой сервис или себя;
- ставить Docker, если его нет: установка меняет правила iptables;
- перезапускать демон Docker;
- делать `apt upgrade` или `dist-upgrade`, менять системный Python, перезагружать сервер;
- занимать порты 80 и 443 или любой порт, который уже слушается;
- запускать `deploy/bootstrap.sh`: он для **чистой** VPS и меняет систему целиком.

**Можно:**
- читать всё, что нужно для осмотра;
- создавать своё только внутри `/srv/ameri` и под пользователем `ameri`;
- использовать отдельный compose-проект `ameri` с контейнерами `ameri-*` и сетью `ameri`;
- использовать свободный порт **только на 127.0.0.1**;
- ставить **отдельные** пакеты через `apt-get install` без обновления остальных, если их нет (LibreOffice, git) — но сначала сообщить заказчику, что ставишь.

Если сомневаешься, считается ли действие вмешательством, — **остановись и спроси**.

## Шаг 1. Осмотр (только чтение)

Выполни и сохрани вывод. Секреты (токены, пароли, содержимое `.env`) не выводи и не записывай.

```bash
ssh bishkek 'set -x
  hostnamectl; cat /etc/os-release | head -3; uptime
  nproc; free -h; df -h / /srv 2>/dev/null
  python3 --version; which docker && docker --version && docker compose version
  sudo -n true 2>/dev/null && echo SUDO_OK || echo SUDO_NEEDS_PASSWORD; id
  sudo ss -ltnp
  docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Ports}}\t{{.Status}}" 2>/dev/null
  docker compose ls 2>/dev/null
  systemctl list-units --type=service --state=running --no-pager
  ls /etc/nginx/sites-enabled /etc/caddy /etc/traefik 2>/dev/null
  sudo ufw status 2>/dev/null; sudo iptables -S 2>/dev/null | head -40
  ls -la /srv; getent passwd ameri
  curl -fsS4 https://api.ipify.org; echo
  curl -s -o /dev/null -w "deepseek %{http_code}\n" https://api.deepseek.com
  curl -s -o /dev/null -w "github %{http_code}\n" https://github.com
'
```

Составь отчёт `docs/server-bishkek.md`:
- ОС, ресурсы, свободная память и диск;
- есть ли Docker;
- **какие порты заняты и кем**;
- какие сервисы работают — это **список «не трогать»**;
- есть ли reverse proxy на 80/443, для каких доменов;
- свободен ли `/srv/ameri`;
- доступны ли DeepSeek и GitHub.

Там же зафиксируй «снимок до»: `ss -ltnp`, `docker ps`, `systemctl --failed`. Проверь ответы чужих сервисов, если у них есть HTTP-адреса: `curl -I`.

## Шаг 2. План — показать заказчику и дождаться «да»

По результатам осмотра выбери вариант установки и вариант доступа и **опиши их заказчику одним сообщением до любых изменений**.

**Установка:**
| Условие | Вариант |
|---|---|
| Docker уже установлен и используется | **A. Docker**: отдельный проект `deploy/shared-host/docker-compose.yml` |
| Docker нет | **B. Без Docker**: пользователь `ameri`, Python 3.13 через `uv` в `/srv/ameri`, systemd-служба `deploy/shared-host/ameri.service`. Docker не ставить |

**Доступ к сайту:**
| Условие | Вариант | Что трогаем |
|---|---|---|
| 80 и 443 свободны | **1. Свой HTTPS**: Caddy, `https://<ip-через-дефисы>.sslip.io` | Только наши порты 80/443 |
| На 80/443 уже есть nginx/caddy/traefik | **2. Через существующий proxy**: новый отдельный vhost или `location /ameri/` → `127.0.0.1:<порт>`. Ставить **только с согласия заказчика**: бэкап конфига, `nginx -t` (или аналог), `reload`, не `restart` | Один новый файл конфига чужого proxy |
| Заказчик не хочет трогать proxy | **3. Отдельный порт**: наш Caddy на свободном порту (например 8443) с самоподписанным сертификатом, `https://<ip>:8443` | Новый порт; если файрвол его закрывает, то доступ по SSH-туннелю: `ssh -L 18501:127.0.0.1:18501 bishkek` → `http://localhost:18501` |

По умолчанию рекомендуй вариант 1, если порты свободны, иначе вариант 3 с туннелем. Вариант 2 предлагай, только если у заказчика есть домен на этом proxy. Для варианта 2 с подкаталогом задай `STREAMLIT_SERVER_BASE_URL_PATH=ameri`.

Порт приложения: первый свободный из `18501, 18511, 18521…`. Проверь его по `ss -ltnp`.

## Шаг 3. Установка

Всё ниже — в `/srv/ameri`. Если нужен `sudo`, а без пароля он не работает, попроси заказчика выполнить команды самому.

```bash
sudo mkdir -p /srv/ameri/{data,duct-calc,backups}
sudo useradd --system --home /srv/ameri --shell /usr/sbin/nologin ameri 2>/dev/null || true
sudo git clone https://github.com/exmuzzy/ameri.git /srv/ameri/app   # или git pull, если уже есть
sudo chown -R ameri:ameri /srv/ameri && sudo chmod 700 /srv/ameri/data
```

**Пароль администратора.** Сгенерируй его локально, например `python3 -c 'import secrets;print(secrets.token_urlsafe(12))'`, и покажи заказчику в чате. В репозиторий его не записывай. Хэш и `users.toml` сделай на сервере:

```bash
ssh bishkek "cd /srv/ameri/app && sudo -u ameri env PW='<пароль>' python3 -c \"import os,sys;sys.path.insert(0,'src');from ameri.auth import hash_password,save_users,User;from pathlib import Path;save_users(Path('/srv/ameri/data/users.toml'),{'admin':User('admin','Администратор','admin',hash_password(os.environ['PW']))})\""
```

Если системный Python старше 3.11 и нет `tomllib`, выполни это после создания venv (вариант B) или внутри контейнера (вариант A).

**Прототип расчётки (duct-calc).** Архив прототипа есть только у заказчика, в репозиторий его не класть: репозиторий публичный, а в шаблоне цены. Спроси у заказчика путь к архиву `duct-calc-review-*.zip` на его компьютере и перенеси:

```bash
scp <путь>/duct-calc-review-*.zip bishkek:/tmp/duct-calc.zip
ssh bishkek 'sudo -u ameri unzip -oq /tmp/duct-calc.zip -d /srv/ameri/duct-calc && rm /tmp/duct-calc.zip && ls /srv/ameri/duct-calc/src/duct_calc /srv/ameri/duct-calc/data'
```

Если архива нет, сайт работает и без расчётки: действие «Расчётка воздуховодов» просто не показывается.

### Вариант A — Docker

```bash
cd /srv/ameri/app/deploy/shared-host
printf 'AMERI_PORT=18501\n' | sudo -u ameri tee .env
# для варианта доступа 1 добавить: SITE_ADDRESS=<ip-через-дефисы>.sslip.io
sudo docker compose -p ameri build
sudo docker compose -p ameri up -d                         # только приложение на 127.0.0.1
# вариант доступа 1 (80/443 свободны):
# sudo docker compose -p ameri --profile own-https up -d
```

Всегда указывай `-p ameri` и работай из `deploy/shared-host`. Никаких `down`, `prune` и `restart` без `-p ameri`.

### Вариант B — без Docker

```bash
sudo apt-get install -y --no-install-recommends libreoffice-calc libreoffice-writer   # только если их нет и заказчик согласен
sudo -u ameri bash -c 'curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/srv/ameri/.local/bin sh'
sudo -u ameri /srv/ameri/.local/bin/uv venv --python 3.13 /srv/ameri/venv
sudo -u ameri /srv/ameri/.local/bin/uv pip install --python /srv/ameri/venv -r /srv/ameri/app/requirements.txt
sudo install -o ameri -m 600 /srv/ameri/app/deploy/shared-host/ameri.env.example /srv/ameri/ameri.env   # поправить AMERI_PORT
sudo cp /srv/ameri/app/deploy/shared-host/ameri.service /etc/systemd/system/ameri.service
sudo systemctl daemon-reload && sudo systemctl enable --now ameri
```

Для варианта доступа 1 без Docker: Caddy — отдельный бинарник в `/srv/ameri/bin` с отдельной systemd-службой `ameri-caddy`. Пакет caddy из apt не ставить: он заберёт 80/443 глобальной службой.

### Доступ

Настрой выбранный в шаге 2 вариант. Для варианта 2 пример vhost для nginx лежит ниже. Создай его **отдельным файлом**, чужие не правь.

```nginx
# /etc/nginx/sites-available/ameri  (+ симлинк в sites-enabled), только с согласия заказчика
location /ameri/ {
    proxy_pass http://127.0.0.1:18501/ameri/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_read_timeout 600s;
    client_max_body_size 50m;
}
```

Streamlit работает через WebSocket, поэтому заголовки `Upgrade` и `Connection` обязательны. Длинные расчёты требуют `proxy_read_timeout` не меньше 600 секунд.

### Бэкап

Для пользователя `ameri` (его crontab, не системный):

```cron
30 3 * * * tar -czf /srv/ameri/backups/ameri-$(date +\%F).tgz -C /srv/ameri data && find /srv/ameri/backups -name 'ameri-*.tgz' -mtime +14 -delete
```

## Шаг 4. Проверка

1. **Сайт жив:** `curl -fsS http://127.0.0.1:<порт>/_stcore/health` на сервере отвечает `ok`, внешний адрес открывается.
2. **Работа в браузере:**
   - войти под `admin`;
   - в «Настройках» заказчик сам вставляет ключ DeepSeek (в чат его не присылать);
   - создать менеджера и руководителя;
   - начать новый чат, задать вопрос ассистенту, приложить спецификацию и построить расчётку.
3. **Чужое не пострадало:** повтори «снимок до» и сравни. Должно совпадать всё, кроме новых `ameri-*`: `ss -ltnp`, `docker ps`, `systemctl --failed`, ответы чужих сервисов. Если что-то отличается — сразу откат и сообщение заказчику.

## Откат

```bash
# Вариант A
cd /srv/ameri/app/deploy/shared-host && sudo docker compose -p ameri --profile own-https down
# Вариант B
sudo systemctl disable --now ameri ameri-caddy 2>/dev/null; sudo rm -f /etc/systemd/system/ameri*.service; sudo systemctl daemon-reload
# Доступ, вариант 2: удалить наш vhost, проверить конфиг, reload
# Данные сохранить или удалить по решению заказчика: /srv/ameri/data
```

## Результат для заказчика

Одним сообщением:
- ссылка на сайт;
- логин `admin` и пароль;
- что сделано и какой вариант выбран;
- что проверено: сайт работает, чужие сервисы не затронуты;
- что заказчику сделать самому: вставить ключ DeepSeek в «Настройках», завести пользователей.

В репозиторий закоммить в `master` только `docs/server-bishkek.md` (без секретов) и правки скриптов, если понадобились.
