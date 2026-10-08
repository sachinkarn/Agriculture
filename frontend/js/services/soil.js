/* Soil scoring logic */
function soilScore(s){let sc=100,adv=[],prob=[],fert=[];
 const lv={n:s.n<280?"Low":s.n>450?"High":"Good",p:s.p<11?"Low":"Good",k:s.k<110?"Low":"Good",ph:s.ph<5.8?"Acidic":s.ph>7.8?"Alkaline":"Optimal"};
 if(s.n<280){sc-=15;prob.push("Nitrogen is low");fert.push("Apply urea in two small splits");adv.push("Nitrogen is low: apply urea in two small splits instead of one heavy dose.")}else if(s.n>450){sc-=8;prob.push("Nitrogen is high");fert.push("Skip nitrogen top-dressing");adv.push("Nitrogen is high: skip nitrogen top-dressing this round.")}
 if(s.p<11){sc-=15;prob.push("Phosphorus is low");fert.push("Add DAP or SSP at sowing");adv.push("Phosphorus is low: add DAP or SSP at sowing.")}
 if(s.k<110){sc-=12;prob.push("Potassium is low");fert.push("Add muriate of potash");adv.push("Potassium is low: add muriate of potash.")}
 if(s.ph<5.8){sc-=14;prob.push("Soil is acidic");fert.push("Add agricultural lime");adv.push("Soil is acidic: add agricultural lime before sowing.")}else if(s.ph>7.8){sc-=14;prob.push("Soil is alkaline");fert.push("Add gypsum or organic matter");adv.push("Soil is alkaline: add gypsum or organic matter.")}
 if(!adv.length)adv.push("Nutrients look balanced. Skip extra fertilizer and re-test next season.");
 return{sc:Math.max(35,sc),adv,lv,prob,main:prob[0]||"None. Nutrients look balanced",fert:fert[0]||"No extra fertilizer needed"}}
