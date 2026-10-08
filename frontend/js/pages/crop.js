/* crop page */
V.crop=function(){if(!DIS[S.crop])S.crop="Apple";return `<div class="top"><div><h1>Crop analysis</h1><p>Upload a leaf photo. The AI checks for disease and tells you what to do.</p></div></div>
 <div class="grid g2"><div class="card"><label for="cs">Crop</label><select id="cs">${Object.keys(DIS).map(c=>`<option ${c===S.crop?"selected":""}>${c}</option>`).join("")}</select>
 <label>Leaf photo</label><div class="drop" id="drop">${S.img?`<img src="${S.img}" alt="Leaf preview">`:"<div>📷<br>No photo yet<br>Choose a photo or use a sample</div>"}</div>
 <input type="file" id="file" accept="image/*" hidden>
 <div class="row" style="margin-top:12px;flex-wrap:wrap"><button class="alt" id="pick">Choose photo</button><button class="alt" id="sd">Sample: diseased</button><button class="alt" id="sh">Sample: healthy</button></div>
 <button id="go" style="width:100%;margin-top:12px">Analyse crop</button></div>
 <div class="card"><h3>Result</h3><div id="out" class="mut">Your result will appear here, with confidence, severity and next steps.</div></div></div>
`};

H.crop=function(){const sel=$("#cs");sel.onchange=()=>S.crop=sel.value;
 const file=$("#file");$("#pick").onclick=()=>file.click();
 const show=u=>{S.img=u;$("#drop").innerHTML=`<img src="${u}" alt="Leaf preview">`};
 file.onchange=()=>{const f=file.files[0];if(f){S.file=f;S.seed=f.size;S.healthy=false;show(URL.createObjectURL(f))}};
 const svg=(c)=>"data:image/svg+xml,"+encodeURIComponent(`<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 300 200'><rect width='300' height='200' fill='#CFE3C6'/><path d='M40 100C90 20 210 20 260 100C210 180 90 180 40 100Z' fill='#4E9A5F'/><path d='M40 100H260' stroke='#2E6B3D' stroke-width='4'/>${c}</svg>`);
 $("#sd").onclick=()=>{S.file=null;S.seed=7;S.healthy=false;show(svg("<ellipse cx='130' cy='80' rx='16' ry='9' fill='#8A5A2B'/><ellipse cx='185' cy='125' rx='20' ry='10' fill='#8A5A2B'/><ellipse cx='95' cy='120' rx='10' ry='6' fill='#A87A45'/>"))};
 $("#sh").onclick=()=>{S.file=null;S.seed=3;S.healthy=true;show(svg(""))};
 $("#go").onclick=async()=>{if(!S.img){toast("Choose or pick a sample photo first");return}
  const out=$("#out");out.innerHTML="Analysing…";let r=null;
  let warn="";
  if(API&&S.file){try{const fd=new FormData();fd.append("file",S.file);fd.append("crop",S.crop);const res=await fetch(API+"/api/crop/analyze",{method:"POST",body:fd});
   if(res.ok){const j=await res.json();r={d:j.healthy?"Healthy":j.disease,conf:Math.round(j.confidence*100),sev:j.healthy?"None":j.severity,ok:!!j.healthy,src:"model",acts:j.actions,unc:!!j.uncertain}}
   else if(res.status===503)warn="The disease model is not installed on the server yet, so this is a demo result, not a real diagnosis.";
   else{let m="";try{m=(await res.json()).detail}catch(e){}warn="The server could not analyse this photo"+(m?": "+m:" (error "+res.status+")")+". Showing a demo result."}
  }catch(e){warn="Could not reach the analysis service. Showing a demo result, not a real diagnosis."}}
  if(!r){await new Promise(z=>setTimeout(z,700));const seed=S.seed||7,ok=S.healthy;r={d:ok?"Healthy":DIS[S.crop][0],conf:ok?96:82+seed%15,sev:ok?"None":["Low","Medium","High"][(seed+1)%3],ok}}
  const c=S.crop,d=DIS[c],ok=r.ok,demo=r.src!=="model",pen={Low:12,Medium:22,High:38}[r.sev]||0;
  const score=ok?94:Math.max(40,100-pen-(100-r.conf)),acts=ok?["Keep your current routine","Scout once a week"]:(r.acts&&r.acts.length?r.acts:d[2]),st=r.unc?", uncertain":"";
  S.last={crop:c,d:r.d,conf:r.conf,sev:r.sev,score,acts,t:now(),src:r.src,unc:!!r.unc};
  S.hist.unshift({t:now(),type:"Crop analysis",res:`${c}: ${ok?"Healthy":r.d} (${r.conf}%${st})`});save();
  const tag=demo?'<span class="chip">Demo prediction</span>':'<span class="chip">Model prediction</span>';
  const wn=(warn?`<div class="alert a-red">${esc(warn)}</div>`:"")+(r.unc?'<div class="alert a-red">Low confidence: the model is not sure. Retake the photo in good light with one leaf filling the frame, or ask your local agri officer.</div>':"");
  out.innerHTML=tag+wn+(ok?`<h2 style="margin-top:8px">Healthy ${c}</h2><p class="mut">Confidence ${r.conf}%${st}</p><div class="alert a-grn">✔ No disease signs found</div>${list(acts)}`:
  `<h2 style="margin-top:8px">${demo||r.unc?"Possible ":""}${r.d}</h2><p class="mut" style="margin:2px 0">${c} · ${d[1]} issue</p><p style="margin:10px 0 4px">Confidence ${r.conf}%${st}</p><div class="bar"><i style="width:${r.conf}%"></i></div><p style="margin:12px 0 4px"><span class="pill">${r.sev} severity</span></p><b>What to do</b>${list(acts)}`);
  toast("Saved to history")}};
