function route(keep){const id=(location.hash||"#dashboard").slice(1),p=V[id]?id:"dashboard";
 $("#nav").innerHTML=`<div class="logo">🌱 KisanMitra AI</div>`+PAGES.map(x=>`<a href="#${x[0]}" class="${x[0]===p?"on":""}" ${x[0]===p?'aria-current="page"':""}><span aria-hidden="true">${x[1]}</span>${x[2]}</a>`).join("");
 $("#view").innerHTML=V[p]();if(H[p])H[p]();
 if(!keep){if(p==="dashboard")loadWx(true);else if(p==="irrigation"&&!S.wx)loadWx()}
 if(!keep)window.scrollTo(0,0)}
