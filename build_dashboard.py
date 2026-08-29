#!/usr/bin/env python3
"""Build the REAL-data Needs Atlas dashboard (county-level Census QuickFacts) -> needs-atlas-demo.html"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
R = json.loads((ROOT / "config" / "real_counties.json").read_text())
counties = R["counties"]; state = R["state"]

# Relative Need Index (0-100 across the 7 service-area counties): min-max of
# poverty% and uninsured% averaged. Transparent and defensible.
def mm(vals):
    lo, hi = min(vals), max(vals); span = (hi - lo) or 1.0
    return [(v - lo) / span for v in vals]
pov = mm([c["poverty_pct"] for c in counties])
uni = mm([c["uninsured_under65_pct"] for c in counties])
for c, p, u in zip(counties, pov, uni):
    c["need_index"] = round((p + u) / 2 * 100, 1)

DATA = json.dumps({"counties": counties, "state": state}, separators=(",", ":"))

TEMPLATE = r"""<title>Needs Atlas Demo</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700;12..96,800&family=IBM+Plex+Mono:wght@400;500;600&family=Public+Sans:wght@400;500;600;700&display=swap');
  :root{--ground:#EDF1EE;--paper:#FBFCFB;--paper-2:#F3F7F4;--ink:#16211D;--ink-soft:#4F615A;--ink-faint:#7B8C84;
    --line:#D8E1DC;--line-strong:#C1CFC8;--primary:#1E6B57;--primary-deep:#124A3B;--primary-soft:#E1EDE8;
    --heat-lo:#E4B24A;--heat-mid:#DE7C3B;--heat-hi:#C0442E;--shadow:0 1px 2px rgba(20,40,34,.05),0 8px 26px rgba(20,40,34,.06);--radius:14px;}
  :root[data-theme="dark"],:root:not([data-theme="light"]){@media (prefers-color-scheme:dark){
    --ground:#0C1411;--paper:#14201C;--paper-2:#1A2723;--ink:#E6EEE9;--ink-soft:#9EB0A8;--ink-faint:#71827A;
    --line:#253431;--line-strong:#33443E;--primary:#53BF9F;--primary-deep:#82D4BA;--primary-soft:#16302A;
    --heat-lo:#E7C062;--heat-mid:#E88A4C;--heat-hi:#E4634A;--shadow:0 1px 2px rgba(0,0,0,.3),0 10px 30px rgba(0,0,0,.35);}}
  :root[data-theme="dark"]{--ground:#0C1411;--paper:#14201C;--paper-2:#1A2723;--ink:#E6EEE9;--ink-soft:#9EB0A8;--ink-faint:#71827A;
    --line:#253431;--line-strong:#33443E;--primary:#53BF9F;--primary-deep:#82D4BA;--primary-soft:#16302A;
    --heat-lo:#E7C062;--heat-mid:#E88A4C;--heat-hi:#E4634A;--shadow:0 1px 2px rgba(0,0,0,.3),0 10px 30px rgba(0,0,0,.35);}
  *{box-sizing:border-box}
  body{margin:0;background:var(--ground);color:var(--ink);font-family:"Public Sans",system-ui,sans-serif;font-size:15px;line-height:1.55;-webkit-font-smoothing:antialiased}
  h1,h2,h3{font-family:"Bricolage Grotesque","Public Sans",sans-serif;font-weight:700;margin:0;line-height:1.1}
  #gate{position:fixed;inset:0;z-index:50;display:flex;align-items:center;justify-content:center;background:linear-gradient(180deg,var(--paper-2),var(--ground));padding:24px}
  #gate .card{max-width:440px;width:100%;background:var(--paper);border:1px solid var(--line);border-radius:18px;padding:38px 34px;box-shadow:var(--shadow);text-align:center}
  #gate .lock{width:52px;height:52px;border-radius:14px;background:var(--primary-soft);display:flex;align-items:center;justify-content:center;margin:0 auto 18px;color:var(--primary);font-size:24px}
  #gate h1{font-size:1.9rem;letter-spacing:-.02em}
  #gate .sub{color:var(--ink-soft);font-size:14px;margin:8px 0 4px}
  #gate .org{font-family:"IBM Plex Mono",monospace;font-size:12px;color:var(--primary);letter-spacing:.08em;text-transform:uppercase;margin-top:14px}
  #gate .note{font-size:12.5px;color:var(--ink-faint);margin:22px 0 20px;padding-top:16px;border-top:1px solid var(--line)}
  #gate button{font-family:"Public Sans";font-weight:600;font-size:15px;background:var(--primary);color:#fff;border:0;border-radius:10px;padding:13px 22px;cursor:pointer;width:100%}
  #app{display:none;max-width:1160px;margin:0 auto;padding:0 20px 60px}
  .topbar{display:flex;align-items:center;gap:14px;flex-wrap:wrap;padding:18px 0;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--ground);z-index:10}
  .brand{font-family:"Bricolage Grotesque";font-weight:800;font-size:1.25rem}.brand .dot{color:var(--primary)}
  .spacer{flex:1}
  .badge{font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.09em;text-transform:uppercase;background:var(--primary);color:#fff;padding:4px 9px;border-radius:6px}
  select{font-family:"Public Sans";font-size:14px;font-weight:600;color:var(--ink);background:var(--paper);border:1px solid var(--line-strong);border-radius:9px;padding:9px 12px;cursor:pointer}
  label.sel{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--ink-faint)}
  .kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:22px 0}
  .kpi{background:var(--paper);border:1px solid var(--line);border-radius:12px;padding:15px 16px;box-shadow:var(--shadow)}
  .kpi .k{font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-faint)}
  .kpi .v{font-family:"Bricolage Grotesque";font-weight:700;font-size:1.6rem;margin-top:6px;line-height:1}
  .kpi .u{font-size:11.5px;color:var(--ink-soft);margin-top:4px}
  .kpi.hot .v{color:var(--heat-hi)}
  .grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px}@media (max-width:840px){.grid2{grid-template-columns:1fr}}
  .panel{background:var(--paper);border:1px solid var(--line);border-radius:var(--radius);padding:20px;box-shadow:var(--shadow)}
  .panel h3{font-size:1.02rem;margin-bottom:4px}.panel .cap{font-size:12.5px;color:var(--ink-faint);margin-bottom:14px}
  .chartwrap{position:relative;height:260px}
  .cells{display:flex;flex-wrap:wrap;gap:8px;margin-top:4px}
  .ccell{flex:1;min-width:120px;border-radius:10px;padding:12px 14px;color:#fff}
  .ccell .cn{font-weight:700;font-size:14px}.ccell .ci{font-family:"IBM Plex Mono",monospace;font-size:12px;opacity:.95;margin-top:2px}
  table{width:100%;border-collapse:collapse;font-size:13.5px}
  th,td{text-align:left;padding:9px 10px;border-bottom:1px solid var(--line)}
  th{font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-faint);font-weight:500}
  td.r,th.r{text-align:right}
  .score-pill{display:inline-block;min-width:38px;text-align:center;padding:2px 8px;border-radius:20px;font-weight:600;font-size:12.5px;color:#fff}
  .embed-ph{border:1px dashed var(--line-strong);border-radius:10px;padding:14px;margin-top:14px;background:var(--paper-2);font-size:13px;color:var(--ink-soft)}
  .embed-ph b{color:var(--ink)}
  footer{margin-top:28px;padding-top:18px;border-top:1px solid var(--line);font-family:"IBM Plex Mono",monospace;font-size:11.5px;color:var(--ink-faint)}
</style>

<div id="gate"><div class="card">
  <div class="lock">&#128202;</div>
  <h1>Needs Atlas</h1>
  <div class="sub">Community health-needs &amp; grant-intelligence tool</div>
  <div class="org">Zufall Health &middot; Food Aid Project</div>
  <div class="note"><b>Live data.</b> County figures are real U.S. Census Bureau QuickFacts values (2020&ndash;2024 ACS 5-year). The production site is login-gated with Firebase Authentication.</div>
  <button id="enter">Enter &rarr;</button>
</div></div>

<div id="app">
  <div class="topbar">
    <div class="brand">Needs Atlas<span class="dot">.</span></div>
    <span class="badge">&#9679; Live &middot; Census QuickFacts</span>
    <div class="spacer"></div>
    <label class="sel" for="county">County</label>
    <select id="county"></select>
  </div>
  <div class="kpis" id="kpis"></div>
  <div class="grid2">
    <div class="panel"><h3>Relative need index by county</h3><div class="cap">Poverty and uninsured rates combined, scaled across the 7-county service area. Selected county highlighted.</div><div class="chartwrap"><canvas id="countyChart"></canvas></div></div>
    <div class="panel"><h3 id="profTitle">County vs. New Jersey</h3><div class="cap">Selected county against the statewide figure &mdash; both real.</div><div class="chartwrap"><canvas id="profChart"></canvas></div></div>
  </div>
  <div class="panel" style="margin-bottom:16px">
    <h3>Service area by need</h3>
    <div class="cap">All seven counties, real Census figures. Essex and Union carry the highest need; the affluent northwest (Hunterdon, Morris) the lowest.</div>
    <div class="cells" id="cells"></div>
    <div class="embed-ph"><b>County-level, live.</b> Tract-level detail &mdash; the heat map that reveals need <i>within</i> each county &mdash; comes from the ACS pipeline (needs the API key run on GitHub/your machine). County figures above are QuickFacts and final.</div>
  </div>
  <div class="grid2">
    <div class="panel"><h3>Ranking &mdash; real figures</h3><div class="cap">Sortable in production; here, ordered by need.</div><div style="overflow-x:auto"><table id="tbl"></table></div></div>
    <div class="panel"><h3>What's live vs. next</h3>
      <div class="cap">Being transparent about the data.</div>
      <div style="font-size:13.5px;color:var(--ink-soft);line-height:1.6">
        <b style="color:var(--primary)">Live now (Census QuickFacts):</b> population, median income, poverty, uninsured under 65, race/ethnicity, seniors, language.<br><br>
        <b style="color:var(--heat-mid)">Next layer:</b> tract-level detail (ACS pipeline), and health/social figures &mdash; chronic disease &amp; maternal-infant (NJSHAD), provider ratios &amp; housing (County Health Rankings), ALICE (United Way), food insecurity (Feeding America).
      </div>
    </div>
  </div>
  <footer>Needs Atlas &middot; live county data: U.S. Census Bureau QuickFacts, 2020&ndash;2024 ACS 5-year estimates &middot; Food Aid Project, Inc.</footer>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<script>
window.ATLAS = /*DATA*/;
(function(){
  const C=ATLAS.counties, S=ATLAS.state;
  const cssv=n=>getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  const fmt=n=>Number(n).toLocaleString();
  function heat(s){const st=[[0,[63,143,116]],[45,[228,178,74]],[100,[192,68,46]]];s=Math.max(0,Math.min(100,s));
    let a=st[0],b=st[2];for(let i=0;i<2;i++){if(s>=st[i][0]&&s<=st[i+1][0]){a=st[i];b=st[i+1];break;}}
    const t=(s-a[0])/((b[0]-a[0])||1),c=a[1].map((v,i)=>Math.round(v+(b[1][i]-v)*t));return`rgb(${c[0]},${c[1]},${c[2]})`;}
  const sel=document.getElementById('county');
  C.slice().sort((a,b)=>a.county.localeCompare(b.county)).forEach(c=>{const o=document.createElement('option');o.value=c.county;o.textContent=c.county+' County';sel.appendChild(o);});
  let ch1,ch2;
  function render(name){
    const c=C.find(x=>x.county===name);
    const kpis=[['Population',fmt(c.population),''],
      ['Need index',c.need_index,'0&ndash;100 · service area',true],
      ['Poverty',c.poverty_pct+'%','NJ '+S.poverty_pct+'%'],
      ['Uninsured &lt;65',c.uninsured_under65_pct+'%','NJ '+S.uninsured_under65_pct+'%'],
      ['Language &ne; English',c.language_other_pct+'%','NJ '+S.language_other_pct+'%'],
      ['Age 65+',c.pct_65_plus+'%','NJ '+S.pct_65_plus+'%'],
      ['Median income','$'+fmt(c.median_hh_income),'NJ $'+fmt(S.median_hh_income)]];
    document.getElementById('kpis').innerHTML=kpis.map(k=>`<div class="kpi ${k[3]?'hot':''}"><div class="k">${k[0]}</div><div class="v">${k[1]}</div><div class="u">${k[2]}</div></div>`).join('');
    const ord=C.slice().sort((a,b)=>b.need_index-a.need_index);
    if(ch1)ch1.destroy();
    ch1=new Chart(document.getElementById('countyChart'),{type:'bar',
      data:{labels:ord.map(x=>x.county),datasets:[{data:ord.map(x=>x.need_index),backgroundColor:ord.map(x=>x.county===name?heat(x.need_index):cssv('--line-strong')),borderRadius:6}]},
      options:{plugins:{legend:{display:false}},scales:{y:{beginAtZero:true,grid:{color:cssv('--line')},ticks:{color:cssv('--ink-soft')}},x:{grid:{display:false},ticks:{color:cssv('--ink-soft'),font:{size:11}}}}}});
    document.getElementById('profTitle').textContent=name+' County vs. New Jersey';
    const inds=[['Poverty','poverty_pct'],['Uninsured','uninsured_under65_pct'],['Lang≠Eng','language_other_pct'],['Age 65+','pct_65_plus']];
    if(ch2)ch2.destroy();
    ch2=new Chart(document.getElementById('profChart'),{type:'bar',
      data:{labels:inds.map(i=>i[0]),datasets:[
        {label:name,data:inds.map(i=>c[i[1]]),backgroundColor:cssv('--primary'),borderRadius:5},
        {label:'New Jersey',data:inds.map(i=>S[i[1]]),backgroundColor:cssv('--heat-lo'),borderRadius:5}]},
      options:{plugins:{legend:{labels:{color:cssv('--ink-soft'),font:{size:11},boxWidth:12}}},scales:{y:{beginAtZero:true,grid:{color:cssv('--line')},ticks:{color:cssv('--ink-soft')}},x:{grid:{display:false},ticks:{color:cssv('--ink-soft'),font:{size:11}}}}}});
    document.getElementById('cells').innerHTML=ord.map(x=>`<div class="ccell" style="background:${heat(x.need_index)}"><div class="cn">${x.county}</div><div class="ci">need ${x.need_index} · ${x.poverty_pct}% pov · ${x.uninsured_under65_pct}% unins.</div></div>`).join('');
    document.getElementById('tbl').innerHTML='<tr><th>County</th><th class="r">Need</th><th class="r">Poverty</th><th class="r">Uninsured</th><th class="r">Median income</th></tr>'+
      ord.map(x=>`<tr><td>${x.county}</td><td class="r"><span class="score-pill" style="background:${heat(x.need_index)}">${x.need_index}</span></td><td class="r">${x.poverty_pct}%</td><td class="r">${x.uninsured_under65_pct}%</td><td class="r">$${fmt(x.median_hh_income)}</td></tr>`).join('');
  }
  document.getElementById('enter').addEventListener('click',()=>{document.getElementById('gate').style.display='none';document.getElementById('app').style.display='block';});
  sel.addEventListener('change',e=>render(e.target.value));
  render('Essex');
})();
</script>
"""
out = TEMPLATE.replace("/*DATA*/", DATA)
(ROOT / "needs-atlas-demo.html").write_text(out)
print("wrote needs-atlas-demo.html", len(out), "bytes; need index:",
      {c["county"]: c["need_index"] for c in counties})
