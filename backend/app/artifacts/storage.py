from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class S3CompatibleStorage:
    bucket: str

    def put_path(self, *, key: str, local_path: str) -> str:
        _ = local_path
        return f"s3://{self.bucket}/{key}"
