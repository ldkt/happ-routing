"""Serialize canonical policy into Xray/3x-ui routing JSON."""

from __future__ import annotations

import json
from typing import Any, Mapping, Sequence

from ..model import RoutingPolicy
from .base import GeneratedFile


class XrayGenerator:
    def generate(
        self, policy: RoutingPolicy, settings: Mapping[str, Any]
    ) -> Sequence[GeneratedFile]:
        tags = settings["outbound_tags"]
        result: list[dict[str, Any]] = []
        for action, rules in policy.ordered_rules():
            tag = tags[action.value]
            if rules.domains:
                result.append({"type": "field", "outboundTag": tag, "domain": list(rules.domains)})
            if rules.ips:
                result.append({"type": "field", "outboundTag": tag, "ip": list(rules.ips)})
        result.append({
            "type": "field",
            "network": "tcp,udp",
            "outboundTag": tags[policy.fallback.value],
        })
        document = {"domainStrategy": policy.domain_strategy, "rules": result}
        return (GeneratedFile("3x-ui-routing.json", json.dumps(document, indent=2) + "\n"),)
