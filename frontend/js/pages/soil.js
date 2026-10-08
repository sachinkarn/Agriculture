/* soil page */
V.soil=function(){const s=S.soil;
 const f=(id,l,min,max,st)=>`<label for="${id}">${l}: <b id="v-${id}">${s[id]}</b></label><input type="range" id="${id}" min="${min}" max="${max}" step="${st}" value="${s[id]}">`;
 return `<div class="top"><div><h1>Soil analysis</h1><p>Enter your soil values to get fertilizer advice.</p></div></div>
 <div class="grid g2"><div class="card">${f("n","Nitrogen (kg/ha)",100,600,10)}${f("p","Phosphorus (kg/ha)",2,40,1)}${f("k","Potassium (kg/ha)",40,300,5)}${f("ph","Soil pH",4,9,.1)}${f("m","Moisture (%)",5,90,1)}</div>
 <div class="card" id="sr">${soilCard(s)}</div></div>`};

H.soil=function(){["n","p","k","ph","m"].forEach(id=>{const e=$("#"+id);e.oninput=()=>{S.soil[id]=+e.value;$("#v-"+id).textContent=e.value;$("#sr").innerHTML=soilCard(S.soil);save()}})};
