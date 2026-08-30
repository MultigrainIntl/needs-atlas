#!/usr/bin/env python3
"""
pull_grants.py — Refresh config/grants.json from the Grants.gov Search2 API.

Surfaces OPEN federal funding opportunities relevant to a community health center /
food-security nonprofit, tags each with need "themes", and writes them for the web
app to rank against each county's indicators.

Stdlib only. Runs on CI (GitHub Actions reaches api.grants.gov; the Cowork container
is firewalled from it). If the pull fails, the committed config/grants.json is left
in place so the app still has data.

    python scripts/pull_grants.py
"""
import json, sys, urllib.request, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "config" / "grants.json"
API = "https://api.grants.gov/v1/api/search2"

KEYWORDS = [
    "community health center", "health center program", "food insecurity", "nutrition",
    "food access", "health equity", "health disparities", "behavioral health",
    "mental health services", "substance use disorder", "maternal health", "healthy start",
    "chronic disease prevention", "diabetes prevention", "rural health", "oral health",
    "access to care", "community health worker", "social determinants of health",
    "older adults services", "family planning",
]

BAD_AGENCY = ("national institutes", "national institute of", "defense health", "u.s. mission",
              "animal and plant", "national science", "department of defense", "army", "navy",
              "air force", "national endowment", "institute of education", "fogarty",
              "bureau of land management")
BAD_TITLE = ("clinical trial", "(r0", "(r2", "(r3", "(k0", "(k2", "(u0", "(p0", "(dp", "(t3",
             "sbir", "sttr", "fellowship", "dissertation", "research center", "global",
             "international", "overseas", "abroad", "foreign", "pepfar", "malaria", "fungal",
             "zoonotic", "surveillance", "water infrastructure", "water system", "conservation corps")

THEME_RULES = [
    ("food", ("food", "nutrition", "hunger", "snap", "wic", "produce", "meal", "grocery", "farmers market", "food bank", "gusnip")),
    ("chronic-disease", ("chronic", "diabet", "obesity", "hypertens", "heart", "cardiov", "cancer", "asthma", "copd", "stroke", "tobacco", "reach")),
    ("behavioral-health", ("behavioral", "mental health", "substance", "opioid", "suicide", "addiction", "psych", "recovery", "moud")),
    ("access", ("uninsured", "access to care", "health center", "primary care", "safety net", "coverage", "telehealth", "workforce", "community health worker", "ryan white", "look-alike", "fqhc")),
    ("maternal-child", ("maternal", "infant", "child", "pediatric", "healthy start", "prenatal", "family planning", "title x", "home visit", "head start", "adolescent", "youth")),
    ("aging", ("older adult", "aging", "senior", "elderly", "geriatric", "alzheimer")),
    ("housing", ("housing", "homeless", "shelter", "healthy homes")),
    ("oral", ("oral health", "dental")),
    ("equity", ("equity", "disparit", "underserved", "minority", "social determinant")),
    ("rural", ("rural",)),
]
CORE = ("health center", "primary care", "community health", "safety net", "rural health",
        "underserved", "health equity", "nutrition", "food", "behavioral", "mental health",
        "substance", "maternal", "home visit", "aging", "older adult", "oral health", "dental",
        "community health worker", "social determinant", "family planning")


def themes(title):
    s = title.lower()
    out = [k for k, kws in THEME_RULES if any(w in s for w in kws)]
    return out or ["general"]


def iso(d):
    try:
        return datetime.datetime.strptime(d, "%m/%d/%Y").date().isoformat()
    except (ValueError, TypeError):
        return None


def search(keyword):
    body = json.dumps({"rows": 25, "oppStatuses": "posted", "keyword": keyword}).encode()
    req = urllib.request.Request(API, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        j = json.load(r)
    return (j.get("data") or {}).get("oppHits") or []


def main():
    merged = {}
    for kw in KEYWORDS:
        try:
            for o in search(kw):
                merged.setdefault(o["number"], o)
        except Exception as e:
            print(f"  WARN: query '{kw}' failed: {e}", file=sys.stderr)

    if not merged:
        print("No Grants.gov results — leaving config/grants.json untouched.", file=sys.stderr)
        sys.exit(1)

    today = datetime.date.today()
    cutoff = today + datetime.timedelta(days=5)
    kept = []
    for o in merged.values():
        ag = (o.get("agency") or "").lower()
        ti = (o.get("title") or "")
        til = ti.lower()
        if any(b in ag for b in BAD_AGENCY) or any(b in til for b in BAD_TITLE):
            continue
        close = iso(o.get("closeDate"))
        if not close or datetime.date.fromisoformat(close) < cutoff:
            continue
        th = themes(ti)
        if th[0] == "general" and not any(w in til for w in CORE):
            continue
        kept.append({
            "number": o.get("number"), "title": ti, "agency": o.get("agency"),
            "close": close, "cfda": (o.get("cfdaList") or [""])[0],
            "themes": th, "url": "https://www.grants.gov/search-results-detail/" + str(o.get("id")),
        })
    kept.sort(key=lambda x: x["close"])
    kept = kept[:32]

    out = {
        "source": "Grants.gov Search2 API — open federal funding opportunities",
        "source_url": "https://www.grants.gov",
        "pulled": today.isoformat(),
        "note": ("Open federal opportunities surfaced by keyword and matched to each county's need "
                 "indicators. Always verify eligibility and full details on grants.gov before applying."),
        "opportunities": kept,
    }
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"Wrote {OUT} — {len(kept)} open opportunities (from {len(merged)} raw hits).")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Grants.gov pull failed ({e}); keeping existing config/grants.json.", file=sys.stderr)
        sys.exit(1)
