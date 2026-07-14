# Happ Routing

Автоматически обновляемый комплект маршрутизации для [Happ](https://www.happ.su/)
и Xray в [3x-ui](https://github.com/MHSanaei/3x-ui). Репозиторий хранит один
декларативный профиль и ежедневно выпускает совместимые `geosite.dat`,
`geoip.dat`, ссылку импорта Happ и JSON маршрутизации 3x-ui.

## Готовые файлы

После первого запуска workflow **Update routing data** файлы доступны в latest
release:

| Файл | Назначение |
| --- | --- |
| `geosite.dat` | Актуальные списки v2fly плюс `happ-direct`, `happ-proxy`, `happ-block` |
| `geoip.dat` | Актуальная база Loyalsoldier, проверенная по upstream SHA-256 |
| `happ-routing.json` | Читаемый профиль Happ |
| `happ-routing-link.txt` | Готовая ссылка `happ://routing/onadd/...` |
| `3x-ui-routing.json` | Объект `routing` для Xray/3x-ui |
| `release.json` | Версии источников, размеры и контрольные суммы |
| `SHA256SUMS` | SHA-256 всех публикуемых артефактов |

Базовый URL релиза:

```text
https://github.com/ldkt/happ-routing/releases/latest/download
```

## Настройка правил

Общий профиль находится в [`config/routing.json`](config/routing.json). Изменяйте
массивы `directSites`, `proxySites`, `blockSites` и соответствующие IP-массивы.
Локальные доменные категории находятся в `data/`:

- `data/happ-direct` — прямое соединение;
- `data/happ-proxy` — прокси;
- `data/happ-block` — блокировка.

Синтаксис соответствует `v2fly/domain-list-community`: `domain:`, `full:`,
`keyword:`, `regexp:` и `include:`. Порядок правил важен: блокировка проверяется
до прямых и прокси-правил.

## Happ

1. Откройте latest release репозитория.
2. Откройте `happ-routing-link.txt` и перейдите по находящейся в нём ссылке на
   устройстве с установленным Happ.
3. Подтвердите добавление профиля.

Профиль уже содержит постоянные ссылки на latest `geoip.dat` и `geosite.dat`,
поэтому Happ сможет обновлять геофайлы без переустановки профиля. Если ссылка
не открывается из браузера, скопируйте её целиком в адресную строку.

## 3x-ui

Есть два варианта.

### Замена стандартных geofiles

Скачайте `geoip.dat` и `geosite.dat` из latest release в каталог Xray
(`XUI_BIN_FOLDER`, обычно `/usr/local/x-ui/bin`), затем перезапустите Xray.
После этого категории используются как обычно: `geosite:happ-proxy` и
`geoip:private`.

### Custom Geofiles в новых версиях 3x-ui

Добавьте два URL через **Xray → Geofiles → Custom GeoSite / GeoIP sources** с
алиасом `happ`. 3x-ui сохранит их как `geosite_happ.dat` и `geoip_happ.dat`.
Для внешнего файла замените ссылки в `3x-ui-routing.json`, например:

```text
geosite:happ-proxy       → ext:geosite_happ.dat:happ-proxy
geoip:private            → ext:geoip_happ.dat:private
```

В разделе **Xray Configs → Routing Rules** установите теги outbound в
`config/routing.json` равными фактическим тегам вашего сервера, затем вставьте
содержимое `3x-ui-routing.json`. По умолчанию используются `direct`, `proxy` и
`block` — они должны существовать в конфигурации Xray.

## Локальная сборка

Нужны Git, Go, Python 3, curl и стандартная утилита `shasum`:

```bash
make build
```

Результат появится в `dist/`. Быстрая генерация JSON без скачивания geodata:

```bash
make configs
make test
```

## Автоматизация и безопасность

- CI проверяет Python-тесты и полную сборку на каждом Pull Request.
- Ежедневный release workflow запускается в 03:17 UTC и доступен вручную.
- Upstream `geoip.dat` принимается только при совпадении опубликованной SHA-256.
- Release имеет уникальный тег, а `latest` всегда указывает на свежую успешную
  сборку.
- Workflow использует минимальные GitHub permissions: read в CI и contents:write
  только в release job.

Источники данных сохраняют собственные лицензии. Код этого репозитория — MIT.
