# Проверка релизов

Этот документ описывает обязательную проверку релиза Universal Routing Engine
до установки на пользовательские устройства. Новый участник проекта должен
иметь возможность пройти процедуру от начала до конца без знания внутреннего
устройства генераторов.

Релиз считается проверенным только тогда, когда выполнены все проверки
целостности, профили успешно разобраны, а функциональные тесты показывают
ожидаемый маршрут. Доступность сайта сама по себе не доказывает правильность
маршрута: необходимо проверить outbound tag в логах клиента либо наличие или
отсутствие соединения в access log VPN-сервера.

## Что потребуется

- GitHub CLI `gh`, авторизованный командой `gh auth login`;
- Python 3;
- `sha256sum` в Linux или `shasum` в macOS;
- Git и Go для детальной проверки содержимого `geosite.dat`;
- тестовое устройство с Happ или сервер с Xray/3x-ui;
- доступ к логам клиента или VPN-сервера;
- возможность временно очистить DNS-кэш и перезапустить тестовый клиент.

Все команды ниже запускаются в отдельном пустом каталоге. Они не изменяют
установленную конфигурацию.

## Краткий checklist

- [ ] `geosite.dat` скачан и имеет ненулевой разумный размер.
- [ ] `geoip.dat` скачан и имеет ненулевой разумный размер.
- [ ] `happ-routing.json` и `happ-routing-link.txt` созданы.
- [ ] `3x-ui-routing.json` создан.
- [ ] Все значения из `SHA256SUMS` проверены успешно.
- [ ] `release.json` разобран и содержит сведения об источниках.
- [ ] Release tag указывает на ожидаемый commit ветки `main`.
- [ ] Все обязательные release assets опубликованы на GitHub.
- [ ] Happ link декодируется в тот же профиль, что и `happ-routing.json`.
- [ ] DNS в Happ-профиле соответствует ожидаемым значениям.
- [ ] 3x-ui routing JSON синтаксически корректен и использует существующие tags.
- [ ] DIRECT-домены не проходят через VPN.
- [ ] PROXY-домены проходят через VPN.
- [ ] `category-ads-all` присутствует и реально блокирует выбранный тестовый домен.
- [ ] Результаты проверки записаны вместе с release tag и commit SHA.

## 1. Создание изолированного каталога

```bash
mkdir routing-release-verification
cd routing-release-verification
```

Запишите проверяемый release tag:

```bash
REPO=ldkt/happ-routing
TAG=$(gh release view --repo "$REPO" --json tagName --jq .tagName)
echo "$TAG"
```

Не продолжайте, если команда не вернула ожидаемый tag.

## 2. Проверка источника релиза

Release workflow должен собираться из `main`. Проверьте поле
`targetCommitish`, SHA тега и текущий SHA `main`:

```bash
gh release view --repo "$REPO" \
  --json tagName,targetCommitish,publishedAt,url

TAG_SHA=$(gh api "repos/$REPO/git/ref/tags/$TAG" --jq .object.sha)
MAIN_SHA=$(gh api "repos/$REPO/branches/main" --jq .commit.sha)

printf 'release tag: %s\nmain:        %s\n' "$TAG_SHA" "$MAIN_SHA"
test "$TAG_SHA" = "$MAIN_SHA"
```

Для latest release оба SHA должны совпасть. Исключение допустимо только для
явно помеченного исторического релиза, который не позиционируется как latest.

Найдите workflow run, соответствующий SHA:

```bash
gh run list --repo "$REPO" --workflow release.yml --limit 10 \
  --json databaseId,headBranch,headSha,event,status,conclusion,url
```

В подходящей записи должны быть:

- `headBranch` равен `main`;
- `headSha` равен `$TAG_SHA`;
- `status` равен `completed`;
- `conclusion` равен `success`.

## 3. Скачивание release assets

```bash
mkdir assets
gh release download "$TAG" --repo "$REPO" --dir assets
ls -lh assets
```

Проверьте полный обязательный набор:

