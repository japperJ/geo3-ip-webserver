from fastapi import FastAPI

from app.routers.audit import router as audit_router
from app.routers.auth import router as auth_router
from app.routers.geofences import router as geofences_router
from app.routers.health import router as health_router
from app.routers.ip_rules import router as ip_rules_router
from app.routers.site_users import router as site_users_router
from app.routers.sites import router as sites_router
from app.middleware.access_gate import AccessGateMiddleware

app = FastAPI()
app.add_middleware(AccessGateMiddleware)
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(audit_router)
app.include_router(sites_router)
app.include_router(geofences_router)
app.include_router(ip_rules_router)
app.include_router(site_users_router)
