from __future__ import annotations

from app.db.models.audit import AccessDecision
from app.db.models.site import SiteFilterMode


def decide_access(
    *,
    filter_mode: SiteFilterMode,
    ip_action: object | None,
    geo_allowed: bool | None,
) -> AccessDecision:
    if filter_mode == SiteFilterMode.DISABLED:
        return AccessDecision.ALLOWED
    if filter_mode == SiteFilterMode.IP:
        return _decision_from_ip(ip_action)
    if filter_mode == SiteFilterMode.GEO:
        return AccessDecision.ALLOWED if geo_allowed else AccessDecision.BLOCKED
    return _decision_from_ip_and_geo(ip_action, geo_allowed)


def _decision_from_ip(ip_action: object | None) -> AccessDecision:
    if str(ip_action) == "allow":
        return AccessDecision.ALLOWED
    return AccessDecision.BLOCKED


def _decision_from_ip_and_geo(
    ip_action: object | None,
    geo_allowed: bool | None,
) -> AccessDecision:
    if str(ip_action) != "allow":
        return AccessDecision.BLOCKED
    if geo_allowed:
        return AccessDecision.ALLOWED
    return AccessDecision.BLOCKED
