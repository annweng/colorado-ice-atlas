from app.services.object_store import LocalObjectStore


def test_round_trip(tmp_path):
    store = LocalObjectStore(tmp_path)
    store.put_bytes("ice/meta.json", b'{"ok":true}', "application/json")
    assert store.exists("ice/meta.json")
    assert store.get_bytes("ice/meta.json") == b'{"ok":true}'
