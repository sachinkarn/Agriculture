function sampleWx(){const d=new Date(),i=(d.getDate()+d.getHours())%SAMPLE_WX.length;return Object.assign({source:"sample"},SAMPLE_WX[i])}
function refreshWx(){const p=(location.hash||"#dashboard").slice(1);if(p==="dashboard"||p==="irrigation")route(true)}/* re-render only, no new fetch */
let wxSeq=0;/* ignore a slow, older response if a newer load has started */
async function loadWx(fresh){
 const n=++wxSeq;
 if(fresh){S.wx=null;refreshWx()}/* never show last visit's weather as if it were current */
 if(API){try{const r=await fetch(API+"/api/weather"+(fresh?"?fresh=1":""),{cache:"no-store"});if(r.ok){const w=await r.json();if(n!==wxSeq)return;S.wx=w;refreshWx();return}}catch(e){}}
 if(n!==wxSeq)return;S.wx=sampleWx();refreshWx()}
