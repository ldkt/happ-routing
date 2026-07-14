#!/usr/bin/env python3
"""Generate Happ and Xray/3x-ui routing artifacts from one JSON source."""

from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def load_config(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def happ_profile(config: dict[str, Any], release_base_url: str) -> dict[str, Any]:
    dns = config["dns"]
    rules = config["rules"]
    return {
        "Name": config["name"],
        "GlobalProxy": str(config["globalProxy"]).lower(),
        "RemoteDNSType": dns["remote"]["type"],
        "RemoteDNSDomain": dns["remote"]["domain"],
        "RemoteDNSIP": dns["remote"]["ip"],
        "DomesticDNSType": dns["domestic"]["type"],
        "DomesticDNSDomain": dns["domestic"]["domain"],
        "DomesticDNSIP": dns["domestic"]["ip"],
        "Geoipurl": f"{release_base_url}/geoip.dat",
        "Geositeurl": f"{release_base_url}/geosite.dat",
        "DnsHosts": {
            "cloudflare-dns.com": dns["remote"]["ip"],
            "dns.google": dns["domestic"]["ip"],
        },
        "DirectSites": rules["directSites"],
        "DirectIp": rules["directIp"],
        "ProxySites": rules["proxySites"],
        "ProxyIp": rules["proxyIp"],
        "BlockSites": rules["blockSites"],
        "BlockIp": rules["blockIp"],
        "DomainStrategy": config["domainStrategy"],
    }


def xray_routing(config: dict[str, Any]) -> dict[str, Any]:
    rules = config["rules"]
    tags = config["outboundTags"]
    result: list[dict[str, Any]] = []

    def add(tag: str, field: str, values: list[str]) -> None:
        if values:
            result.append({"type": "field", "outboundTag": tag, field: values})

    # Xray uses first-match semantics, so block and explicit direct rules win.
    add(tags["block"], "domain", rules["blockSites"])
    add(tags["block"], "ip", rules["blockIp"])
    add(tags["direct"], "domain", rules["directSites"])
    add(tags["direct"], "ip", rules["directIp"])
    add(tags["proxy"], "domain", rules["proxySites"])
    add(tags["proxy"], "ip", rules["proxyIp"])
    result.append({
        "type": "field",
        "network": "tcp,udp",
        "outboundTag": tags["proxy"] if config["globalProxy"] else tags["direct"],
    })
    return {"domainStrategy": config["domainStrategy"], "rules": result}


def dump_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def generate(config_path: Path, output: Path, release_base_url: str) -> None:
    config = load_config(config_path)
    output.mkdir(parents=True, exist_ok=True)
    profile = happ_profile(config, release_base_url.rstrip("/"))
    serialized = json.dumps(profile, ensure_ascii=False, separators=(",", ":"))
    encoded = base64.b64encode(serialized.encode()).decode()
    dump_json(output / "happ-routing.json", profile)
    (output / "happ-routing-link.txt").write_text(
        f"happ://routing/onadd/{encoded}\n", encoding="utf-8"
    )
    dump_json(output / "3x-ui-routing.json", xray_routing(config))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "config/routing.json")
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    parser.add_argument(
        "--release-base-url",
        default="https://github.com/ldkt/happ-routing/releases/latest/download",
    )
    args = parser.parse_args()
    generate(args.config, args.output, args.release_base_url)


if __name__ == "__main__":
    main()
