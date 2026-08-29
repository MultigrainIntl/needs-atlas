#!/usr/bin/env python3
"""
generate_assessment.py — Generate a county Community Needs Assessment in Zufall's
house style.

County + statewide comparisons come from config/real_counties.json (Census
QuickFacts — consistent county/state fields). When the ACS pipeline has run
(data/tracts_need.csv present), the narrative is ENRICHED with real tract-level
detail (concentration of need within the county) — the thing county averages hide.

    python scripts/generate_assessment.py Union
"""
import csv, json, re, sys, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = json.loads((ROOT / "config" / "real_counties.json").read_text())
STATE = R["state"]
BY_NAME = {c["county"]: c for c in R["counties"]}
TRACTS = ROOT / "data" / "tracts_need.csv"
TODAY = datetime.date.today().strftime("%B %d, %Y")

CITES = {
    "qf": ("U.S. Census Bureau QuickFacts. {county} County, New Jersey and New Jersey. "
           "2020-2024 American Community Survey 5-Year Estimates and 2025 Population "
           "Estimates. Accessed " + TODAY + "."),
    "acs": ("U.S. Census Bureau, American Community Survey 5-Year Estimates, census-tract "
            "tables (C17002, B27001), retrieved via the Needs Atlas data pipeline. "
            "Accessed " + TODAY + "."),
}

PENDING_ALL = [
    ("alice", "ALICE (Asset Limited, Income Constrained, Employed) household rate",
     "United Way United For ALICE — New Jersey"),
    ("njshad", "Chronic disease prevalence, prenatal care, and infant mortality (incl. racial disparity)",
     "New Jersey State Health Assessment Data (NJSHAD)"),
    ("chr", "Primary-care and mental-health provider-to-population ratios; severe housing problems",
     "County Health Rankings & Roadmaps (Univ. of Wisconsin)"),
    ("feeding", "Food insecurity rate", "Feeding America — Map the Meal Gap"),
    ("tract", "Share below 200% of the federal poverty level, and tract-level detail",
     "ACS 5-year via the Needs Atlas pipeline"),
]

CITE_RE = re.compile(r"\[\[cite:([a-z_]+)\]\]")


def rel(cv, sv, hi="above", lo="below", eq="comparable to"):
    return eq if abs(cv - sv) < max(0.4, 0.03 * sv) else (hi if cv > sv else lo)


def tract_enrichment(county):
    """Return (sentence, has_tracts). Sentence uses real tract data if available."""
    if not TRACTS.exists():
        return ("County-wide averages, however, understate need that concentrates in "
                "specific urban communities; tract-level analysis (in progress) is "
                "required to locate it precisely.", False)
    rows = [r for r in csv.DictReader(TRACTS.open()) if r["county_name"] == county]
    def fnum(r, k):
        try: return float(r[k])
        except (ValueError, KeyError, TypeError): return None
    state_unins = STATE["uninsured_under65_pct"]
    n_high = sum(1 for r in rows if (fnum(r, "uninsured_pct") or 0) > state_unins)
    top = max(rows, key=lambda r: fnum(r, "need_score") or 0, default=None)
    if not top:
        return ("Tract-level detail is being finalized.", True)
    return (f"Beneath the county average, need concentrates sharply: {n_high} of "
            f"{len(rows)} census tracts exceed the statewide uninsured rate, and the "
            f"highest-need tract shows {top.get('uninsured_pct')}% uninsured with "
            f"{top.get('under_200_fpl_pct')}% of residents below 200% of the federal "
            f"poverty level.[[cite:acs]]", True)


def build(c):
    s = STATE
    tline, has_tracts = tract_enrichment(c["county"])
    secs = [
        ("Poverty, income, and the case for concentrated need",
         f"The communities Zufall Health serves within {c['county']} County, New Jersey "
         f"include urbanized areas with pockets of concentrated poverty and limited "
         f"access to care. {c['county']} County's median household income is "
         f"${c['median_hh_income']:,}, {rel(c['median_hh_income'], s['median_hh_income'], 'above', 'below', 'near')} "
         f"the statewide median of ${s['median_hh_income']:,}, and {c['poverty_pct']}% of "
         f"residents live in poverty, {rel(c['poverty_pct'], s['poverty_pct'])} the New "
         f"Jersey rate of {s['poverty_pct']}%.[[cite:qf]] {tline}"),
        ("Barriers to care: insurance and providers",
         f"Access to coverage is a clear barrier. {c['uninsured_under65_pct']}% of "
         f"{c['county']} County residents under age 65 are uninsured, "
         f"{rel(c['uninsured_under65_pct'], s['uninsured_under65_pct'])} the statewide "
         f"rate of {s['uninsured_under65_pct']}%.[[cite:qf]] Provider-supply measures — "
         f"primary-care and mental-health provider-to-population ratios — are pending "
         f"(see below) and are expected to reinforce this access gap."),
        ("Demographics and language access",
         f"{c['county']} County is home to {c['population']:,} residents. "
         f"{c['pct_hispanic']}% identify as Hispanic or Latino and {c['pct_black']}% as "
         f"Black or African American, compared with {s['pct_hispanic']}% and "
         f"{s['pct_black']}% statewide.[[cite:qf]] Language access is a substantial need: "
         f"{c['language_other_pct']}% of residents age 5 and over speak a language other "
         f"than English at home, {rel(c['language_other_pct'], s['language_other_pct'])} "
         f"the New Jersey figure of {s['language_other_pct']}%.[[cite:qf]] Adults age 65 "
         f"and over make up {c['pct_65_plus']}% of the population (New Jersey: "
         f"{s['pct_65_plus']}%).[[cite:qf]]"),
    ]
    pending = [p for p in PENDING_ALL if not (has_tracts and p[0] == "tract")]
    return secs, pending


