# SDN QNX Generator

## Overview

This project provides a **CLI-based SDN configuration generator** that converts an abstract, vendor-independent network configuration (based on YANG JSON models) into **QNX-specific network configuration files**.

This is part of the SDV (Software Defined Vehicle) platform to enable:
- Automated network configuration
- OS-independent networking abstraction
- CI/CD-based configuration generation

---

## ObjectiveConvert:

Convert: 
```
Abstract Network Config (YANG JSON)
            ↓
QNX Network Configuration
```
---

## Features

- Parse JSON-based network configuration
- Generate:
  - VLAN configuration
  - IP configuration
  - Routing table
- CLI-based (non-interactive)
- CI compatible
- Extensible for:
  - TSN (IEEE 802.1Qav)
  - Time synchronization
  - DNS configuration

---

## Project Structure

```
sdn-config-generator/
│
├── src/
│   ├── core/
│   ├── plugins/
│   ├── sdk/
│   └── main.py
├── input/
├── output/
├── models/
├── pyproject.toml
├── README.md
├── requirements.txt
└── setup.cfg (optional)

```
---

## Setup

### Install dependencies
```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip -y
```

### Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```
### Install Python packages
```bash
pip install -r requirements.txt
```

## Usage
Run the generator:
```bash
python src/main.py --input input/config.json --output output/
```
Input Format (Example JSON)
```bash
{
  "interfaces": [
    {
      "name": "eth0",
      "vlan_id": 100,
      "ip": "192.168.1.10",
      "netmask": "255.255.255.0"
    }
  ],
  "routes": [
    {
      "destination": "0.0.0.0/0",
      "gateway": "192.168.1.1"
    }
  ]
}

```

Output Files
Example generated files:
```
output/
├── interfaces.conf
├── routes.conf
```
Example content:
interfaces.conf
```bash
ifconfig eth0 192.168.1.10 netmask 255.255.255.0
vlan create 100 eth0
```
routes.conf
```bash
route add 0.0.0.0/0 192.168.1.1
```
---

## Testing
Run basic test:
```bash
python src/main.py --input input/config.json --output output/
```
Verify output:
```bash
ls output/
```
## CI/CD Integration
This tool is designed to run in CI pipelines:
```bash
python src/main.py --input config.json --output build/qnx_config/
```

## Limitations
- Partial YANG model support (initial phase)
- Time synchronization not fully implemented
- No runtime configuration (build-time only)


## Future Enhancements
- Full YANG validation (libyang)
- TSN (IEEE 802.1Qav) configuration
- DNS and time sync configuration
- Integration with SDN controller pipeline
- Support for Android / Linux generators


## Team
- SDN1 Team – SDV Platform Development

## Status
Work in Progress – PoC Phase


---

