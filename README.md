# Universal Routing Engine

Client-neutral routing policy compiler for VPN and proxy ecosystems. Routing
decisions are defined once and converted into Happ and Xray/3x-ui artifacts.
The architecture is prepared for future sing-box, Clash/Mihomo and Keenetic
generators without coupling the policy to any client.

> Keenetic, sing-box and Clash/Mihomo generators are not implemented yet.

## Architecture

```text
policy/*.yaml ──> typed core model ──> generator ──> client artifacts
                       │
targets/*.yaml ────────┘
```

The layers have deliberately narrow responsibilities:

| Layer | Location | Responsibility |
| --- | --- | --- |
| Routing Policy | `policy/` | Rules, precedence, fallback and domain strategy |
| Core | `routing_engine/model.py`, `loader.py` | Loading, normalization and validation |
| Target settings | `targets/` | Client-specific URLs, DNS settings and outbound tags |
| Generators | `routing_engine/generators/` | Pure conversion of a validated policy to client formats |
| Geodata build | `data/`, `scripts/build.sh` | Compile custom geosite categories and package GeoIP |

Business rules must not be added to generators. If a decision affects routing
semantics—such as precedence, fallback, validation or classification—it belongs
to the policy or core model. A generator may only map the validated model to a
client schema.

## Routing Policy

`policy/policy.yaml` contains global semantics:

```yaml
version: 1
name: Universal Routing Policy
domain_strategy: IPIfNonMatch
action_order: [block, direct, proxy]
fallback: direct
```

Rules are split by action for clean reviews:

- `policy/direct.yaml` — bypass proxy;
- `policy/proxy.yaml` — use proxy;
- `policy/block.yaml` — reject traffic.

Each file has the same client-neutral shape:

```yaml
domains:
  - geosite:private
ips:
  - geoip:private
```

Custom domain-list-community categories remain under `data/`. They are compiled
into `geosite.dat` and referenced from the policy as `geosite:routing-direct`,
`geosite:routing-proxy` and `geosite:routing-block`. The old `happ-*` categories
remain as aliases so existing installations continue to work; new rules belong
in the client-neutral `data/routing-*` lists.

## Generators

Every generator implements the small contract in
`routing_engine/generators/base.py` and is registered in
`routing_engine/generators/__init__.py`.

Implemented:

- Happ → `happ-routing.json`, `happ-routing-link.txt`;
- Xray/3x-ui → `3x-ui-routing.json`.

Planned adapters can be added independently:

- sing-box;
- Clash/Mihomo;
- Keenetic.

To add one, create a serializer, register it, and add a YAML file under
`targets/`. Do not duplicate policy ordering or fallback logic in the adapter;
consume `RoutingPolicy.ordered_rules()` and `RoutingPolicy.fallback`.

## Release artifacts

The daily GitHub workflow builds and validates:

| File | Purpose |
| --- | --- |
| `geosite.dat` | v2fly lists plus local custom categories |
| `geoip.dat` | Loyalsoldier database verified against upstream SHA-256 |
| `happ-routing.json` | Happ routing profile |
| `happ-routing-link.txt` | Happ `happ://routing/onadd/...` import link |
| `3x-ui-routing.json` | Xray routing object for 3x-ui |
| `release.json` | Source provenance, sizes and digests |
| `SHA256SUMS` | Release checksums |

Latest release base URL:

```text
https://github.com/ldkt/happ-routing/releases/latest/download
```

## Using Happ

Open `happ-routing-link.txt` from the latest release on a device with Happ and
confirm profile import. The profile points to the latest `geoip.dat` and
`geosite.dat`, preserving the behavior of the original Happ-specific project.
Happ-only DNS and release URL settings live in `targets/happ.yaml`.

## Using Xray and 3x-ui

Download `geoip.dat` and `geosite.dat` into the Xray binary directory, or add
them in **Xray → Geofiles → Custom GeoSite / GeoIP sources**. Custom geofiles
are referenced using Xray's external form, for example:

```text
ext:geosite_happ.dat:routing-proxy
ext:geoip_happ.dat:private
```

Insert `3x-ui-routing.json` into the Xray routing configuration. Adjust
`targets/xray.yaml` if the server uses outbound tags other than `direct`,
`proxy` and `block`.

## Home Assistant через HACS

Добавьте `https://github.com/ldkt/happ-routing` в HACS как custom repository типа **Integration**, установите **Universal Routing Database**, перезапустите Home Assistant и выберите **Настройки → Устройства и службы → Добавить интеграцию → Universal Routing Database**. Config Flow запросит только базовый URL URDB API и автоматически создаст устройство, два сенсора, три кнопки и Diagnostics; YAML и ручное редактирование `configuration.yaml` не используются.

## Development

Requirements: Git, Go, Python 3 and curl.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
make PYTHON=.venv/bin/python configs
make PYTHON=.venv/bin/python test
make PYTHON=.venv/bin/python build
```

`make configs` generates client artifacts without downloading geodata. The full
build compiles `geosite.dat`, downloads and verifies `geoip.dat`, writes release
metadata and validates the complete output.

CI runs unit tests and a full build for every pull request. The release workflow
runs daily at 03:17 UTC and can also be started manually. Binary output in
`dist/` is intentionally not committed.

Data sources retain their respective licenses. Repository code is MIT licensed.
