from app.db.models import Site


def test_site_filter_mode_default():
    column = Site.__table__.c.filter_mode
    assert column.default is not None
    assert column.default.arg == "allowlist"
