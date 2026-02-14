from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any


@dataclass(slots=True)
class S3CompatibleStorage:
    bucket: str
    endpoint_url: str | None = None
    region_name: str | None = None
    access_key: str | None = None
    secret_key: str | None = None
    use_ssl: bool = True

    def put_path(self, *, key: str, local_path: str) -> str | None:
        if not local_path or not os.path.exists(local_path):
            return None
        client = _create_boto3_client(
            endpoint_url=self.endpoint_url,
            region_name=self.region_name,
            access_key=self.access_key,
            secret_key=self.secret_key,
            use_ssl=self.use_ssl,
        )
        if client is None:
            return f"s3://{self.bucket}/{key}"
        client.upload_file(local_path, self.bucket, key)
        return f"s3://{self.bucket}/{key}"


def _create_boto3_client(
    *,
    endpoint_url: str | None,
    region_name: str | None,
    access_key: str | None,
    secret_key: str | None,
    use_ssl: bool,
) -> Any | None:
    try:
        import boto3
    except Exception:
        return None
    session = boto3.session.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region_name,
    )
    return session.client(
        "s3",
        endpoint_url=endpoint_url,
        use_ssl=use_ssl,
    )