```bash
for file in \
  geosite.dat \
  geoip.dat \
  happ-routing.json \
  happ-routing-link.txt \
  3x-ui-routing.json \
  release.json \
  SHA256SUMS
do
  test -s "assets/$file" || {
    echo "Отсутствует или пуст: $file" >&2
    exit 1
  }
done
```

Проверка размеров не заменяет SHA-256, но помогает обнаружить очевидно
оборванную загрузку:

```bash
test "$(wc -c < assets/geosite.dat)" -gt 1024
test "$(wc -c < assets/geoip.dat)" -gt 1024
```

## 4. Проверка SHA-256

Linux:

```bash
cd assets
sha256sum -c SHA256SUMS
cd ..
```

macOS:

```bash
cd assets
shasum -a 256 -c SHA256SUMS
cd ..
```

Каждая строка должна завершиться `OK`. Один несовпавший digest делает весь
релиз непригодным для установки. Не заменяйте повреждённый файл вручную: нужно
исправить сборку и выпустить новый release.

## 5. Проверка release metadata

```bash
python3 -m json.tool assets/release.json
```

Убедитесь, что:

- `schemaVersion` поддерживается текущим проектом;
- `generatedAt` соответствует времени release;
- присутствуют источники geosite и GeoIP;
- для `geosite.dat`, `geoip.dat`, Happ и 3x-ui artifacts записаны размер и SHA-256;
- записанные значения совпадают со скачанными файлами.

## 6. Проверка Happ-профиля

Следующий скрипт декодирует `happ-routing-link.txt`, сравнивает его с JSON и
проверяет DNS и URL геофайлов:

```bash
python3 - <<'PY'
import base64
import json
from pathlib import Path

root = Path("assets")
profile = json.loads((root / "happ-routing.json").read_text(encoding="utf-8"))
link = (root / "happ-routing-link.txt").read_text(encoding="utf-8").strip()
prefix = "happ://routing/onadd/"

assert link.startswith(prefix), "Неверная схема Happ link"
decoded = json.loads(base64.b64decode(link[len(prefix):], validate=True))
assert decoded == profile, "Happ link не соответствует happ-routing.json"

expected = {
    "RemoteDNSType": "DoH",
    "RemoteDNSDomain": "https://dns.google/dns-query",
    "RemoteDNSIP": "8.8.8.8",
    "DomesticDNSType": "DoH",
    "DomesticDNSDomain": "https://dns.yandex.net/dns-query",
    "DomesticDNSIP": "77.88.8.8",
    "DnsHosts": {
        "dns.google": "8.8.8.8",
        "dns.yandex.net": "77.88.8.8",
    },
}

for key, value in expected.items():
    assert profile.get(key) == value, (key, profile.get(key), value)

base = "https://github.com/ldkt/happ-routing/releases/latest/download/"
assert profile["Geoipurl"] == base + "geoip.dat"
assert profile["Geositeurl"] == base + "geosite.dat"

for key in (
    "DirectSites", "DirectIp", "ProxySites", "ProxyIp",
    "BlockSites", "BlockIp", "DomainStrategy",
):
    assert key in profile, f"Отсутствует поле {key}"

print("Happ profile: OK")
PY
```

Перед установкой визуально проверьте JSON. В нём не должно быть токенов,
паролей, адресов частных серверов или иных секретов.

## 7. Проверка 3x-ui/Xray routing

```bash
python3 - <<'PY'
import json
from pathlib import Path

routing = json.loads(Path("assets/3x-ui-routing.json").read_text(encoding="utf-8"))
assert isinstance(routing.get("rules"), list) and routing["rules"]
assert routing.get("domainStrategy")

tags = {rule.get("outboundTag") for rule in routing["rules"]}
assert {"direct", "proxy", "block"}.issubset(tags), tags

fallback = routing["rules"][-1]
assert fallback.get("network") == "tcp,udp"
assert fallback.get("outboundTag") == "direct"

print("3x-ui/Xray routing: OK")
PY
```

