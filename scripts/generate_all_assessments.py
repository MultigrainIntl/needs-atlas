#!/usr/bin/env python3
"""Generate a needs assessment for every county in config/real_counties.json."""
import json
from pathlib import Path
import generate_assessment as G

ROOT = Path(__file__).resolve().parents[1]
names = [c["county"] for c in json.loads((ROOT / "config" / "real_counties.json").read_text())["counties"]]
for n in names:
    stem = G.generate(n)
    print(f"  {n:10s} -> data/{stem}.docx")
print(f"Generated {len(names)} county assessments.")
