#!/usr/bin/env python3
"""
🚀 Master seed script — seeds the entire Neo4j database.
Run once: python seed_database.py
"""

import sys
import subprocess
import os

# ── Windows compatibility ─────────────────────────────────────────────────────
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Pass PYTHONUTF8=1 to all child processes so their emoji prints work too.
_child_env = {**os.environ, "PYTHONUTF8": "1"}

scripts = [
    ("setup_graph.py", "Setup: Creating cities"),
    ("update_memory_schema.py", "Schema: Persistent Memory Setup"),
    ("populate_travel_graph.py", "Populate: Adding attractions"),
    ("booking_sync.py", "Booking: Adding hotels"),
    ("flights.py", "Flights: Adding flights"),
]

print("=" * 60)
print("🌍 HORYZONTY - SEEDING DATABASE")
print("=" * 60)

for script, description in scripts:
    script_path = os.path.join(BASE_DIR, script)
    print(f"\n🔄 [{description}]")
    print(f"  Running: {script}")

    result = subprocess.run([sys.executable, script_path], cwd=BASE_DIR, env=_child_env)

    if result.returncode != 0:
        print(f"❌ ERROR: {script} failed!")
        sys.exit(1)
    print(f"✅ {script} completed successfully")

print("\n" + "=" * 60)
print("✅ DATABASE SEEDED SUCCESSFULLY!")
print("=" * 60)
print("\nYou can now start the backend:")
print("  python api.py")
print("\nAnd open in browser:")
print("  http://127.0.0.1:5500/index.html")
print("=" * 60)
