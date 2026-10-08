/* reco page */
V.reco=function(){const s=S.soil;
 return `<div class="top"><div><h1>Recommendations</h1><p>Crops that suit your soil, plus the fertilizer plan.</p></div></div>
 <div class="grid g2"><div class="card"><label for="rw">Water available this season</label><select id="rw"><option value="L">Low</option><option value="M" selected>Medium</option><option value="H">High</option></select>
 <p class="mut" style="font-size:13px">Uses your soil values: pH ${s.ph}, nitrogen ${s.n}, moisture ${s.m}%. Change them on the Soil analysis page.</p><div id="rc"></div></div>
 <div class="card"><h3>Fertilizer plan</h3>${list(soilScore(s).adv)}</div></div>`};

H.reco=function(){const run=()=>{const s=S.soil,w=$("#rw").value;
  const res=CROPS.map(c=>{let sc=40;const[a,b]=c[1];sc+=s.ph>=a&&s.ph<=b?30:Math.max(0,30-Math.min(Math.abs(s.ph-a),Math.abs(s.ph-b))*15);
   const nl=s.n<280?1:s.n<450?2:3;sc+=20-Math.abs(nl-LV[c[2]])*8;sc+=10-Math.abs(LV[w]-LV[c[3]])*5;return[c[0],Math.round(Math.max(30,Math.min(98,sc)))]}).sort((x,y)=>y[1]-x[1]).slice(0,4);
  $("#rc").innerHTML=`<h3 style="margin-top:12px">Best crops for you</h3>`+res.map(r=>`<div style="margin:10px 0"><div class="row"><b>${r[0]}</b><span>${r[1]}% match</span></div><div class="bar"><i style="width:${r[1]}%"></i></div></div>`).join("")};
 $("#rw").onchange=run;run()};
