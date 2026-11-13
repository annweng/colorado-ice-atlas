from app.services.query import significant_tokens

from data.processing.aliases import apply_alias, load_aliases


def test_georgetown_alias_is_documented():
    aliases = load_aliases()
    assert "nhd-2884804" in aliases
    assert aliases["nhd-2884804"]["display_name"] == "Georgetown Lake"


def test_apply_alias_sets_searchable_name():
    row = apply_alias(
        {
            "id": "nhd-2884804",
            "name": "Unnamed waterbody",
            "display_name": "Unnamed waterbody",
            "official_name": None,
            "named": False,
        }
    )
    assert row["name"] == "Georgetown Lake"
    assert row["named"] is True
    assert "Georgetown Reservoir" in row["alternative_names"]


def test_georgetown_query_keeps_place_token():
    assert significant_tokens("Georgetown Lake") == ["georgetown"]
