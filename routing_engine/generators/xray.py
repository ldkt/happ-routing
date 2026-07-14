"""Serialize canonical policy into Xray/3x-ui routing JSON."""

from __future__ import annotations

import json
from typing import Any, Mapping, Sequence

from ..model import NormalizedPolicy
from .base import GeneratedFile, collect_compatible_rules


class XrayGenerator:
    def generate(
        self, policy: NormalizedPolicy, settings: Mapping[str, Any]
    ) -> Sequence[GeneratedFile]:
        tags = settings["outbound_tags"]
        buckets = collect_compatible_rules(policy, settings)
        result: list[dict[str, Any]] = []
        ordered_roles: list[str] = []
        bindings = settings["egress_bindings"]
        for rule in policy.enabled_rules():
            role = bindings[rule.action.egress]
            if role not in ordered_roles:
                ordered_roles.append(role)
        for role in ordered_roles:
            rules = buckets[role]
            tag = tags[role]
            if rules["domains"]:
                result.append({"type": "field", "outboundTag": tag, "domain": rules["domains"]})
            if rules["ips"]:
                result.append({"type": "field", "outboundTag": tag, "ip": rules["ips"]})
        fallback_role = bindings[policy.fallback]
        result.append({
            "type": "field",
            "network": "tcp,udp",
            "outboundTag": tags[fallback_role],
        })
        document = {"domainStrategy": settings["domain_strategy"], "rules": result}
        return (GeneratedFile("3x-ui-routing.json", json.dumps(document, indent=2) + "\n"),)
