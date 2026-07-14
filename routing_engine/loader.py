"""Strict parser for canonical Routing Policy schema version 1."""

from __future__ import annotations

import ipaddress
import re
from pathlib import Path
from typing import Any, Callable, Mapping, TypeVar

import yaml

from .model import (
    ASN,
    Action,
    AllMatcher,
    AnyMatcher,
    Category,
    CategoryRef,
    Country,
    DestinationCIDR,
    DestinationIP,
    Direction,
    Domain,
    DomainEntry,
    DomainKeyword,
    DomainRegex,
    DomainSet,
    DomainSetRef,
    DomainSuffix,
    Egress,
    IPEntry,
    IPSet,
    IPSetRef,
    Matcher,
    Metadata,
    Network,
    NotMatcher,
    Object,
    ObjectRef,
    PackageName,
    PolicyError,
    Port,
    PortRange,
    Process,
    Protocol,
    ResourceSource,
    RoutingPolicy,
    Rule,
    SourceCIDR,
    SourceIP,
)


IDENTIFIER = re.compile(r"^[a-z][a-z0-9-]{0,62}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
COUNTRY = re.compile(r"^[A-Z]{2}$")
ISO_COUNTRIES = set(
    "AD AE AF AG AI AL AM AO AQ AR AS AT AU AW AX AZ BA BB BD BE BF BG BH BI "
    "BJ BL BM BN BO BQ BR BS BT BV BW BY BZ CA CC CD CF CG CH CI CK CL CM CN "
    "CO CR CU CV CW CX CY CZ DE DJ DK DM DO DZ EC EE EG EH ER ES ET FI FJ FK "
    "FM FO FR GA GB GD GE GF GG GH GI GL GM GN GP GQ GR GS GT GU GW GY HK HM "
    "HN HR HT HU ID IE IL IM IN IO IQ IR IS IT JE JM JO JP KE KG KH KI KM KN "
    "KP KR KW KY KZ LA LB LC LI LK LR LS LT LU LV LY MA MC MD ME MF MG MH MK "
    "ML MM MN MO MP MQ MR MS MT MU MV MW MX MY MZ NA NC NE NF NG NI NL NO NP "
    "NR NU NZ OM PA PE PF PG PH PK PL PM PN PR PS PT PW PY QA RE RO RS RU RW "
    "SA SB SC SD SE SG SH SI SJ SK SL SM SN SO SR SS ST SV SX SY SZ TC TD TF "
    "TG TH TJ TK TL TM TN TO TR TT TV TW TZ UA UG UM US UY UZ VA VC VE VG VI "
    "VN VU WF WS YE YT ZA ZM ZW".split()
)
PROTOCOLS = {"http", "tls", "quic", "dns", "bittorrent"}
NETWORKS = {"tcp", "udp", "icmp"}
T = TypeVar("T")


class StrictSafeLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""


def _construct_mapping(loader: StrictSafeLoader, node: yaml.MappingNode, deep: bool = False):
    loader.flatten_mapping(node)
    result: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise PolicyError(f"duplicate YAML key: {key!r}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


StrictSafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping
)


def _load_yaml(path: Path) -> Mapping[str, Any]:
    try:
        value = yaml.load(path.read_text(encoding="utf-8"), Loader=StrictSafeLoader)
    except PolicyError:
        raise
    except (OSError, yaml.YAMLError) as error:
        raise PolicyError(f"cannot load {path}: {error}") from error
    return _mapping(value, str(path))


def _mapping(value: Any, path: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise PolicyError(f"{path} must be a mapping")
    if not all(isinstance(key, str) for key in value):
        raise PolicyError(f"{path} keys must be strings")
    return value


def _list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise PolicyError(f"{path} must be a list")
    return value


def _strict_keys(
    value: Mapping[str, Any], path: str, *, required: set[str], optional: set[str] = set()
) -> None:
    missing = required - value.keys()
    unknown = value.keys() - required - optional
    if missing:
        raise PolicyError(f"{path} is missing fields: {', '.join(sorted(missing))}")
    if unknown:
        raise PolicyError(f"{path} has unknown fields: {', '.join(sorted(unknown))}")


def _string(value: Any, path: str, *, nonempty: bool = True) -> str:
    if not isinstance(value, str):
        raise PolicyError(f"{path} must be a string")
    if nonempty and not value.strip():
        raise PolicyError(f"{path} must not be empty")
    return value.strip() if nonempty else value


def _integer(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise PolicyError(f"{path} must be an integer")
    return value


def _boolean(value: Any, path: str) -> bool:
    if not isinstance(value, bool):
        raise PolicyError(f"{path} must be a boolean")
    return value


def _identifier(value: Any, path: str) -> str:
    result = _string(value, path)
    if not IDENTIFIER.fullmatch(result):
        raise PolicyError(f"{path} must match {IDENTIFIER.pattern}")
    return result


def _optional_string(value: Mapping[str, Any], key: str, path: str) -> str | None:
    return _string(value[key], f"{path}.{key}") if key in value else None


def _unique(values: list[T], key: Callable[[T], Any], path: str) -> tuple[T, ...]:
    result: list[T] = []
    seen: set[Any] = set()
    for value in values:
        marker = key(value)
        if marker in seen:
            raise PolicyError(f"{path} contains duplicate normalized value: {marker!r}")
        seen.add(marker)
        result.append(value)
    return tuple(result)


def _domain(value: Any, path: str) -> str:
    raw = _string(value, path).lower()
    if raw.endswith("."):
        raw = raw[:-1]
    if not raw or any(character in raw for character in "/:@"):
        raise PolicyError(f"{path} must be a domain name without scheme, port or path")
    try:
        normalized = raw.encode("idna").decode("ascii")
    except UnicodeError as error:
        raise PolicyError(f"{path} is not a valid IDNA domain") from error
    if len(normalized) > 253:
        raise PolicyError(f"{path} exceeds 253 characters")
    labels = normalized.split(".")
    if any(not label or len(label) > 63 for label in labels):
        raise PolicyError(f"{path} contains an invalid domain label")
    if any(label.startswith("-") or label.endswith("-") for label in labels):
        raise PolicyError(f"{path} contains a label with an invalid hyphen")
    if any(not re.fullmatch(r"[a-z0-9-]+", label) for label in labels):
        raise PolicyError(f"{path} contains characters invalid in a domain label")
    return normalized


def _ip(value: Any, path: str) -> str:
    try:
        return str(ipaddress.ip_address(_string(value, path)))
    except ValueError as error:
        raise PolicyError(f"{path} is not a valid IP address") from error


def _cidr(value: Any, path: str) -> str:
    try:
        return str(ipaddress.ip_network(_string(value, path), strict=True))
    except ValueError as error:
        raise PolicyError(f"{path} is not a canonical CIDR prefix") from error


def _direction(value: Any, path: str) -> Direction:
    try:
        return Direction(_string(value, path))
    except ValueError as error:
        raise PolicyError(f"{path} must be source or destination") from error


def _port(value: Any, path: str) -> int:
    result = _integer(value, path)
    if not 1 <= result <= 65535:
        raise PolicyError(f"{path} must be between 1 and 65535")
    return result


def _validate_re2(pattern: str, path: str) -> str:
    if not pattern:
        raise PolicyError(f"{path} must not be empty")
    unsupported = ("(?=", "(?!", "(?<=", "(?<!", "(?P=", "(?>")
    if any(token in pattern for token in unsupported) or re.search(r"\\[1-9]", pattern):
        raise PolicyError(f"{path} uses a construct unsupported by RE2")
    try:
        re.compile(pattern)
    except re.error as error:
        raise PolicyError(f"{path} is not a valid regular expression: {error}") from error
    return pattern


def _source(value: Any, path: str) -> ResourceSource:
    raw = _mapping(value, path)
    _strict_keys(
        raw,
        path,
        required={"provider", "resource"},
        optional={"revision", "sha256"},
    )
    digest = _optional_string(raw, "sha256", path)
    if digest is not None and not SHA256.fullmatch(digest):
        raise PolicyError(f"{path}.sha256 must be 64 lowercase hexadecimal characters")
    return ResourceSource(
        provider=_identifier(raw["provider"], f"{path}.provider"),
        resource=_identifier(raw["resource"], f"{path}.resource"),
        revision=_optional_string(raw, "revision", path),
        sha256=digest,
    )


def _domain_entry(value: Any, path: str) -> DomainEntry:
    raw = _mapping(value, path)
    if len(raw) != 1:
        raise PolicyError(f"{path} must contain exactly one domain matcher")
    key, item = next(iter(raw.items()))
    if key == "domain":
        return Domain(_domain(item, f"{path}.domain"))
    if key == "domain_suffix":
        return DomainSuffix(_domain(item, f"{path}.domain_suffix"))
    if key == "domain_keyword":
        return DomainKeyword(_string(item, f"{path}.domain_keyword").lower())
    if key == "domain_regex":
        regex = _mapping(item, f"{path}.domain_regex")
        _strict_keys(regex, f"{path}.domain_regex", required={"pattern", "dialect"})
        dialect = _string(regex["dialect"], f"{path}.domain_regex.dialect")
        if dialect != "re2":
            raise PolicyError(f"{path}.domain_regex.dialect must be re2")
        pattern = _validate_re2(
            _string(regex["pattern"], f"{path}.domain_regex.pattern"),
            f"{path}.domain_regex.pattern",
        )
        return DomainRegex(pattern, dialect)
    raise PolicyError(f"{path} has unknown domain matcher: {key}")


def _country(value: Any, path: str) -> Country:
    raw = _mapping(value, path)
    _strict_keys(raw, path, required={"code", "direction", "ip_set"})
    code = _string(raw["code"], f"{path}.code").upper()
    if not COUNTRY.fullmatch(code) or code not in ISO_COUNTRIES:
        raise PolicyError(f"{path}.code must be an ISO alpha-2 code")
    return Country(
        code,
        _direction(raw["direction"], f"{path}.direction"),
        _identifier(raw["ip_set"], f"{path}.ip_set"),
    )


def _asn(value: Any, path: str) -> ASN:
    raw = _mapping(value, path)
    _strict_keys(raw, path, required={"number", "direction", "ip_set"})
    number = raw["number"]
    if isinstance(number, str) and re.fullmatch(r"AS[0-9]+", number.upper()):
        number = int(number[2:])
    number = _integer(number, f"{path}.number")
    if not 0 <= number <= 4294967295:
        raise PolicyError(f"{path}.number is outside the ASN range")
    return ASN(
        number,
        _direction(raw["direction"], f"{path}.direction"),
        _identifier(raw["ip_set"], f"{path}.ip_set"),
    )


def _ip_entry(value: Any, path: str) -> IPEntry:
    raw = _mapping(value, path)
    if len(raw) != 1:
        raise PolicyError(f"{path} must contain exactly one IP matcher")
    key, item = next(iter(raw.items()))
    if key in {"ip", "destination_ip"}:
        return DestinationIP(_ip(item, f"{path}.{key}"))
    if key in {"cidr", "destination_cidr"}:
        return DestinationCIDR(_cidr(item, f"{path}.{key}"))
    if key == "source_ip":
        return SourceIP(_ip(item, f"{path}.source_ip"))
    if key == "source_cidr":
        return SourceCIDR(_cidr(item, f"{path}.source_cidr"))
    if key == "country":
        return _country(item, f"{path}.country")
    if key == "asn":
        return _asn(item, f"{path}.asn")
    raise PolicyError(f"{path} has unknown IP matcher: {key}")


def _domain_set(identifier: str, value: Any, path: str) -> DomainSet:
    raw = _mapping(value, path)
    _strict_keys(raw, path, required=set(), optional={"description", "entries", "source"})
    has_entries = "entries" in raw
    has_source = "source" in raw
    if has_entries == has_source:
        raise PolicyError(f"{path} must contain exactly one of entries or source")
    entries: tuple[DomainEntry, ...] = ()
    source = None
    if has_entries:
        values = [
            _domain_entry(item, f"{path}.entries[{index}]")
            for index, item in enumerate(_list(raw["entries"], f"{path}.entries"))
        ]
        if not values:
            raise PolicyError(f"{path}.entries must not be empty")
        entries = _unique(values, repr, f"{path}.entries")
    else:
        source = _source(raw["source"], f"{path}.source")
    return DomainSet(identifier, _optional_string(raw, "description", path), entries, source)


def _ip_set(identifier: str, value: Any, path: str) -> IPSet:
    raw = _mapping(value, path)
    _strict_keys(raw, path, required=set(), optional={"description", "entries", "source"})
    has_entries = "entries" in raw
    has_source = "source" in raw
    if has_entries == has_source:
        raise PolicyError(f"{path} must contain exactly one of entries or source")
    entries: tuple[IPEntry, ...] = ()
    source = None
    if has_entries:
        values = [
            _ip_entry(item, f"{path}.entries[{index}]")
            for index, item in enumerate(_list(raw["entries"], f"{path}.entries"))
        ]
        if not values:
            raise PolicyError(f"{path}.entries must not be empty")
        entries = _unique(values, repr, f"{path}.entries")
    else:
        source = _source(raw["source"], f"{path}.source")
    return IPSet(identifier, _optional_string(raw, "description", path), entries, source)


def _port_matcher(value: Any, path: str) -> Port:
    raw = _mapping(value, path)
    _strict_keys(raw, path, required={"direction", "value"})
    return Port(
        _direction(raw["direction"], f"{path}.direction"),
        _port(raw["value"], f"{path}.value"),
    )


def _port_range(value: Any, path: str) -> PortRange:
    raw = _mapping(value, path)
    _strict_keys(raw, path, required={"direction", "from", "to"})
    start = _port(raw["from"], f"{path}.from")
    end = _port(raw["to"], f"{path}.to")
    if start > end:
        raise PolicyError(f"{path}.from must be less than or equal to to")
    return PortRange(_direction(raw["direction"], f"{path}.direction"), start, end)


def _matcher(value: Any, path: str) -> Matcher:
    raw = _mapping(value, path)
    if len(raw) != 1:
        raise PolicyError(f"{path} must contain exactly one matcher key")
    key, item = next(iter(raw.items()))
    if key in {"domain", "domain_suffix", "domain_keyword", "domain_regex"}:
        return _domain_entry({key: item}, path)
    if key in {
        "ip", "cidr", "destination_ip", "destination_cidr", "source_ip",
        "source_cidr", "country", "asn",
    }:
        return _ip_entry({key: item}, path)
    if key == "domain_set":
        return DomainSetRef(_identifier(item, f"{path}.domain_set"))
    if key == "ip_set":
        return IPSetRef(_identifier(item, f"{path}.ip_set"))
    if key == "object":
        return ObjectRef(_identifier(item, f"{path}.object"))
    if key == "category":
        return CategoryRef(_identifier(item, f"{path}.category"))
    if key == "port":
        return _port_matcher(item, f"{path}.port")
    if key == "port_range":
        return _port_range(item, f"{path}.port_range")
    if key == "protocol":
        protocol = _string(item, f"{path}.protocol").lower()
        if protocol not in PROTOCOLS:
            raise PolicyError(f"{path}.protocol is not in the schema-v1 registry")
        return Protocol(protocol)
    if key == "network":
        network = _string(item, f"{path}.network").lower()
        if network not in NETWORKS:
            raise PolicyError(f"{path}.network is not in the schema-v1 registry")
        return Network(network)
    if key == "process":
        process = _mapping(item, f"{path}.process")
        _strict_keys(process, f"{path}.process", required={"name"})
        return Process(_string(process["name"], f"{path}.process.name"))
    if key == "package_name":
        return PackageName(_string(item, f"{path}.package_name"))
    if key in {"any", "all"}:
        children = tuple(
            _matcher(child, f"{path}.{key}[{index}]")
            for index, child in enumerate(_list(item, f"{path}.{key}"))
        )
        if len(children) < 2:
            raise PolicyError(f"{path}.{key} must contain at least two matchers")
        return AnyMatcher(children) if key == "any" else AllMatcher(children)
    if key == "not":
        return NotMatcher(_matcher(item, f"{path}.not"))
    raise PolicyError(f"{path} has unknown matcher: {key}")


def _metadata(value: Any, path: str) -> Metadata:
    raw = _mapping(value, path)
    _strict_keys(
        raw,
        path,
        required={"name"},
        optional={"revision", "description", "owners", "labels"},
    )
    revision = raw.get("revision")
    if revision is not None and (
        isinstance(revision, bool) or not isinstance(revision, (str, int))
    ):
        raise PolicyError(f"{path}.revision must be a string or integer")
    owners = tuple(
        _string(owner, f"{path}.owners[{index}]")
        for index, owner in enumerate(_list(raw.get("owners", []), f"{path}.owners"))
    )
    labels_raw = _mapping(raw.get("labels", {}), f"{path}.labels")
    labels = {
        _string(key, f"{path}.labels key"): _string(value, f"{path}.labels.{key}")
        for key, value in labels_raw.items()
    }
    return Metadata(
        _string(raw["name"], f"{path}.name"),
        revision,
        _optional_string(raw, "description", path),
        owners,
        labels,
    )


def _named_mapping(
    value: Any, path: str, parser: Callable[[str, Any, str], T]
) -> dict[str, T]:
    raw = _mapping(value, path)
    result: dict[str, T] = {}
    for identifier, item in raw.items():
        normalized = _identifier(identifier, f"{path} key")
        if normalized in result:
            raise PolicyError(f"{path} contains duplicate identifier: {normalized}")
        result[normalized] = parser(normalized, item, f"{path}.{normalized}")
    return result


def _egress(identifier: str, value: Any, path: str) -> Egress:
    raw = _mapping(value, path)
    _strict_keys(raw, path, required=set(), optional={"description"})
    return Egress(identifier, _optional_string(raw, "description", path))


def _object(identifier: str, value: Any, path: str) -> Object:
    raw = _mapping(value, path)
    _strict_keys(
        raw, path, required=set(), optional={"description", "domain_sets", "ip_sets"}
    )
    domain_sets = tuple(
        _identifier(item, f"{path}.domain_sets[{index}]")
        for index, item in enumerate(_list(raw.get("domain_sets", []), f"{path}.domain_sets"))
    )
    ip_sets = tuple(
        _identifier(item, f"{path}.ip_sets[{index}]")
        for index, item in enumerate(_list(raw.get("ip_sets", []), f"{path}.ip_sets"))
    )
    if not domain_sets and not ip_sets:
        raise PolicyError(f"{path} must reference at least one Domain Set or IP Set")
    if len(set(domain_sets)) != len(domain_sets) or len(set(ip_sets)) != len(ip_sets):
        raise PolicyError(f"{path} contains duplicate Set references")
    return Object(identifier, _optional_string(raw, "description", path), domain_sets, ip_sets)


def _category(identifier: str, value: Any, path: str) -> Category:
    raw = _mapping(value, path)
    _strict_keys(raw, path, required={"objects"}, optional={"description"})
    objects = tuple(
        _identifier(item, f"{path}.objects[{index}]")
        for index, item in enumerate(_list(raw["objects"], f"{path}.objects"))
    )
    if not objects:
        raise PolicyError(f"{path}.objects must not be empty")
    if len(set(objects)) != len(objects):
        raise PolicyError(f"{path}.objects contains duplicate references")
    return Category(identifier, _optional_string(raw, "description", path), objects)


def _rule(value: Any, index: int, path: str) -> Rule:
    raw = _mapping(value, path)
    _strict_keys(
        raw,
        path,
        required={"id", "match", "action"},
        optional={"description", "priority", "enabled"},
    )
    action_raw = _mapping(raw["action"], f"{path}.action")
    _strict_keys(action_raw, f"{path}.action", required={"egress"})
    priority = _integer(raw.get("priority", 0), f"{path}.priority")
    if not -(2**31) <= priority <= 2**31 - 1:
        raise PolicyError(f"{path}.priority is outside signed 32-bit range")
    return Rule(
        id=_identifier(raw["id"], f"{path}.id"),
        matcher=_matcher(raw["match"], f"{path}.match"),
        action=Action(_identifier(action_raw["egress"], f"{path}.action.egress")),
        description=_optional_string(raw, "description", path),
        priority=priority,
        enabled=_boolean(raw.get("enabled", True), f"{path}.enabled"),
        source_index=index,
    )


def load_policy(path: Path) -> RoutingPolicy:
    """Load policy input and return only the canonical schema-v1 model.

    Legacy action-bucket input is accepted temporarily and migrated at this
    boundary. No legacy representation crosses into normalization or code
    generation.
    """

    policy_dir = path if path.is_dir() else path.parent
    policy_path = policy_dir / "policy.yaml" if path.is_dir() else path
    raw = _load_yaml(policy_path)
    if "schema_version" not in raw and "version" in raw:
        from .legacy import migrate_legacy_policy

        return migrate_legacy_policy(policy_dir, raw)

    path = policy_path
    _strict_keys(
        raw,
        "policy",
        required={"schema_version", "kind", "metadata", "egresses", "rules", "fallback"},
        optional={"domain_sets", "ip_sets", "objects", "categories"},
    )
    schema_version = _integer(raw["schema_version"], "policy.schema_version")
    if schema_version != 1:
        raise PolicyError(f"unsupported policy schema version: {schema_version}")
    kind = _string(raw["kind"], "policy.kind")
    if kind != "RoutingPolicy":
        raise PolicyError("policy.kind must be RoutingPolicy")

    egresses = _named_mapping(raw["egresses"], "policy.egresses", _egress)
    if not egresses:
        raise PolicyError("policy.egresses must not be empty")
    domain_sets = _named_mapping(
        raw.get("domain_sets", {}), "policy.domain_sets", _domain_set
    )
    ip_sets = _named_mapping(raw.get("ip_sets", {}), "policy.ip_sets", _ip_set)
    objects = _named_mapping(raw.get("objects", {}), "policy.objects", _object)
    categories = _named_mapping(
        raw.get("categories", {}), "policy.categories", _category
    )
    rules = tuple(
        _rule(value, index, f"policy.rules[{index}]")
        for index, value in enumerate(_list(raw["rules"], "policy.rules"))
    )
    identifiers = [rule.id for rule in rules]
    if len(set(identifiers)) != len(identifiers):
        raise PolicyError("policy.rules contains duplicate Rule IDs")
    fallback = _identifier(raw["fallback"], "policy.fallback")
    return RoutingPolicy(
        schema_version,
        kind,
        _metadata(raw["metadata"], "policy.metadata"),
        egresses,
        domain_sets,
        ip_sets,
        objects,
        categories,
        rules,
        fallback,
    )


def load_target(path: Path) -> dict[str, Any]:
    """Load existing untyped target settings; typing belongs to Phase 2."""

    target = dict(_load_yaml(path))
    if not isinstance(target.get("generator"), str):
        raise PolicyError(f"{path} must declare a generator")
    return target
