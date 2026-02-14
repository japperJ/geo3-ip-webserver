from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "geo3-ip-webserver"
    jwt_secret: str = "dev-secret"
    jwt_algorithm: str = "HS256"
    jwt_exp_minutes: int = 60


settings = Settings()
