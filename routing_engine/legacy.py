"""Temporary legacy action-bucket to canonical schema-v1 migration.

This is the only module that understands the pre-v1 policy layout. Its public
boundary returns ``RoutingPolicy`` so all downstream code remains canonical.
Remove this compatibility adapter after v1.0.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .loader import (
    _cidr,
    _domain,
    _identifier,
    _integer,
    _ip,
    _list,
    _mapping,
    _string,
    _strict_keys,
    _validate_re2,
    _load_yaml,
)
from .model import (
    Action,
    Category,
    DestinationCIDR,
    DestinationIP,
    Domain,
    DomainEntry,
    DomainKeyword,
    DomainRegex,
    DomainSet,
    DomainSuffix,
    Egress,
    IPEntry,
    IPSet,
    Metadata,
    Object,
    ObjectRef,
    PolicyError,
    ResourceSource,
    RoutingPolicy,
    Rule,
)


_ACTIONS = {"direct": "internet", "proxy": "vpn", "block": "block"}


def migrate_legacy_policy(
    policy_dir: Path, metadata: Mapping[str, Any]
) -> RoutingPolicy:
    """Parse a legacy directory and migrate it into a canonical model."""

    _strict_keys(
        metadata,
        "legacy policy",
        required={"version", "name", "domain_strategy", "action_order", "fallback"},
    )
    version = _integer(metadata["version"], "legacy policy.version")
    if version != 1:
        raise PolicyError(f"unsupported legacy policy version: {version}")
    strategy = _string(metadata["domain_strategy"], "legacy policy.domain_strategy")
    if strategy != "IPIfNonMatch":
        raise PolicyError(
            "legacy policy.domain_strategy must be IPIfNonMatch for compatible migration"
        )

    action_order = tuple(
        _action(item, f"legacy policy.action_order[{index}]")
        for index, item in enumerate(
            _list(metadata["action_order"], "legacy policy.action_order")
        )
    )
    if set(action_order) != set(_ACTIONS) or len(action_order) != len(_ACTIONS):
        raise PolicyError("legacy policy.action_order must contain direct, proxy and block once")
    fallback_action = _action(metadata["fallback"], "legacy policy.fallback")

    domain_sets: dict[str, DomainSet] = {}
    ip_sets: dict[str, IPSet] = {}
    objects: dict[str, Object] = {}
    categories: dict[str, Category] = {}
    rules: list[Rule] = []

    for action in action_order:
        bucket_path = policy_dir / f"{action}.yaml"
        bucket = _load_yaml(bucket_path)
        _strict_keys(bucket, f"legacy {action}", required={"domains", "ips"})
        object_ids: list[str] = []

        domain_values = _list(bucket["domains"], f"legacy {action}.domains")
        for index, raw_value in enumerate(domain_values):
            set_id = f"legacy-{action}-domain-{index + 1}"
            domain_sets[set_id] = _legacy_domain_set(
                set_id, raw_value, f"legacy {action}.domains[{index}]"
            )
            object_id = set_id
            objects[object_id] = Object(object_id, domain_sets=(set_id,))
            object_ids.append(object_id)

        ip_values = _list(bucket["ips"], f"legacy {action}.ips")
        for index, raw_value in enumerate(ip_values):
            set_id = f"legacy-{action}-ip-{index + 1}"
            ip_sets[set_id] = _legacy_ip_set(
                set_id, raw_value, f"legacy {action}.ips[{index}]"
            )
            object_id = set_id
            objects[object_id] = Object(object_id, ip_sets=(set_id,))
            object_ids.append(object_id)

        if object_ids:
            category_id = f"legacy-{action}"
            categories[category_id] = Category(category_id, objects=tuple(object_ids))
        for object_id in object_ids:
            rules.append(
                Rule(
                    id=f"rule-{object_id}",
                    matcher=ObjectRef(object_id),
                    action=Action(_ACTIONS[action]),
                    source_index=len(rules),
                )
            )

    return RoutingPolicy(
        schema_version=1,
        kind="RoutingPolicy",
        metadata=Metadata(name=_string(metadata["name"], "legacy policy.name"), revision=1),
        egresses={name: Egress(name) for name in _ACTIONS.values()},
        domain_sets=domain_sets,
        ip_sets=ip_sets,
        objects=objects,
        categories=categories,
        rules=tuple(rules),
        fallback=_ACTIONS[fallback_action],
    )


def _action(value: Any, path: str) -> str:
    action = _identifier(value, path)
    if action not in _ACTIONS:
        raise PolicyError(f"{path} must be direct, proxy or block")
    return action


def _legacy_domain_set(identifier: str, value: Any, path: str) -> DomainSet:
    raw = _string(value, path)
    if raw.startswith("geosite:"):
        resource = _identifier(raw.removeprefix("geosite:"), path)
        return DomainSet(identifier, source=ResourceSource("v2fly-geosite", resource))
    entry: DomainEntry
    if raw.startswith("full:"):
        entry = Domain(_domain(raw.removeprefix("full:"), path))
    elif raw.startswith("domain:"):
        entry = DomainSuffix(_domain(raw.removeprefix("domain:"), path))
    elif raw.startswith("keyword:"):
        entry = DomainKeyword(_string(raw.removeprefix("keyword:"), path))
    elif raw.startswith("regexp:"):
        pattern = raw.removeprefix("regexp:")
        entry = DomainRegex(_validate_re2(pattern, path))
    else:
        entry = DomainSuffix(_domain(raw, path))
    return DomainSet(identifier, entries=(entry,))


def _legacy_ip_set(identifier: str, value: Any, path: str) -> IPSet:
    raw = _string(value, path)
    if raw.startswith("geoip:"):
        resource = _identifier(raw.removeprefix("geoip:"), path)
        return IPSet(identifier, source=ResourceSource("v2fly-geoip", resource))
    entry: IPEntry
    if "/" in raw:
        entry = DestinationCIDR(_cidr(raw, path))
    else:
        entry = DestinationIP(_ip(raw, path))
    return IPSet(identifier, entries=(entry,))
