#!/usr/bin/env python3
"""
pull_grants.py — Refresh open federal funding opportunities from the Grants.gov
Search2 API, for one of two profiles:

    python scripts/pull_grants.py county   # -> config/grants.json      (for the 7-county tool)
    python scripts/pull_grants.py fap      # -> config/fap_grants.json  (Food Aid Project's own radar)

Surfaces OPEN opportunities, tags each with need "themes", filters out research /
clinical-trial / global noise, and writes them for the web app to rank.

Stdlib only. Runs on CI (GitHub Actions reaches api.grants.gov; the Cowork container
is firewalled from it). On failure the committed JSON is left in place.
"""
import json, sys, urllib.request, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = "https://api.grants.gov/v1/api/search2"

# Agencies / titles that are never a fit for a community health / food-security nonprofit.
BAD_AGENCY = ("national institutes", "national institute of", "defense", "u.s. mission",
              "animal and plant", "national science", "army", "navy", "naval", "air force",
              "endowment", "fogarty", "bureau of land", "forest service", "geological",
              "fish and wildlife", "transportation", "federal highway", "environmental protection",
              "foreign agricultural", "small business", "oceanic", "maritime", "department of energy")
BAD_TITLE = ("clinical trial", "(r0", "(r2", "(r3", "(k0", "(k2", "(u0", "(p0", "(dp", "(t3",
             "sbir", "sttr", "fellowship", "dissertation", "research center", "global",
             "international", "overseas", "abroad", "foreign", "pepfar", "malaria", "fungal",
             "zoonotic", "surveillance", "wildlife", "watershed", "forest", "aquaculture",
             "livestock", "specialty crop block", "water infrastructure", "resilient operations",
             "highway")

# ---- County tool profile (FQHC service-area opportunities) ----
COUNTY_THEMES = [
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
COUNTY_CORE = ("health center", "primary care", "community health", "safety net", "rural health",
               "underserved", "health equity", "nutrition", "food", "behavioral", "mental health",
               "substance", "maternal", "home visit", "aging", "older adult", "oral health", "dental",
               "community health worker", "social determinant", "family planning")

# ---- Food Aid Project profile (the nonprofit's own funding radar) ----
FAP_THEMES = [
    ("food-security", ("food", "nutrition", "hunger", "farm to", "local food", "emergency food", "snap", "meal", "produce", "food bank", "food system", "gusnip", "healthy food", "senior nutrition", "child nutrition", "summer food", "farmers market", "wic")),
    ("health-equity", ("health equity", "health disparit", "community health", "social determinant", "minority health", "underserved", "health center")),
    ("capacity", ("capacity building", "technical assistance", "nonprofit capacity", "organizational capacity")),
    ("community-dev", ("community economic development", "community development financial", "community development block", "healthy food financing")),
    ("data-infrastructure", ("data modernization", "health information", "informatics", "public health infrastructure")),
]

PROFILES = {
    "county": {
        "out": "config/grants.json",
        "keywords": ["community health center", "health center program", "food insecurity", "nutrition",
                     "food access", "health equity", "health disparities", "behavioral health",
                     "mental health services", "substance use disorder", "maternal health", "healthy start",
                     "chronic disease prevention", "diabetes prevention", "rural health", "oral health",
                     "access to care", "community health worker", "social determinants of health",
                     "older adults services", "family planning"],
        "themes": COUNTY_THEMES, "core": COUNTY_CORE,
        "source": "Grants.gov Search2 API — open federal funding opportunities",
        "note": ("Open federal opportunities surfaced by keyword and matched to each county's need "
                 "indicators. Always verify eligibility and full details on grants.gov before applying."),
        "require_core": True,
    },
    "fap": {
        "out": "config/fap_grants.json",
        "keywords": ["food security", "food insecurity", "nutrition assistance", "health equity",
                     "community health", "capacity building", "nonprofit capacity",
                     "health information technology", "data modernization", "public health infrastructure",
                     "social determinants of health", "economic mobility", "community development",
                     "hunger", "farm to", "local food"],
        "themes": FAP_THEMES, "core": (),
        "source": "Grants.gov Search2 API — open federal opportunities for Food Aid Project, Inc.",
        "profile_desc": "Food Aid Project — food security, health equity, nonprofit capacity, data infrastructure",
        "note": ("Open federal opportunities matched to Food Aid Project's own mission. Federal NOFOs for an "
                 "organization this size are limited at any moment; foundation prospecting (IRS 990 data) is a "
                 "larger near-term source and can be added next. Always verify eligibility on grants.gov."),
        "require_core": False,
    },
}


def tag(title, rules):
    s = title.lower()
    return [k for k, kws in rules if any(w in s for w in kws)] or (["general"])


def iso(d):
    try:
        return datetime.datetime.strptime(d, "%m/%d/%Y").date().isoformat()
    except (ValueError, TypeError):
        return None


def search(keyword):
    body = json.dumps({"rows": 25, "oppStatuses": "posted", "keyword": keyword}).encode()
    req = urllib.request.Request(API, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return (json.load(r).get("data") or {}).get("oppHits") or []


def main(profile):
    cfg = PROFILES[profile]
    merged = {}
    for kw in cfg["keywords"]:
        try:
            for o in search(kw):
                merged.setdefault(o["number"], o)
        except Exception as e:
            print(f"  WARN: query '{kw}' failed: {e}", file=sys.stderr)
    if not merged:
        print(f"No Grants.gov results for '{profile}' — leaving existing file untouched.", file=sys.stderr)
        sys.exit(1)

    cutoff = datetime.date.today() + datetime.timedelta(days=5)
    kept = []
    for o in merged.values():
        ag = (o.get("agency") or "").lower()
        ti = (o.get("title") or "").replace("&amp;", "&")
        til = ti.lower()
        if any(b in ag for b in BAD_AGENCY) or any(b in til for b in BAD_TITLE):
            continue
        close = iso(o.get("closeDate"))
        if not close or datetime.date.fromisoformat(close) < cutoff:
            continue
        th = tag(ti, cfg["themes"])
        if cfg["require_core"]:
            if th[0] == "general" and not any(w in til for w in cfg["core"]):
                continue
        else:
            if th[0] == "general":      # FAP profile keeps only clearly on-theme opps
                continue
        kept.append({"number": o.get("number"), "title": ti, "agency": o.get("agency"),
                     "close": close, "cfda": (o.get("cfdaList") or [""])[0], "themes": th,
                     "url": "https://www.grants.gov/search-results-detail/" + str(o.get("id"))})
    kept.sort(key=lambda x: x["close"])
    kept = kept[:32]

    out = {"source": cfg["source"], "source_url": "https://www.grants.gov",
           "pulled": datetime.date.today().isoformat(), "note": cfg["note"], "opportunities": kept}
    if cfg.get("profile_desc"):
        out["profile"] = cfg["profile_desc"]
    (ROOT / cfg["out"]).write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"Wrote {cfg['out']} — {len(kept)} open opportunities (profile '{profile}', {len(merged)} raw hits).")


if __name__ == "__main__":
    prof = sys.argv[1] if len(sys.argv) > 1 else "county"
    if prof not in PROFILES:
        raise SystemExit(f"Unknown profile '{prof}'. Options: {', '.join(PROFILES)}")
    try:
        main(prof)
    except Exception as e:
        print(f"Grants.gov pull failed ({e}); keeping existing file.", file=sys.stderr)
        sys.exit(1)
