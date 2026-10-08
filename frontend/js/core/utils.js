/* Small DOM / formatting helpers */
const $=(q,r=document)=>r.querySelector(q);
const esc=s=>String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
const clamp=(v,a,b)=>Math.min(b,Math.max(a,Math.round(v)));
const toast=m=>{const t=$("#toast");t.textContent=m;t.classList.add("show");setTimeout(()=>t.classList.remove("show"),2200)};
const now=()=>new Date().toLocaleString([], {day:"numeric",month:"short",hour:"2-digit",minute:"2-digit"});
