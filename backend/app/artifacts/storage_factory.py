from app.artifacts.storage import S3CompatibleStorage
from app.settings import settings


def build_storage() -> S3CompatibleStorage:
    return S3CompatibleStorage(
        bucket=settings.artifact_bucket,
        endpoint_url=settings.artifact_endpoint_url,
        region_name=settings.artifact_region,
        access_key=settings.artifact_access_key,
        secret_key=settings.artifact_secret_key,
        use_ssl=settings.artifact_use_ssl,
    )
