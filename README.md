# PC Inventory Exporter

[github.com/vxti-glitch](https://github.com/vxti-glitch)

Gathers a full machine inventory - OS, CPU, RAM, disks, network adapters, and installed programs - and exports it as formatted `.txt`, `.csv`, and optional `.json` reports for asset management use.

---

## Example output (`.txt`)

```
============================================================
  PC INVENTORY REPORT
  Generated: 2026-08-03 20:15:00
============================================================

SYSTEM INFORMATION
------------------------------------------------------------
  Hostname               DESKTOP-IV1234
  Logged-in User         MIke
  OS                     Windows 11
  OS Version             10.0.22631
  Architecture           AMD64
  Processor              Intel64 Family 6 Model 154
  Last Boot              2026-08-03 09:01:12
  Uptime                 11h 13m 48s

MEMORY
------------------------------------------------------------
  Total RAM              31.9 GB
  Available RAM          17.7 GB
  RAM Usage              44.5%

DISK DRIVES
------------------------------------------------------------
  C:\  (NTFS)  ->  C:\
    Total: 476.8 GB  |  Used: 210.3 GB (44.1%)  |  Free: 266.5 GB

NETWORK ADAPTERS
------------------------------------------------------------
  [Up] Wi-Fi
    AF_INET: 192.168.1.105  (mask: 255.255.255.0)

INSTALLED PROGRAMS (142 found)
------------------------------------------------------------
  - 7-Zip 23.01
  - Google Chrome
  - Microsoft Visual C++ 2022 Redistributable
  - Python 3.12.0
  - ...
```

---

## Usage

```bash
# Install dependency
pip install -r requirements.txt

# Generate both .txt and .csv reports (default)
python inventory.py

# Text report only
python inventory.py --txt

# CSV only
python inventory.py --csv

# JSON snapshot, written to a specific folder
python inventory.py --json --output reports
```

Reports are saved in the same directory as the script by default, or in `--output DIR`, with a timestamped filename:
- `inventory_20260803_201500.txt`
- `inventory_20260803_201500.csv`
- `inventory_20260803_201500.json`

Run tests:

```bash
python -m unittest discover -s tests -v
```

---

## What it collects

| Section | Fields |
|---|---|
| System | Hostname, current user, OS, version, architecture, processor, last boot, uptime |
| Memory | Total RAM, available RAM, usage % |
| Disks | Device, mount point, filesystem, total / used / free / usage % |
| Network | Adapter name, IPv4/IPv6 address, netmask, up/down status |
| Installed Programs | Full list from Windows registry (Windows only) |

---

## Help Desk relevance

Asset inventory and machine documentation are standard Help Desk tasks. When a user needs remote support, being able to quickly generate and share a machine snapshot accelerates diagnosis. This tool automates the collection process that would otherwise require opening 5–6 different menus manually.

The CSV output is formatted to be imported directly into a spreadsheet-based asset register - the same workflow used in small IT teams that have not yet deployed a formal MDM or asset management system.

**Skills:** Python · psutil · Windows registry (winreg) · Asset documentation · CSV reporting

---

*Part of the [vxti-glitch IT Support Portfolio](https://github.com/vxti-glitch)*
