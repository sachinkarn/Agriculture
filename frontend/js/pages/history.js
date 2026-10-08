/* history page */
V.history=function(){const h=S.hist;
 return `<div class="top"><div><h1>History</h1><p>Every analysis you have run on this device.</p></div>${h.length?'<button class="alt" id="clr">Clear history</button>':""}</div>
 <div class="card">${h.length?`<table><tr><th>When</th><th>Type</th><th>Result</th></tr>${h.map(x=>`<tr><td>${esc(x.t)}</td><td>${esc(x.type)}</td><td>${esc(x.res)}</td></tr>`).join("")}</table>`:'<p class="mut">Nothing yet. Run a crop analysis or get irrigation advice and it shows up here.</p>'}</div>`};

H.history=function(){const c=$("#clr");if(c)c.onclick=()=>{S.hist=[];save();route()}};