После импорта убедитесь, что реальные Xray outbounds называются `direct`,
`proxy` и `block`. Если сервер использует другие tags, сначала настройте mapping
в target-конфигурации и создайте новый проверенный release. Не исправляйте
сгенерированный JSON вручную.

## 8. Проверка содержимого geosite.dat

Скачайте исходники официального compiler/dump tool и извлеките необходимые
категории:

```bash
git clone --depth=1 https://github.com/v2fly/domain-list-community.git
mkdir datdump
cd domain-list-community
go run ./cmd/datdump \
  -inputdata "$(cd .. && pwd)/assets/geosite.dat" \
  -outputdir "$(cd .. && pwd)/datdump" \
  -exportlists category-ads-all,routing-direct,routing-proxy,routing-block
cd ..
ls -lh datdump
```

Ожидаются непустые файлы:

```text
category-ads-all.yml
routing-direct.yml
routing-proxy.yml
routing-block.yml
```

Просмотрите файлы и убедитесь, что пользовательские категории присутствуют, а
`category-ads-all` содержит реальные правила, а не только имя категории.

## 9. Функциональные routing tests

### Подготовка

1. Установите проверенные `geoip.dat` и `geosite.dat`.
2. Импортируйте проверенный Happ profile либо 3x-ui routing JSON.
3. Перезапустите клиент и Xray core.
4. Очистите DNS-кэш клиента.
5. Включите подробный routing/access log.
6. Зафиксируйте IP VPN-сервера и обычный IP устройства.
7. Закройте фоновые приложения, чтобы тестовые соединения легко находились в
   логах.

Для каждого домена выполните новый запрос без повторного использования старого
соединения:

```bash
curl --http1.1 --no-keepalive --connect-timeout 15 -I "https://DOMAIN/"
```

HTTP-код `403`, `404` или redirect допустим: проверяется маршрут TCP/TLS
соединения, а не содержимое ответа.

Способ подтверждения маршрута:

- предпочтительно: найти домен и выбранный outbound tag в routing/access log;
- альтернативно: одновременно наблюдать access log VPN-сервера;
- DIRECT подтверждён, если соединение не появилось на VPN-сервере и клиент
  выбрал direct outbound;
- PROXY подтверждён, если соединение появилось на VPN-сервере и клиент выбрал
  proxy outbound;
- BLOCK подтверждён, если соединение отклонено локально и не установлено ни
  напрямую, ни через VPN.

### DIRECT

| Домен | Ожидаемый результат |
| --- | --- |
| `gosuslugi.ru` | Не проходит через VPN |
| `nalog.gov.ru` | Не проходит через VPN |
| `sberbank.ru` | Не проходит через VPN |
| `tbank.ru` | Не проходит через VPN |
| `yandex.ru` | Не проходит через VPN |
| `vk.com` | Не проходит через VPN |
| `ozon.ru` | Не проходит через VPN |
| `wildberries.ru` | Не проходит через VPN |

Любое соединение к этим доменам через proxy outbound означает провал релиза.

### PROXY

| Домен | Ожидаемый результат |
| --- | --- |
| `youtube.com` | Обязательно проходит через VPN |
| `github.com` | Обязательно проходит через VPN |
| `chatgpt.com` | Обязательно проходит через VPN |
| `openai.com` | Обязательно проходит через VPN |
| `instagram.com` | Обязательно проходит через VPN |
| `facebook.com` | Обязательно проходит через VPN |
| `discord.com` | Обязательно проходит через VPN |
| `telegram.org` | Обязательно проходит через VPN |

Прямое соединение хотя бы к одному из этих доменов означает провал релиза.

### BLOCK

1. Убедитесь, что Happ profile или Xray routing содержит
   `geosite:category-ads-all` в block action.
2. Откройте `datdump/category-ads-all.yml` и выберите актуальное доменное
   правило. Не используйте домен, которого нет в скачанном release.
