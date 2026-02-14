from __future__ import annotations

from ipaddress import ip_address, ip_network
from typing import Iterable, Mapping

from app.db.models.ip_rule import IPRuleAction


def evaluate_ip_rules(
    client_ip: str,
    rules: Iterable[Mapping[str, object]],
) -> IPRuleAction | None:
    try:
        ip = ip_address(client_ip)
    except ValueError:
        return None

    matched_action: IPRuleAction | None = None
    matched_prefix = -1

    for rule in rules:
        try:
            cidr = str(rule["cidr"])
            action = rule["action"]
            network = ip_network(cidr, strict=False)
        except (ValueError, KeyError, TypeError):
            continue
        if ip in network:
            try:
                if not isinstance(action, IPRuleAction):
                    action = IPRuleAction(str(action).lower())
            except Exception:
                continue
            if network.prefixlen > matched_prefix:
                matched_action = action
                matched_prefix = network.prefixlen

    return matched_action