def render_runs(secs):
    order = []
    def num(k):
        if k not in order: order.append(k)
        return str(order.index(k) + 1)
    out = []
    for title, text in secs:
        runs, pos = [], 0
        for m in CITE_RE.finditer(text):
            runs.append(("t", text[pos:m.start()])); runs.append(("c", num(m.group(1)))); pos = m.end()
        runs.append(("t", text[pos:]))
        out.append((title, runs))
    return out, order


def to_docx(c, secs, order, pending, path):
    from docx import Document
    from docx.shared import Pt, RGBColor, Inches
    doc = Document()
    sec = doc.sections[0]; sec.page_width, sec.page_height = Inches(8.5), Inches(11)
    sec.left_margin = sec.right_margin = Inches(1)
    doc.styles["Normal"].font.name = "Calibri"; doc.styles["Normal"].font.size = Pt(11)
    r = doc.add_paragraph().add_run(f"{c['county']} County Needs Assessment — {datetime.date.today():%B %Y}")
    r.bold = True; r.font.size = Pt(16)
    b = doc.add_paragraph().add_run(
        "Demographic figures below are live U.S. Census Bureau values. Health, ALICE, and "
        "provider indicators are pending source connection and are listed at the end.")
    b.italic = True; b.font.size = Pt(8.5); b.font.color.rgb = RGBColor(0x1E, 0x6B, 0x57)
    for title, runs in secs:
        doc.add_paragraph().add_run(title).bold = True
        p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(10)
        for kind, txt in runs:
            run = p.add_run(txt)
            if kind == "c": run.font.superscript = True
    doc.add_paragraph().add_run("Indicators pending source connection").bold = True
    for _, label, src in pending:
        pp = doc.add_paragraph(style="List Bullet")
        pp.add_run(label + " — ").font.size = Pt(10)
        em = pp.add_run(src); em.italic = True; em.font.size = Pt(10)
    doc.add_paragraph().add_run("References").bold = True
    for i, k in enumerate(order, 1):
        rp = doc.add_paragraph(f"{i}. " + CITES[k].format(county=c["county"]))
        for run in rp.runs: run.font.size = Pt(8.5)
    doc.save(path)


def to_md(c, secs, order, pending):
    out = [f"# {c['county']} County Needs Assessment — {datetime.date.today():%B %Y}", "",
           "_Demographic figures are live Census values; health/ALICE/provider indicators pending (listed below)._\n"]
    for title, runs in secs:
        out.append(f"## {title}")
        out.append("".join(t if k == "t" else f"[{t}]" for k, t in runs) + "\n")
    out.append("## Indicators pending source connection")
    out += [f"- {label} — *{src}*" for _, label, src in pending]
    out.append("\n## References")
    out += [f"{i}. " + CITES[k].format(county=c["county"]) for i, k in enumerate(order, 1)]
    return "\n".join(out)


def generate(name):
    if name not in BY_NAME:
        raise SystemExit(f"Unknown county '{name}'. Options: {', '.join(BY_NAME)}")
    c = BY_NAME[name]
    secs, pending = build(c)
    runs, order = render_runs(secs)
    outdir = ROOT / "data"; outdir.mkdir(exist_ok=True)
    stem = name.lower() + "_needs_assessment"
    (outdir / f"{stem}.md").write_text(to_md(c, runs, order, pending))
    to_docx(c, runs, order, pending, outdir / f"{stem}.docx")
    return stem


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "Union"
    stem = generate(name)
    print(f"Wrote {stem}.docx/.md for {name} County"
          + (" (with real tract enrichment)" if TRACTS.exists() else " (county-level; run pipeline for tract detail)"))
