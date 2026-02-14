from fastapi import FastAPI

from app.routers.auth import router as auth_router
from app.routers.health import router as health_router
from app.middleware.access_gate import AccessGateMiddleware

app = FastAPI()
app.add_middleware(AccessGateMiddleware)
app.include_router(health_router)
app.include_router(auth_router)
