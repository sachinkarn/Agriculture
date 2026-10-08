/* dashboard page */
V.dashboard=function(){const L=S.last||sample,i=S.irr,so=soilScore(S.soil),sh=so.sc,health=Math.round(L.score*.7+sh*.3);
 const bad=L.d!=="Healthy",demo=L.src!=="model",poss=demo||L.unc,acts=bad?L.acts:["Keep your current routine","Walk the field once a week"];
 const fung=bad&&DIS[L.crop]&&DIS[L.crop][1]==="fungal";
 const rows=[["🌱","Crop",L.crop],["⚠️","Risk",bad?`${poss?"Possible ":""}${L.d}, ${L.sev} severity`:"No disease signs found"],["💧","Water",i?i.title+(i.t?` (checked ${i.t})`:""):"Run the irrigation check"],["🧪","Fertilizer",fung?"Avoid additional nitrogen":so.fert],["👀","Check",acts[0]],["📅","Next check",bad?"In 48 hours":"In 7 days"]];
 const ml=(S.mlog||[]).slice(-7),real=ml.length>=2,days=real?ml:[62,55,48,45,40,36,33],lab=real?ml.map(v=>v+"%"):["Mon","Tue","Wed","Thu","Fri","Sat","Sun"];
 return `<div class="top"><div><h1>Good morning, farmer</h1><p>Here is what to do with your crop today.</p></div><span class="chip">${S.wx?`📍 Karaikal · ${Math.round(S.wx.temperature)}°C · humidity ${Math.round(S.wx.humidity)}% · rain ${Math.round(S.wx.rain_probability)}%`:"📍 Karaikal · loading weather…"}</span></div>
 <div class="grid g2"><div class="card"><div class="hero">${ringSVG(health)}<div><h3>${L.crop} · ${bad?L.d:"Healthy"}</h3><p class="mut" style="margin:2px 0">${demo?"Demo prediction · ":""}${L.unc?"Low confidence · ":""}Confidence ${L.conf}% · Severity ${L.sev}</p>
 <div class="alert ${bad?"a-red":"a-grn"}">${bad?"⚠ Possible "+L.d.toLowerCase()+". Check the leaves today.":"✔ No disease signs found."}</div></div></div></div>
 <div class="card hero2"><h2 style="margin-bottom:6px">Today's farm plan</h2>${rows.map(r=>`<div class="pr"><span aria-hidden="true">${r[0]}</span><div><small>${r[1]}</small><b>${r[2]}</b></div></div>`).join("")}</div></div>
 <div class="grid g3" style="margin-top:14px">
 <div class="card"><p class="mut" style="margin:0">Soil health</p><div class="big">${sh}</div><div class="bar"><i style="width:${sh}%"></i></div></div>
 <div class="card"><p class="mut" style="margin:0">Soil moisture now</p><div class="big">${S.soil.m}%</div><div class="bar"><i style="width:${S.soil.m}%;background:var(--blue)"></i></div></div>
 <div class="card"><p class="mut" style="margin:0">Estimated water saving</p><div class="big">${i?i.save+"%":"—"}</div><p class="mut" style="margin:0;font-size:13px">${i?"Model estimate. Actual savings may vary.":"Run the irrigation check to see this."}</p></div></div>
 <div class="card" style="margin-top:14px"><h3>${real?"Your last "+ml.length+" soil moisture readings":"Soil moisture this week (sample data)"}</h3><div class="bars" style="margin-bottom:24px">${days.map((d,k)=>`<div style="height:${d*1.3}px"><span>${lab[k]}</span></div>`).join("")}</div></div>
`};
