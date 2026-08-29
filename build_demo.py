#!/usr/bin/env python3
"""Assemble the self-contained Needs Atlas demo (sample data inlined) for publishing."""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
js = (ROOT / "web" / "sample-data.js").read_text()
data = js[js.index("{"): js.rindex("}") + 1]   # extract the JSON blob

TEMPLATE = r"""<title>Needs Atlas Demo</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700;12..96,800&family=IBM+Plex+Mono:wght@400;500;600&family=Public+Sans:wght@400;500;600;700&display=swap');
  :root{
    --ground:#EDF1EE;--paper:#FBFCFB;--paper-2:#F3F7F4;--ink:#16211D;--ink-soft:#4F615A;--ink-faint:#7B8C84;
    --line:#D8E1DC;--line-strong:#C1CFC8;--primary:#1E6B57;--primary-deep:#124A3B;--primary-soft:#E1EDE8;
    --heat-lo:#E4B24A;--heat-mid:#DE7C3B;--heat-hi:#C0442E;--good:#2E7D5B;
    --shadow:0 1px 2px rgba(20,40,34,.05),0 8px 26px rgba(20,40,34,.06);--radius:14px;
  }
  :root[data-theme="dark"],:root:not([data-theme="light"]){@media (prefers-color-scheme:dark){
    --ground:#0C1411;--paper:#14201C;--paper-2:#1A2723;--ink:#E6EEE9;--ink-soft:#9EB0A8;--ink-faint:#71827A;
    --line:#253431;--line-strong:#33443E;--primary:#53BF9F;--primary-deep:#82D4BA;--primary-soft:#16302A;
    --heat-lo:#E7C062;--heat-mid:#E88A4C;--heat-hi:#E4634A;--good:#57C08C;
    --shadow:0 1px 2px rgba(0,0,0,.3),0 10px 30px rgba(0,0,0,.35);
  }}
  :root[data-theme="dark"]{
    --ground:#0C1411;--paper:#14201C;--paper-2:#1A2723;--ink:#E6EEE9;--ink-soft:#9EB0A8;--ink-faint:#71827A;
    --line:#253431;--line-strong:#33443E;--primary:#53BF9F;--primary-deep:#82D4BA;--primary-soft:#16302A;
    --heat-lo:#E7C062;--heat-mid:#E88A4C;--heat-hi:#E4634A;--good:#57C08C;
    --shadow:0 1px 2px rgba(0,0,0,.3),0 10px 30px rgba(0,0,0,.35);
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--ground);color:var(--ink);font-family:"Public Sans",system-ui,sans-serif;font-size:15px;line-height:1.55;-webkit-font-smoothing:antialiased}
  h1,h2,h3{font-family:"Bricolage Grotesque","Public Sans",sans-serif;font-weight:700;margin:0;line-height:1.1}
  .mono{font-family:"IBM Plex Mono",monospace}

  /* gate */
  #gate{position:fixed;inset:0;z-index:50;display:flex;align-items:center;justify-content:center;
    background:linear-gradient(180deg,var(--paper-2),var(--ground));padding:24px}
  #gate .card{max-width:440px;width:100%;background:var(--paper);border:1px solid var(--line);border-radius:18px;
    padding:38px 34px;box-shadow:var(--shadow);text-align:center}
  #gate .lock{width:52px;height:52px;border-radius:14px;background:var(--primary-soft);display:flex;align-items:center;
    justify-content:center;margin:0 auto 18px;color:var(--primary);font-size:24px}
  #gate h1{font-size:1.9rem;letter-spacing:-.02em}
  #gate .sub{color:var(--ink-soft);font-size:14px;margin:8px 0 4px}
  #gate .org{font-family:"IBM Plex Mono",monospace;font-size:12px;color:var(--primary);letter-spacing:.08em;text-transform:uppercase;margin-top:14px}
  #gate .note{font-size:12.5px;color:var(--ink-faint);margin:22px 0 20px;padding-top:16px;border-top:1px solid var(--line)}
  #gate button{font-family:"Public Sans";font-weight:600;font-size:15px;background:var(--primary);color:#fff;border:0;
    border-radius:10px;padding:13px 22px;cursor:pointer;width:100%}
  #gate button:hover{background:var(--primary-deep)}

  /* app */
  #app{display:none;max-width:1160px;margin:0 auto;padding:0 20px 60px}
  .topbar{display:flex;align-items:center;gap:16px;flex-wrap:wrap;padding:18px 0;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--ground);z-index:10}
  .brand{font-family:"Bricolage Grotesque";font-weight:800;font-size:1.25rem;letter-spacing:-.01em}
  .brand .dot{color:var(--primary)}
  .spacer{flex:1}
  .badge{font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.09em;text-transform:uppercase;
    background:var(--heat-hi);color:#fff;padding:4px 9px;border-radius:6px}
  select{font-family:"Public Sans";font-size:14px;font-weight:600;color:var(--ink);background:var(--paper);
    border:1px solid var(--line-strong);border-radius:9px;padding:9px 12px;cursor:pointer}
  label.sel{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--ink-faint);margin-right:2px}

  .kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:22px 0}
  .kpi{background:var(--paper);border:1px solid var(--line);border-radius:12px;padding:16px 16px;box-shadow:var(--shadow)}
  .kpi .k{font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.07em;text-transform:uppercase;color:var(--ink-faint)}
  .kpi .v{font-family:"Bricolage Grotesque";font-weight:700;font-size:1.7rem;margin-top:6px;line-height:1}
  .kpi .u{font-size:12px;color:var(--ink-soft);margin-top:3px}
  .kpi.hot .v{color:var(--heat-hi)}

  .grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px}
  @media (max-width:840px){.grid2{grid-template-columns:1fr}}
  .panel{background:var(--paper);border:1px solid var(--line);border-radius:var(--radius);padding:20px;box-shadow:var(--shadow)}
  .panel h3{font-size:1.02rem;margin-bottom:4px}
  .panel .cap{font-size:12.5px;color:var(--ink-faint);margin-bottom:14px}
  .chartwrap{position:relative;height:260px}

  /* heat grid */
  .maprow{display:grid;grid-template-columns:1fr;gap:16px;margin-bottom:16px}
  .heatnote{display:flex;gap:8px;align-items:center;font-size:12px;color:var(--ink-faint);margin-top:12px;flex-wrap:wrap}
  .ramp{display:inline-flex;height:10px;width:120px;border-radius:3px;background:linear-gradient(90deg,#3f8f74,var(--heat-lo),var(--heat-hi))}
  .cells{display:flex;flex-wrap:wrap;gap:4px;margin-top:4px}
  .cell{width:20px;height:20px;border-radius:4px;cursor:default}
  .embed-ph{border:1px dashed var(--line-strong);border-radius:10px;padding:16px;margin-top:16px;background:var(--paper-2);
    font-size:13px;color:var(--ink-soft)}
  .embed-ph b{color:var(--ink)}

  table{width:100%;border-collapse:collapse;font-size:13.5px}
  th,td{text-align:left;padding:9px 10px;border-bottom:1px solid var(--line)}
  th{font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-faint);font-weight:500}
  td.mono{font-family:"IBM Plex Mono",monospace;font-size:12.5px}
  .score-pill{display:inline-block;min-width:38px;text-align:center;padding:2px 8px;border-radius:20px;font-weight:600;font-size:12.5px;color:#fff}

  .docs{display:flex;flex-wrap:wrap;gap:10px;margin-top:8px}
  .doc{display:flex;align-items:center;gap:10px;background:var(--paper-2);border:1px solid var(--line);border-radius:9px;padding:10px 14px;font-size:13px;color:var(--ink-soft)}
  footer{margin-top:28px;padding-top:18px;border-top:1px solid var(--line);font-family:"IBM Plex Mono",monospace;font-size:11.5px;color:var(--ink-faint)}
</style>

<div id="gate">
  <div class="card">
    <div class="lock" aria-hidden="true">&#128274;</div>
    <h1>Needs Atlas</h1>
    <div class="sub">Community health-needs &amp; grant-intelligence tool</div>
    <div class="org">Zufall Health &middot; Food Aid Project</div>
    <div class="note">Demo preview &mdash; illustrative sample data, not live ACS values. The production site is login-gated with Firebase Authentication.</div>
    <button id="enter">Enter demo &rarr;</button>
  </div>
</div>

<div id="app">
  <div class="topbar">
    <div class="brand">Needs Atlas<span class="dot">.</span></div>
    <span class="badge">Demo data</span>
    <div class="spacer"></div>
    <label class="sel" for="county">County</label>
    <select id="county"></select>
  </div>

  <div class="kpis" id="kpis"></div>

  <div class="grid2">
    <div class="panel">
      <h3>Composite need score by county</h3>
      <div class="cap">Higher = greater concentration of low-income, uninsured, and access-barrier residents. Selected county highlighted.</div>
      <div class="chartwrap"><canvas id="countyChart"></canvas></div>
    </div>
    <div class="panel">
      <h3 id="profTitle">Indicator profile</h3>
      <div class="cap">Selected county vs. the 7-county average.</div>
      <div class="chartwrap"><canvas id="profChart"></canvas></div>
    </div>
  </div>

  <div class="maprow">
    <div class="panel">
      <h3 id="heatTitle">Tract-level need heat map</h3>
      <div class="cap">Each square is a census tract, shaded by need score &mdash; the pattern the live map shows geographically.</div>
      <div class="cells" id="cells"></div>
      <div class="heatnote"><span>Lower</span><span class="ramp"></span><span>Higher need</span></div>
      <div class="embed-ph"><b>In production:</b> this panel is the live <b>ArcGIS time-enabled heat map</b> &mdash; the real tract geography with a year slider to animate how need shifts over time, embedded from the Food Aid Project ArcGIS org.</div>
    </div>
  </div>

  <div class="grid2">
    <div class="panel">
      <h3 id="tableTitle">Highest-need tracts</h3>
      <div class="cap">Where to focus &mdash; and the numbers that go straight into a grant narrative.</div>
      <div style="overflow-x:auto"><table id="tractTable"></table></div>
    </div>
    <div class="panel">
      <h3>Grant materials library</h3>
      <div class="cap">In production, a shared folder of reference docs, prior assessments, and generated profiles.</div>
      <div class="docs">
        <div class="doc">&#128196; HRSA needs-assessment template</div>
        <div class="doc">&#128196; Prior UDS report</div>
        <div class="doc">&#128196; County community profile (PDF export)</div>
        <div class="doc">&#128196; Methodology &amp; sources</div>
      </div>
      <div class="embed-ph" style="margin-top:18px"><b>Coming in the intelligence phase:</b> matched open grants for the selected profile, and an auto-drafted, source-cited "community need" paragraph.</div>
    </div>
  </div>

  <footer>Needs Atlas &middot; demo build &middot; sample data &middot; Food Aid Project, Inc. &mdash; the live tool runs on real ACS, PLACES &amp; SVI data keyed to 2020 census tracts.</footer>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<script>
window.ATLAS_SAMPLE = /*DATA*/;
(function(){
  const D = window.ATLAS_SAMPLE;
  const counties = D.counties;
  const cssv = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  const fmt = n => n==null?'&mdash;':Number(n).toLocaleString();
  const avg = k => Math.round((counties.reduce((s,c)=>s+c[k],0)/counties.length)*10)/10;

  // heat color from need score (0-100): green -> amber -> red
  function heat(s){
    if(s==null) return cssv('--line');
    const stops=[[10,[63,143,116]],[45,[228,178,74]],[100,[192,68,46]]];
    s=Math.max(0,Math.min(100,s));
    let a=stops[0],b=stops[stops.length-1];
    for(let i=0;i<stops.length-1;i++){if(s>=stops[i][0]&&s<=stops[i+1][0]){a=stops[i];b=stops[i+1];break;}}
    const t=(s-a[0])/((b[0]-a[0])||1);
    const c=a[1].map((v,i)=>Math.round(v+(b[1][i]-v)*t));
    return `rgb(${c[0]},${c[1]},${c[2]})`;
  }

  const sel=document.getElementById('county');
  counties.forEach(c=>{const o=document.createElement('option');o.value=c.county;o.textContent=c.county+' County';sel.appendChild(o);});

  let countyChart, profChart;
  function render(name){
    const c=counties.find(x=>x.county===name);
    // KPIs
    const kpis=[
      ['Population',fmt(c.population),''],
      ['Need score',c.need_score,'0&ndash;100',true],
      ['Uninsured',c.uninsured_pct+'%',''],
      ['Under 200% FPL',c.under_200_fpl_pct+'%',''],
      ['Limited English',c.lep_pct+'%',''],
      ['Age 65+',c.pct_65_plus+'%',''],
      ['Median income','$'+fmt(c.median_hh_income),'']
    ];
    document.getElementById('kpis').innerHTML=kpis.map(k=>
      `<div class="kpi ${k[3]?'hot':''}"><div class="k">${k[0]}</div><div class="v">${k[1]}</div><div class="u">${k[2]}</div></div>`).join('');

    // county bar chart
    const labels=counties.map(x=>x.county);
    const vals=counties.map(x=>x.need_score);
    const colors=counties.map(x=>x.county===name?heat(x.need_score):cssv('--line-strong'));
    if(countyChart)countyChart.destroy();
    countyChart=new Chart(document.getElementById('countyChart'),{type:'bar',
      data:{labels,datasets:[{data:vals,backgroundColor:colors,borderRadius:6}]},
      options:{plugins:{legend:{display:false}},scales:{
        y:{beginAtZero:true,grid:{color:cssv('--line')},ticks:{color:cssv('--ink-soft')}},
        x:{grid:{display:false},ticks:{color:cssv('--ink-soft'),font:{size:11}}}}}});

    // profile chart: county vs avg across indicators
    document.getElementById('profTitle').textContent=name+' County — indicator profile';
    const inds=[['Poverty','pov_rate'],['Uninsured','uninsured_pct'],['<200% FPL','under_200_fpl_pct'],['Limited Eng.','lep_pct'],['Age 65+','pct_65_plus']];
    if(profChart)profChart.destroy();
    profChart=new Chart(document.getElementById('profChart'),{type:'bar',
      data:{labels:inds.map(i=>i[0]),datasets:[
        {label:name,data:inds.map(i=>c[i[1]]),backgroundColor:cssv('--primary'),borderRadius:5},
        {label:'7-county avg',data:inds.map(i=>avg(i[1])),backgroundColor:cssv('--heat-lo'),borderRadius:5}]},
      options:{plugins:{legend:{labels:{color:cssv('--ink-soft'),font:{size:11},boxWidth:12}}},
        scales:{y:{beginAtZero:true,grid:{color:cssv('--line')},ticks:{color:cssv('--ink-soft')}},
        x:{grid:{display:false},ticks:{color:cssv('--ink-soft'),font:{size:10}}}}}});

    // heat grid of tracts
    const tr=D.tracts.filter(t=>t.county_name===name).sort((a,b)=>b.need_score-a.need_score);
    document.getElementById('heatTitle').textContent=name+' County — '+tr.length+' census tracts by need';
    document.getElementById('cells').innerHTML=tr.map(t=>
      `<div class="cell" title="Tract ${t.GEOID} · need ${t.need_score} · uninsured ${t.uninsured_pct}%" style="background:${heat(t.need_score)}"></div>`).join('');

    // table: top 8 tracts
    document.getElementById('tableTitle').textContent='Highest-need tracts — '+name+' County';
    const top=tr.slice(0,8);
    document.getElementById('tractTable').innerHTML=
      '<tr><th>Tract (GEOID)</th><th>Need</th><th>Uninsured</th><th>&lt;200% FPL</th><th>Median income</th></tr>'+
      top.map(t=>`<tr><td class="mono">${t.GEOID}</td>
        <td><span class="score-pill" style="background:${heat(t.need_score)}">${t.need_score}</span></td>
        <td>${t.uninsured_pct}%</td><td>${t.under_200_fpl_pct}%</td><td>$${fmt(t.median_hh_income)}</td></tr>`).join('');
  }

  document.getElementById('enter').addEventListener('click',()=>{
    document.getElementById('gate').style.display='none';
    document.getElementById('app').style.display='block';
  });
  sel.addEventListener('change',e=>render(e.target.value));
  render(counties[0].county);
})();
</script>
"""

out = TEMPLATE.replace("/*DATA*/", data)
(ROOT / "needs-atlas-demo.html").write_text(out)
print("wrote needs-atlas-demo.html", len(out), "bytes")
