"""Serialize canonical policy into Happ routing artifacts."""

from __future__ import annotations

import base64
import json
from typing import Any, Mapping, Sequence
from urllib.parse import urlparse

from ..model import Action, RoutingPolicy
from .base import GeneratedFile


class HappGenerator:
    def generate(
        self, policy: RoutingPolicy, settings: Mapping[str, Any]
    ) -> Sequence[GeneratedFile]:
        dns = settings["dns"]
        remote_host = urlparse(dns["remote"]["domain"]).hostname
        domestic_host = urlparse(dns["domestic"]["domain"]).hostname
        release_url = str(settings["release_base_url"]).rstrip("/")
        rules = policy.rules
        profile = {
            "Name": settings.get("name", policy.name),
            "GlobalProxy": str(bool(settings.get("global_proxy", False))).lower(),
            "RemoteDNSType": dns["remote"]["type"],
            "RemoteDNSDomain": dns["remote"]["domain"],
            "RemoteDNSIP": dns["remote"]["ip"],
            "DomesticDNSType": dns["domestic"]["type"],
            "DomesticDNSDomain": dns["domestic"]["domain"],
            "DomesticDNSIP": dns["domestic"]["ip"],
            "Geoipurl": f"{release_url}/geoip.dat",
            "Geositeurl": f"{release_url}/geosite.dat",
            "DnsHosts": {
                remote_host: dns["remote"]["ip"],
                domestic_host: dns["domestic"]["ip"],
            },
            "DirectSites": list(rules[Action.DIRECT].domains),
            "DirectIp": list(rules[Action.DIRECT].ips),
            "ProxySites": list(rules[Action.PROXY].domains),
            "ProxyIp": list(rules[Action.PROXY].ips),
            "BlockSites": list(rules[Action.BLOCK].domains),
            "BlockIp": list(rules[Action.BLOCK].ips),
            "DomainStrategy": policy.domain_strategy,
        }
        pretty = json.dumps(profile, ensure_ascii=False, indent=2) + "\n"
        compact = json.dumps(profile, ensure_ascii=False, separators=(",", ":"))
        link = "happ://routing/onadd/" + base64.b64encode(compact.encode()).decode() + "\n"
        return (
            GeneratedFile("happ-routing.json", pretty),
            GeneratedFile("happ-routing-link.txt", link),
        )
