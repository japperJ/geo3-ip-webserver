import uuid

from app.artifacts import worker
from app.artifacts.storage import S3CompatibleStorage


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


def test_capture_artifact_returns_placeholder_path():
    storage = S3CompatibleStorage(bucket="artifacts")

    path = worker.capture_artifact(
        site_id=uuid.uuid4(),
        capture_callable=None,
        storage=storage,
    )

    assert path == "s3://artifacts/placeholder"
