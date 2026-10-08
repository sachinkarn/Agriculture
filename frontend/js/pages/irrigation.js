/* irrigation page */
V.irrigation=function(){const s=S.soil,i=S.irr,w=S.wx,T=w?clamp(w.temperature,15,45):31,Hm=w?clamp(w.humidity,20,100):78,R=w?clamp(w.rain_probability,0,100):20;
 return `<div class="top"><div><h1>Irrigation</h1><p>Should you water today? Get a clear yes or no.</p></div></div>
 <div class="grid g2"><div class="card"><label for="ic">Crop</label><select id="ic">${["Apple","Corn","Orange","Potato"].map(c=>`<option ${c===S.crop?"selected":""}>${c}</option>`).join("")}</select>
 <label for="im">Soil moisture: <b id="vm">${s.m}</b>%</label><input type="range" id="im" min="5" max="90" value="${s.m}">
 <label for="it">Temperature: <b id="vt">${T}</b>°C</label><input type="range" id="it" min="15" max="45" value="${T}">
 <label for="ih">Humidity: <b id="vh">${Hm}</b>%</label><input type="range" id="ih" min="20" max="100" value="${Hm}">
 <label for="ir">Chance of rain: <b id="vr">${R}</b>%</label><input type="range" id="ir" min="0" max="100" value="${R}">
 <p class="mut" style="font-size:13px;margin:8px 0 0">${w?(w.source==="sample"?"Live weather is unavailable, so typical values were filled in. You can adjust them.":"Temperature, humidity and rain chance were filled from today's local forecast. You can adjust them."):"Live weather is unavailable. Set temperature, humidity and rain chance yourself."}</p>
 <button id="go" style="width:100%;margin-top:14px">Get irrigation advice</button></div>
 <div class="card"><h3>Advice</h3><div id="out">${i?decHTML(i):'<span class="mut">Your advice will appear here.</span>'}</div></div></div>`};

H.irrigation=function(){["m","t","h","r"].forEach(k=>{const e=$("#i"+k);e.oninput=()=>$("#v"+k).textContent=e.value});
 $("#go").onclick=async()=>{const mo=+$("#im").value,t=+$("#it").value,h=+$("#ih").value,r=+$("#ir").value,c=$("#ic").value;
  const dis=!!(S.last&&S.last.d!=="Healthy"),sick=dis&&h>70;let o;
  if(r>=60)o={title:"Do not irrigate today",why:`Rain chance is ${r}%, so rainfall will water the crop.`,save:25,mm:0,time:"No watering needed"};
  else if(mo>=55)o={title:"Do not irrigate today",why:`Soil moisture is ${mo}%, which is sufficient.`,save:18,mm:0,time:"Recheck tomorrow morning"};
  else if(mo<30)o={title:"Irrigate now",why:`Soil is dry (${mo}%) and rain chance is only ${r}%.`,save:0,mm:t>35?25:20,time:"Early morning",go:1};
  else o={title:"Light irrigation this evening",why:`Soil moisture is moderate (${mo}%) and rain chance is ${r}%.`,save:10,mm:10,time:"Evening"};
  if(sick&&o.mm)o.why+=" Water at the base. Wet leaves can spread the disease.";
  if(API){try{const res=await fetch(API+"/api/irrigation/advise",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({crop:c,soil_moisture:mo,temperature:t,humidity:h,rain_probability:r,diseased:dis})});
   if(res.ok){const j=await res.json();o={title:j.title,why:j.why,mm:j.mm,time:j.time,go:j.go?1:0,save:j.save,inp:j.inputs}}}catch(e){}}
  if(!o.inp)o.inp=[["Crop",c],["Soil moisture",mo+"%"],["Rain probability",r+"%"],["Temperature",t+"°C"],["Humidity",h+"%"]];
  o.t=now();S.irr=o;S.soil.m=mo;S.crop=c;S.mlog=(S.mlog||[]).concat(mo).slice(-7);S.hist.unshift({t:now(),type:"Irrigation",res:`${c}: ${o.title}`});save();
  $("#out").innerHTML=decHTML(o);toast("Saved to history")}};
