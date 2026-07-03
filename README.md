# SDN Config Generator

## Overview

- A CLI-based
- Network configuration generator
- that converts a vendor-agnostic network JSON (based on YANG data model)
- into OS-specific network configuration file(s).

## Current Status

Stable for development use with multi-OS generation and plugin-based extensibility.

- Supported OS:
  - QNX
  - Android
  - Linux

## What Is Achieved

The current implementation delivers the following checklist:

- Parallel execution engine for all plugins when `--os all` is used
- Dynamic plugin loading via entry points with fallback auto-loading
- Clean CLI orchestration from `parse` to `validate` to `map` to `generate`
- Multi-OS generator outputs: `QNX`, `Android`, `Linux`
- Plugin SDK architecture (`BasePlugin`, renderer, registry)
- Production-grade structure (`src/core`, `src/plugins`, `src/sdk`, packaging metadata)

## Project Structure

```text
sdn-config-generator/
├── src/
│   ├── core/
│   ├── plugins/
│   │   ├── qnx/
│   │   ├── android/
│   │   └── linux/
│   ├── sdk/
│   └── main.py
├── input/
├── output/
├── models/
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Architecture

### Flow

```text
Input JSON
   -> parser
   -> validator
   -> mapper
   -> plugin registry
   -> one or many OS plugins
   -> generated config files
```

### Key Components

- `src/main.py`: CLI entrypoint and orchestration
- `src/core/parser.py`: JSON parsing + validation trigger
- `src/core/validator.py`: schema/rule validation (interfaces, VLAN, TSN, routes)
- `src/core/mapper.py`: normalized internal mapping used by generators
- `src/sdk/base_plugin.py`: plugin abstraction
- `src/sdk/render_template.py`: shared Jinja2 rendering utility
- `src/sdk/registry.py`: plugin discovery + runtime registry
- `src/plugins/<os>/plugin.py`: OS-specific generation logic

## Setup

### 1. Create and activate virtual environment

On Debian/Ubuntu systems, you need to install the python3-venv
package using the following command.

Adjust the version.

```bash
sudo apt install python3.10-venv
```

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Optional: install package in editable mode

```bash
pip install -e .
```

## Usage

Run all plugins in parallel:

```bash
python -m src.main --input input/vehicle_config.json --output output --os all
```

Run a single plugin:

```bash
python -m src.main --input input/vehicle_config.json --output output --os qnx
python -m src.main --input input/vehicle_config.json --output output --os android
python -m src.main --input input/vehicle_config.json --output output --os linux
```

## Input Format

Example (top-level or under `network-config` is supported):

```json
{
  "network-config": {
    "interfaces": [
      {
        "name": "eth0",
        "vlan_id": 100,
        "ip": "192.168.1.10",
        "netmask": "255.255.255.0",
        "tsn": {
          "bandwidth": 75,
          "priority": 3
        }
      }
    ],
    "routes": [
      {
        "destination": "0.0.0.0/0",
        "gateway": "192.168.1.1"
      }
    ]
  }
}
```

## Output Layout

When `--os all` is used, output is grouped by plugin:

```text
output/
├── qnx/
│   ├── interfaces.conf
│   └── routes.conf
├── android/
│   └── interfaces.conf
└── linux/
    └── interfaces.conf
```

## Validation and Safety Checks

Current validation includes:

- Required interface fields (`name`, `ip`, `netmask`)
- IP/gateway validation
- VLAN range validation (`1-4094`)
- TSN validation (`bandwidth` and `priority` bounds)
- Route structure validation

## Plugin Discovery Behavior

Registry loading strategy:

1. Try loading plugins from entry points group `sdn.plugins`
2. If none are found or loading fails, fallback to built-in plugin imports

This ensures generation still works during local development runs.

## Example Success Output

```text
Available plugins: ['qnx', 'android', 'linux']
Validation passed
Completed plugin: android
Completed plugin: linux
Completed plugin: qnx
Config generation completed for: all
```