3. Выполните DNS lookup и HTTPS-запрос к выбранному домену.
4. Проверьте routing log.

Ожидаемый результат:

- выбран block/reject outbound;
- TCP-соединение с доменом не установлено;
- соединение отсутствует в VPN access log;
- запрос не был отправлен напрямую;
- в логе видно совпадение с `category-ads-all` либо соответствующим block rule.

DNS-ошибка сама по себе не доказывает работу block rule. Подтверждение должно
исходить из routing log или другого наблюдаемого решения backend’а.

## 10. Протокол результатов

Сохраните результаты в Issue, PR или release verification log:

```text
Release tag:
Release SHA:
Проверяющий:
Дата и время:
ОС и клиент:
Версия Happ/Xray/3x-ui:
SHA256: PASS/FAIL
Happ profile: PASS/FAIL
3x-ui routing: PASS/FAIL
DIRECT: PASS/FAIL
PROXY: PASS/FAIL
BLOCK: PASS/FAIL
Замечания:
```

Не помечайте релиз проверенным, если хотя бы один обязательный тест имеет статус
`FAIL` или результат невозможно наблюдать.

## Troubleshooting

### Неверный DNS

**Симптомы**

- Happ показывает Cloudflare или другой неожиданный resolver;
- `RemoteDNS*`, `DomesticDNS*` или `DnsHosts` не совпадают;
- домены разрешаются только при отключении профиля;
- DNS работает, но маршрутизация по доменам ведёт себя нестабильно.

**Диагностика**

1. Декодируйте `happ-routing-link.txt` скриптом из раздела 6.
2. Сравните его с `happ-routing.json`.
3. Проверьте `targets/happ.yaml` в commit, на который указывает release tag.
4. Проверьте, что generator не подставляет статические DNS hostnames или IP.
5. Очистите DNS-кэш и повторите тест.

**Исправление**

Исправьте source target или generator, добавьте regression test, соберите новый
release из `main` и повторно проверьте скачанный asset. Не редактируйте профиль
после публикации.

### Устаревший geosite.dat

**Симптомы**

- новые домены не совпадают с ожидаемой категорией;
- `datdump` не находит `routing-*` category;
- release metadata указывает на старый upstream commit;
- поведение отличается от локальной сборки актуального `main`.

**Диагностика**

1. Изучите `release.json` и `generatedAt`.
2. Извлеките категории через `datdump`.
3. Сравните geosite source commit с текущим upstream.
4. Проверьте логи шага `Build and validate` release workflow.

**Исправление**

Запустите новую сборку из актуального `main`. Если upstream fetch использует
неверную ветку или cache, исправьте build script, очистите cache и опубликуйте
новый immutable release.

### Устаревший geoip.dat

**Симптомы**

- IP попадает не в ту страну или категорию;
- `generatedAt` свежий, но digest совпадает со старым release;
- upstream уже опубликовал новый GeoIP asset;
- SHA upstream не соответствует скачанному файлу.

**Диагностика**

1. Проверьте источник GeoIP в `release.json`.
2. Сравните release digest с опубликованным upstream SHA-256.
3. Изучите URL и redirect в логах build workflow.
4. Убедитесь, что сборка не повторно использовала старый файл из cache.

**Исправление**

Исправьте upstream URL или cache handling. Сборка должна заново скачать файл и
проверить upstream checksum до публикации. После этого выпустите новый release.

### Release собран не из того commit

**Симптомы**

- release tag SHA отличается от `main`;
- workflow run показывает другую `headBranch` или `headSha`;
- локальная генерация из `main` отличается от release asset;
- недавно объединённое исправление отсутствует в опубликованном профиле.

**Диагностика**

Выполните команды из раздела 2 и сравните:

- SHA release tag;
- SHA `main`;
- workflow `headSha`;
- commit, содержащий ожидаемое изменение.

Также проверьте base branch объединённого PR. Stacked PR после merge своей base
ветки необходимо перенаправить на `main`; иначе его merge может изменить старую
feature branch, а не `main`.

