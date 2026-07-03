"""Legacy compatibility regression test.

This file preserves the original test module path while validating the
current parser API contract.
"""

from src.core.parser import parse_json


def test_parser_valid_linux_fixture() -> None:
    """Parser should successfully process the canonical Linux fixture."""
    parsed = parse_json("input/configuration_end-station_Linux.json")
    assert "interfaces" in parsed.model
    assert "routes" in parsed.model