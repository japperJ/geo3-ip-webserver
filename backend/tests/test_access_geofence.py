from app.access.geofence import within_geofence


def test_within_geofence_polygon_match():
    polygon = [
        (-1.0, -1.0),
        (1.0, -1.0),
        (1.0, 1.0),
        (-1.0, 1.0),
    ]

    assert within_geofence(point=(0.0, 0.0), polygon=polygon, center=None, radius_meters=None)


def test_within_geofence_polygon_miss():
    polygon = [
        (-1.0, -1.0),
        (1.0, -1.0),
        (1.0, 1.0),
        (-1.0, 1.0),
    ]

    assert not within_geofence(
        point=(2.0, 0.0),
        polygon=polygon,
        center=None,
        radius_meters=None,
    )


def test_within_geofence_polygon_edge_treated_inside():
    polygon = [
        (-1.0, -1.0),
        (1.0, -1.0),
        (1.0, 1.0),
        (-1.0, 1.0),
        (-1.0, -1.0),
    ]

    assert within_geofence(
        point=(1.0, 0.0),
        polygon=polygon,
        center=None,
        radius_meters=None,
    )


def test_within_geofence_radius_match():
    assert within_geofence(
        point=(0.0, 0.009),
        polygon=None,
        center=(0.0, 0.0),
        radius_meters=1200,
    )


def test_within_geofence_radius_miss():
    assert not within_geofence(
        point=(0.0, 0.02),
        polygon=None,
        center=(0.0, 0.0),
        radius_meters=1200,
    )
