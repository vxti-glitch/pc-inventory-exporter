"""
pc-inventory-exporter
----------------------
Gathers machine information — OS version, hostname, logged-in user,
CPU, RAM, disks, network adapters, and installed programs — and exports
a formatted report to both a .txt file and a .csv file for asset-management
use cases.

Usage:
    python inventory.py             # generates both .txt and .csv reports
    python inventory.py --txt       # text report only
    python inventory.py --csv       # CSV only

Requirements:
    pip install psutil
"""

import argparse
import csv
import datetime
import getpass
import io
import json
import os
import platform
import sys
from pathlib import Path

# Force UTF-8 output so any unicode chars render on all Windows consoles
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

try:
    import psutil
except ImportError:
    print("[ERROR] psutil is not installed. Run:  pip install psutil")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fmt_bytes(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def separator(char="=", width=60):
    return char * width


def now_str():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------------------
# Data collectors
# ---------------------------------------------------------------------------

def get_system():
    boot = datetime.datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.datetime.now() - boot
    h, r = divmod(int(uptime.total_seconds()), 3600)
    m, s = divmod(r, 60)
    return {
        "Hostname":     platform.node(),
        "Logged-in User": getpass.getuser(),
        "OS":           f"{platform.system()} {platform.release()}",
        "OS Version":   platform.version(),
        "Architecture": platform.machine(),
        "Processor":    platform.processor() or "N/A",
        "Last Boot":    boot.strftime("%Y-%m-%d %H:%M:%S"),
        "Uptime":       f"{h}h {m}m {s}s",
    }


def get_memory():
    vm = psutil.virtual_memory()
    return {
        "Total RAM":      fmt_bytes(vm.total),
        "Available RAM":  fmt_bytes(vm.available),
        "RAM Usage":      f"{vm.percent}%",
    }


def get_disks():
    result = []
    for p in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(p.mountpoint)
        except PermissionError:
            continue
        result.append({
            "Device":     p.device,
            "Mount":      p.mountpoint,
            "Filesystem": p.fstype,
            "Total":      fmt_bytes(usage.total),
            "Used":       fmt_bytes(usage.used),
            "Free":       fmt_bytes(usage.free),
            "Used %":     f"{usage.percent}%",
        })
    return result


def get_network():
    adapters = []
    addrs = psutil.net_if_addrs()
    stats = psutil.net_if_stats()
    for name, addr_list in addrs.items():
        for addr in addr_list:
            if addr.family.name in ("AF_INET", "AF_INET6"):
                is_up = stats[name].isup if name in stats else False
                adapters.append({
                    "Adapter":  name,
                    "Family":   addr.family.name,
                    "Address":  addr.address,
                    "Netmask":  addr.netmask or "N/A",
                    "Status":   "Up" if is_up else "Down",
                })
    return adapters


def get_installed_programs():
    """
    Returns a list of installed program names on Windows via the registry.
    Falls back to an empty list on non-Windows systems.
    """
    if platform.system() != "Windows":
        return []

    programs = set()
    reg_paths = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
    ]

    try:
        import winreg
        for path in reg_paths:
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
                for i in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        sub_key_name = winreg.EnumKey(key, i)
                        sub_key = winreg.OpenKey(key, sub_key_name)
                        try:
                            name, _ = winreg.QueryValueEx(sub_key, "DisplayName")
                            if name:
                                programs.add(name.strip())
                        except FileNotFoundError:
                            pass
                        winreg.CloseKey(sub_key)
                    except Exception:
                        pass
                winreg.CloseKey(key)
            except Exception:
                pass
    except ImportError:
        pass

    return sorted(programs)


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------

def collect_all():
    return {
        "system":   get_system(),
        "memory":   get_memory(),
        "disks":    get_disks(),
        "network":  get_network(),
        "programs": get_installed_programs(),
    }


