import asyncio
import uuid

from app.artifacts import worker


def test_record_artifact_metadata_stores_minimal_fields():
    class DummySession:
        def __init__(self) -> None:
            self.added = []
            self.committed = False

        def add(self, record) -> None:
            self.added.append(record)

        def commit(self) -> None:
            self.committed = True

    site_id = uuid.uuid4()
    db_session = DummySession()

    record = worker.record_artifact_metadata(
        site_id=site_id,
        path="s3://bucket/path.png",
        db_session=db_session,
    )

    assert record is not None
    assert record.site_id == site_id
    assert record.path == "s3://bucket/path.png"
    assert db_session.added == [record]
    assert db_session.committed is True


def test_record_artifact_metadata_returns_none_without_session():
    record = worker.record_artifact_metadata(
        site_id=uuid.uuid4(),
        path="s3://bucket/path.png",
        db_session=None,
    )

    assert record is None


def test_capture_artifact_invokes_capture_callable():
    class DummyStorage(worker.S3CompatibleStorage):
        def __init__(self) -> None:
            super().__init__(bucket="bucket")
            self.calls = []

        def put_path(self, *, key: str, local_path: str) -> str:
            self.calls.append((key, local_path))
            return f"s3://bucket/{key}"

    called = {"value": False}

    def capture() -> str:
        called["value"] = True
        return "local.png"

    storage = DummyStorage()
    site_id = uuid.uuid4()

    path = asyncio.run(
        worker.capture_artifact(
            site_id=site_id,
            capture_callable=capture,
            storage=storage,
        )
    )

    assert called["value"] is True
    assert storage.calls == [(f"{site_id}/artifact", "local.png")]
    assert path == f"s3://bucket/{site_id}/artifact"


def test_capture_artifact_returns_none_without_capture():
    class DummyStorage(worker.S3CompatibleStorage):
        def __init__(self) -> None:
            super().__init__(bucket="bucket")
            self.calls = []

        def put_path(self, *, key: str, local_path: str) -> str:
            self.calls.append((key, local_path))
            return f"s3://bucket/{key}"

    storage = DummyStorage()

    path = asyncio.run(
        worker.capture_artifact(
            site_id=uuid.uuid4(),
            capture_callable=None,
            storage=storage,
        )
    )

    assert storage.calls == []
    assert path is None


def test_capture_artifact_returns_remote_path_without_upload():
    class DummyStorage(worker.S3CompatibleStorage):
        def __init__(self) -> None:
            super().__init__(bucket="bucket")
            self.calls = []

        def put_path(self, *, key: str, local_path: str) -> str:
            self.calls.append((key, local_path))
            return f"s3://bucket/{key}"

    def capture() -> str:
        return "s3://bucket/remote"

    storage = DummyStorage()
    path = asyncio.run(
        worker.capture_artifact(
            site_id=uuid.uuid4(),
            capture_callable=capture,
            storage=storage,
        )
    )

    assert storage.calls == []
    assert path == "s3://bucket/remote"
