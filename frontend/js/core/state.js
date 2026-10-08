/* Global app state, persisted to localStorage */
let S={hist:[],soil:{n:240,p:14,k:130,ph:6.4,m:45},last:null,irr:null,crop:"Apple",img:null,wx:null,mlog:[]};
try{const d=JSON.parse(localStorage.getItem("agri")||"null");if(d)S=Object.assign(S,d);S.img=null;S.file=null;S.wx=null}catch(e){}
const save=()=>{try{localStorage.setItem("agri",JSON.stringify(Object.assign({},S,{img:null,file:null,wx:null})))}catch(e){}};
