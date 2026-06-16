import json

def parse_json(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)

    # Basic validation (extend using YANG)
    if "interfaces" not in data:
        raise ValueError("Missing 'interfaces' section")

    return data