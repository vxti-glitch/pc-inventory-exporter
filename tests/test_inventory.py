import csv
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import inventory


SAMPLE_DATA = {
    "system": {"Hostname": "WS-01", "OS": "Windows 11"},
    "memory": {"Total RAM": "16.0 GB", "RAM Usage": "40%"},
    "disks": [
        {
            "Device": "C:",
            "Mount": "C:\\",
            "Filesystem": "NTFS",
            "Total": "256.0 GB",
            "Used": "100.0 GB",
            "Free": "156.0 GB",
            "Used %": "39%",
        }
    ],
    "network": [
        {
            "Adapter": "Ethernet",
            "Family": "AF_INET",
            "Address": "192.0.2.10",
            "Netmask": "255.255.255.0",
            "Status": "Up",
        }
    ],
    "programs": ["Example App"],
}


class InventoryReportTests(unittest.TestCase):
    def test_build_txt_report_contains_core_sections(self):
        report = inventory.build_txt_report(SAMPLE_DATA)
        self.assertIn("PC INVENTORY REPORT", report)
        self.assertIn("SYSTEM INFORMATION", report)
        self.assertIn("INSTALLED PROGRAMS", report)

    def test_write_csv_and_json_reports(self):
        with TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "inventory.csv"
            json_path = Path(tmp) / "inventory.json"

            inventory.write_csv_report(SAMPLE_DATA, csv_path)
            inventory.write_json_report(SAMPLE_DATA, json_path)

            with csv_path.open(newline="", encoding="utf-8") as f:
                rows = list(csv.reader(f))
            self.assertIn(["=== SYSTEM ==="], rows)

            payload = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["system"]["Hostname"], "WS-01")


if __name__ == "__main__":
    unittest.main()