def build_txt_report(data):
    lines = []

    def add(text=""):
        lines.append(text)

    ts = now_str()
    add(separator())
    add("  PC INVENTORY REPORT")
    add(f"  Generated: {ts}")
    add(separator())

    # System
    add()
    add("SYSTEM INFORMATION")
    add(separator("-"))
    for k, v in data["system"].items():
        add(f"  {k:<22} {v}")

    # Memory
    add()
    add("MEMORY")
    add(separator("-"))
    for k, v in data["memory"].items():
        add(f"  {k:<22} {v}")

    # Disks
    add()
    add("DISK DRIVES")
    add(separator("-"))
    for d in data["disks"]:
        add(f"  {d['Device']}  ({d['Filesystem']})  ->  {d['Mount']}")
        add(f"    Total: {d['Total']}  |  Used: {d['Used']} ({d['Used %']})  |  Free: {d['Free']}")

    # Network
    add()
    add("NETWORK ADAPTERS")
    add(separator("-"))
    for a in data["network"]:
        add(f"  [{a['Status']}] {a['Adapter']}")
        add(f"    {a['Family']}: {a['Address']}  (mask: {a['Netmask']})")

    # Programs
    programs = data["programs"]
    if programs:
        add()
        add(f"INSTALLED PROGRAMS ({len(programs)} found)")
        add(separator("-"))
        for p in programs:
            add(f"  • {p}")
    else:
        add()
        add("INSTALLED PROGRAMS")
        add(separator("-"))
        add("  (Not available on this OS — Windows registry required)")

    add()
    add(separator())
    add("  END OF REPORT")
    add(separator())
    return "\n".join(lines)


def write_csv_report(data, filepath):
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # System section
        writer.writerow(["=== SYSTEM ==="])
        writer.writerow(["Field", "Value"])
        for k, v in data["system"].items():
            writer.writerow([k, v])
        for k, v in data["memory"].items():
            writer.writerow([k, v])
        writer.writerow([])

        # Disks
        writer.writerow(["=== DISKS ==="])
        writer.writerow(["Device", "Mount", "Filesystem", "Total", "Used", "Free", "Used %"])
        for d in data["disks"]:
            writer.writerow([d["Device"], d["Mount"], d["Filesystem"],
                             d["Total"], d["Used"], d["Free"], d["Used %"]])
        writer.writerow([])

        # Network
        writer.writerow(["=== NETWORK ==="])
        writer.writerow(["Adapter", "Family", "Address", "Netmask", "Status"])
        for a in data["network"]:
            writer.writerow([a["Adapter"], a["Family"], a["Address"],
                             a["Netmask"], a["Status"]])
        writer.writerow([])

        # Programs
        writer.writerow(["=== INSTALLED PROGRAMS ==="])
        writer.writerow(["Program Name"])
        for p in data["programs"]:
            writer.writerow([p])


def write_json_report(data, filepath):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="PC Inventory Exporter — generates system info reports for asset management."
    )
    parser.add_argument("--txt", action="store_true", help="Generate .txt report only")
    parser.add_argument("--csv", action="store_true", help="Generate .csv report only")
    parser.add_argument("--json", action="store_true", help="Generate .json report")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parent,
        help="Directory for generated reports. Default: script directory.",
    )
    args = parser.parse_args()

    requested_format = args.txt or args.csv or args.json
    do_txt = args.txt or not requested_format
    do_csv = args.csv or not requested_format
    do_json = args.json

    print("[*] Collecting system inventory...")
    data = collect_all()
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = args.output
    out_dir.mkdir(parents=True, exist_ok=True)

    if do_txt:
        report = build_txt_report(data)
        txt_path = out_dir / f"inventory_{ts}.txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(report)
        print(f"\n[OK] Text report saved: {txt_path}")

    if do_csv:
        csv_path = out_dir / f"inventory_{ts}.csv"
        write_csv_report(data, csv_path)
        print(f"[OK] CSV  report saved: {csv_path}")

    if do_json:
        json_path = out_dir / f"inventory_{ts}.json"
        write_json_report(data, json_path)
        print(f"[OK] JSON report saved: {json_path}")


if __name__ == "__main__":
    main()
