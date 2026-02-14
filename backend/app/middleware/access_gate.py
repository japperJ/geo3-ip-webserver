from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Awaitable
import inspect
from pathlib import Path
from typing import Iterable, Mapping

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware

from app.access.decision import decide_access
from app.access.ip_rules import evaluate_ip_rules
from app.db.models.audit import AccessDecision
from app.db.models.site import SiteFilterMode

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))


@dataclass
class SiteAccessConfig:
    filter_mode: SiteFilterMode
    ip_rules: list[Mapping[str, object]] = field(default_factory=list)
    geo_allowed: bool | None = None


class SiteConfigRegistry:
    def __init__(self) -> None:
        self._configs: dict[str, SiteAccessConfig] = {}

    def get(self, hostname: str) -> SiteAccessConfig | None:
        return self._configs.get(hostname)

    def set(self, hostname: str, config: SiteAccessConfig) -> None:
        self._configs[hostname.lower()] = config

    def clear(self) -> None:
        self._configs.clear()


def _get_site_registry(app: FastAPI) -> SiteConfigRegistry:
    registry = getattr(app.state, "site_access_registry", None)
    if registry is None:
        registry = SiteConfigRegistry()
        app.state.site_access_registry = registry
    return registry


def register_site_config(app: FastAPI, hostname: str, config: SiteAccessConfig) -> None:
    _get_site_registry(app).set(hostname, config)


def clear_site_configs(app: FastAPI) -> None:
    _get_site_registry(app).clear()


def _normalize_hostname(host: str | None) -> str | None:
    if not host:
        return None
    return host.split(":", 1)[0].lower()


class AccessGateMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, geoip_service: object | None = None) -> None:
        super().__init__(app)
        self._geoip_service = geoip_service

    async def dispatch(self, request: Request, call_next):
        host = _normalize_hostname(request.headers.get("host"))
        if not host:
            return await call_next(request)

        config = _get_site_registry(request.app).get(host)
        if config is None:
            return await call_next(request)

        ip_action = _evaluate_ip_action(request, config.ip_rules)
        geoip_service = self._geoip_service
        if geoip_service is None:
            geoip_service = getattr(request.app.state, "geoip_service", None)
        geo_allowed = await _evaluate_geo_allowed(
            request,
            config.geo_allowed,
            geoip_service,
        )
        decision = decide_access(
            filter_mode=config.filter_mode,
            ip_action=ip_action,
            geo_allowed=geo_allowed,
        )
        if decision == AccessDecision.BLOCKED:
            return templates.TemplateResponse(
                request,
                "block.html",
                {"hostname": host},
                status_code=403,
            )

        return await call_next(request)


def _evaluate_ip_action(request: Request, rules: Iterable[Mapping[str, object]]) -> object | None:
    if not rules:
        return None
    client_ip = request.client.host if request.client else ""
    if not client_ip:
        return None
    try:
        return evaluate_ip_rules(client_ip, rules)
    except Exception:
        return None


async def _evaluate_geo_allowed(
    request: Request,
    geo_allowed: bool | None,
    geoip_service: object | None,
) -> bool | None:
    if geo_allowed is not None:
        return geo_allowed
    if geoip_service is None:
        return None
    client_ip = request.client.host if request.client else ""
    if not client_ip:
        return None
    lookup = getattr(geoip_service, "lookup", None)
    if lookup is None:
        return None
    try:
        result = lookup(client_ip)
        if isinstance(result, Awaitable) or inspect.isawaitable(result):
            result = await result
    except Exception:
        return None
    if result is None:
        return None
    if isinstance(result, bool):
        return result
    if isinstance(result, Mapping):
        return bool(result)
    return True
