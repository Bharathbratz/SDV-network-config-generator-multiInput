from sdn_qnx_generator import parse_json
def test_parser_valid():
    data = parse_json("input/config.json")
    assert "interfaces" in data
    assert "routes" in data