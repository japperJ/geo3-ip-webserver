from __future__ import annotations

import inspect
import uuid
from collections.abc import Awaitable, Callable

from app.artifacts.storage import S3CompatibleStorage
from app.db.models.artifact import Artifact


def record_artifact_metadata(
    *,
    site_id: uuid.UUID,
    path: str,
    db_session: object | None,
) -> Artifact | None:
    if db_session is None:
        return None
    add = getattr(db_session, "add", None)
    commit = getattr(db_session, "commit", None)
    if add is None or commit is None:
        return None
    record = Artifact(site_id=site_id, path=path)
    add(record)
    commit()
    return record


async def capture_artifact(
    *,
    site_id: str | uuid.UUID,
    capture_callable: Callable[[], str] | Callable[[], Awaitable[str]] | None,
    storage: S3CompatibleStorage,
) -> str:
    local_path = "placeholder"
    if capture_callable is not None:
        result = capture_callable()
        if inspect.isawaitable(result):
            result = await result
        local_path = result
    key = "placeholder" if capture_callable is None else f"{site_id}/artifact"
    return storage.put_path(key=key, local_path=local_path)
