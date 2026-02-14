from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "geo3-ip-webserver"


settings = Settings()