**Исправление**

Перенесите проверенные commits на ветку от актуального `main`, откройте PR в
`main`, дождитесь CI и объедините его. Затем запустите release workflow с
`--ref main` и подтвердите новый tag SHA.

### Отсутствуют artifacts

**Симптомы**

- `gh release download` не скачивает обязательный файл;
- файл имеет нулевой размер;
- `SHA256SUMS` ссылается на отсутствующий asset;
- latest URL возвращает `404`.

**Диагностика**

```bash
gh release view "$TAG" --repo "$REPO" --json assets
gh run view RUN_ID --repo "$REPO" --log
```

Сравните asset list с checklist из раздела 3.

**Исправление**

Исправьте artifact manifest или publish step и создайте новый release. Не
догружайте файл вручную в уже проверяемый immutable release: его содержимое
перестанет соответствовать первоначальной проверке.

### Неверный Happ profile

**Симптомы**

- link не декодируется;
- decoded JSON отличается от `happ-routing.json`;
- отсутствуют routing arrays или geodata URLs;
- DNS или категории отличаются от policy/target.

**Диагностика**

1. Запустите скрипт раздела 6.
2. Сгенерируйте профиль локально из release tag.
3. Сравните локальный JSON и опубликованный asset.
4. Проверьте target settings и Happ generator в том же commit.

**Исправление**

Исправьте только source policy, target или generator. Добавьте regression test,
создайте новый release и проверяйте скачанный GitHub asset, а не локальный
`dist/`.

### Неверная конфигурация backend

**Симптомы**

- Xray сообщает `outbound not found`;
- правила загружены, но все соединения используют fallback;
- direct/proxy перепутаны;
- Happ и 3x-ui дают разные результаты при одной policy.

**Диагностика**

1. Сравните tags в `3x-ui-routing.json` с реальными outbound tags Xray.
2. Проверьте порядок правил и последнее fallback rule.
3. Убедитесь, что backend загрузил именно release geodata.
4. Включите routing debug log и найдите выбранное правило для тестового домена.
5. Сравните результат с canonical policy.

**Исправление**

Исправьте target mapping и заново сгенерируйте artifacts. Backend-specific
настройки не должны изменять canonical policy. После исправления повторите все
DIRECT, PROXY и BLOCK tests.

## Рекомендации для будущего CI

Ручная процедура остаётся release gate до появления эквивалентной
автоматизации. Будущий CI должен автоматически проверять:

### Release integrity

- наличие полного artifact manifest;
- отсутствие пустых и неожиданных файлов;
- SHA-256 каждого asset;
- совпадение release tag, workflow head SHA и ожидаемого `main` commit;
- возможность скачать каждый asset через public latest URL.

### Routing consistency

- уникальность и непротиворечивость правил;
- ожидаемую классификацию обязательных DIRECT/PROXY test domains;
- наличие и приоритет BLOCK rules;
- одинаковую семантику fallback во всех backend plans;
- отсутствие молчаливого удаления неподдерживаемых правил.

### Policy validation

- schema version;
- обязательные поля;
- допустимые actions и matcher types;
- дубликаты и конфликты;
- ссылки на существующие domain/IP sets;
- детерминированность normalized policy.

### Generated artifacts

- воспроизводимую генерацию из одного commit;
- semantic comparison Happ link и Happ JSON;
- JSON/schema validation каждого backend output;
- отсутствие секретов;
- release metadata и checksums, построенные из фактически публикуемых файлов.

### Backend compatibility

- contract tests для Happ и Xray/3x-ui;
- capability tests для каждого будущего backend;
- golden files для стабильных форматов;
- явную ошибку при неподдерживаемой policy capability;
- smoke tests с реальными версиями backend’ов в контейнерах или изолированных
  environments.

Автоматическая проверка должна запускаться до публикации. Publish job не должен
иметь возможности создать release, пока integrity, policy, generator и backend
compatibility jobs не завершились успешно.
