# Первый запуск URDB API на VPS

Этот сценарий запускает Orchestrator/API и изолированный updater-контейнер. Updater управляет только контейнером URDB и не обновляет Happ, Keenetic или систему VPS.

## Требования

- Git;
- Docker Engine;
- Docker Compose v2 (`docker compose`).

API пока работает без авторизации и HTTPS. Не публикуйте порт в недоверенную сеть без ограничения доступа firewall.

## Клонирование

```bash
git clone https://github.com/ldkt/happ-routing.git
cd happ-routing
```

Создайте локальный файл настроек и замените `URDB_UPDATER_TOKEN` на длинное случайное значение:

```bash
cp .env.example .env
```

По умолчанию API использует порт `8080`. Чтобы изменить его, задайте `URDB_API_PORT` в `.env` до запуска.

## Получение образов

```bash
docker compose pull
```

## Запуск

```bash
docker compose up -d
```

## Просмотр логов

```bash
docker compose logs -f urdb-api
```

Для однократного вывода без ожидания новых сообщений:

```bash
docker compose logs urdb-api
```

## Проверка контейнера

```bash
docker compose ps
```

После прохождения healthcheck контейнер должен иметь состояние `healthy`.

## Автоматическое обновление

`POST /api/update` проверяет наличие новой версии и передаёт обновление внутреннему updater-контейнеру. Updater:

1. сохраняет идентификатор текущего образа;
2. скачивает новый образ из GHCR;
3. пересоздаёт только `urdb-api`;
4. ожидает успешный healthcheck;
5. при неуспешном healthcheck автоматически восстанавливает предыдущий образ.

Проверить запуск обновления можно командой:

```bash
curl -X POST http://localhost:8080/api/update
```

Перезапустить только контейнер API:

```bash
curl -X POST http://localhost:8080/api/restart
```

## Проверка API

При стандартном порте:

```bash
curl http://localhost:8080/api/status
```

Если `URDB_API_PORT` был изменён, используйте выбранное значение:

```bash
curl http://localhost:<PORT>/api/status
```

Эндпоинт возвращает JSON со значениями `current_version`, `latest_version`, `has_update`, `changes`, `checked_at` и `health`.

## Остановка

```bash
docker compose down
```
