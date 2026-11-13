from app.services.query import parse_coordinates


def test_parse_lat_lon():
    assert parse_coordinates("39.55, -106.07") == (39.55, -106.07)


def test_parse_lon_lat_colorado():
    lat, lon = parse_coordinates("-106.07, 39.55")
    assert lon < 0
    assert 30 < lat < 50


def test_reject_garbage():
    assert parse_coordinates("Granby") is None
