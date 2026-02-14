from app.access.ip_rules import evaluate_ip_rules
from app.db.models.ip_rule import IPRuleAction


def test_evaluate_ip_rules_allows_matching_cidr():
    rules = [
        {"cidr": "10.0.0.0/8", "action": IPRuleAction.ALLOW},
    ]

    assert evaluate_ip_rules("10.1.2.3", rules) == IPRuleAction.ALLOW


def test_evaluate_ip_rules_denies_with_precedence():
    rules = [
        {"cidr": "10.0.0.0/8", "action": IPRuleAction.ALLOW},
        {"cidr": "10.0.1.0/24", "action": IPRuleAction.DENY},
    ]

    assert evaluate_ip_rules("10.0.1.5", rules) == IPRuleAction.DENY


def test_evaluate_ip_rules_prefers_most_specific_match():
    rules = [
        {"cidr": "10.0.0.0/8", "action": IPRuleAction.DENY},
        {"cidr": "10.1.0.0/16", "action": IPRuleAction.ALLOW},
    ]

    assert evaluate_ip_rules("10.1.2.3", rules) == IPRuleAction.ALLOW


def test_evaluate_ip_rules_allows_more_specific_override_deny():
    rules = [
        {"cidr": "10.0.1.0/24", "action": IPRuleAction.DENY},
        {"cidr": "10.0.1.5/32", "action": IPRuleAction.ALLOW},
    ]

    assert evaluate_ip_rules("10.0.1.5", rules) == IPRuleAction.ALLOW


def test_evaluate_ip_rules_returns_none_when_no_match():
    rules = [
        {"cidr": "10.0.0.0/8", "action": IPRuleAction.ALLOW},
    ]

    assert evaluate_ip_rules("192.168.0.1", rules) is None
