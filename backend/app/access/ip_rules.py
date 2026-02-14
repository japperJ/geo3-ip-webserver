from __future__ import annotations

from ipaddress import ip_address, ip_network
from typing import Iterable, Mapping

from app.db.models.ip_rule import IPRuleAction


def evaluate_ip_rules(
    client_ip: str,
    rules: Iterable[Mapping[str, object]],
) -> IPRuleAction | None:
    ip = ip_address(client_ip)

    matched_action: IPRuleAction | None = None
    matched_prefix = -1
    matched_deny = False

    for rule in rules:
        cidr = str(rule["cidr"])
        action = rule["action"]
        network = ip_network(cidr, strict=False)
        if ip in network:
            if not isinstance(action, IPRuleAction):
                action = IPRuleAction(str(action))
            if action == IPRuleAction.DENY:
                if network.prefixlen > matched_prefix or not matched_deny:
                    matched_action = action
                    matched_prefix = network.prefixlen
                    matched_deny = True
            elif not matched_deny and network.prefixlen > matched_prefix:
                matched_action = action
                matched_prefix = network.prefixlen

    return matched_action
