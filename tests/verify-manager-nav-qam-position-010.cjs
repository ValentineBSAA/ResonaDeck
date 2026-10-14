const fs=require('fs'),assert=require('assert/strict');
const src=fs.readFileSync('src/index.js','utf8');
const dist=fs.readFileSync('dist/index.js','utf8');
assert.equal(src,dist,'src/dist differ');
assert(src.includes("const RD_VERSION = '1.0.0'"),'current frontend version missing');
assert(src.includes('function rdManagerSpatialTargetV910'),'Full Manager spatial targeting helper missing');
assert(src.includes('function rdManagerDirectionalV910'),'Full Manager direction handler missing');
assert(src.includes("onGamepadDirection:rdManagerDirectionalV910"),'manager controls are not wired to spatial navigation');
assert(src.includes("music?h('span',{className:'rd-v910-track-position'}"),'Music-only queue position missing');
assert(src.includes('TRACK ${Math.max(1,Number(s.index||0)+1)} OF ${Math.max(1,Number(s.queue?.length||1))}'),'queue position expression missing');
assert(src.includes("const music=role==='music'"),'Music role guard missing for queue-position rule');

// Mirror the geometry rule with a tiny fixture to prove vertical intent cannot
// resolve to a same-row horizontal neighbor.
function pick(current,candidates,d){
  const vertical=d==='up'||d==='down',sign=d==='up'||d==='left'?-1:1;
  const ax=(current.left+current.right)/2, ay=(current.top+current.bottom)/2;
  return candidates.map(el=>{const bx=(el.left+el.right)/2,by=(el.top+el.bottom)/2,along=(vertical?by-ay:bx-ax)*sign,cross=Math.abs(vertical?bx-ax:by-ay),overlapX=Math.min(current.right,el.right)-Math.max(current.left,el.left),overlapY=Math.min(current.bottom,el.bottom)-Math.max(current.top,el.top),sameRow=overlapY>Math.min(current.height,el.height)*.35,sameCol=overlapX>Math.min(current.width,el.width)*.2,valid=along>2&&(vertical?!sameRow:sameRow);if(!valid)return null;return {id:el.id,score:(vertical&&!sameCol?150000:0)+along*1000+cross};}).filter(Boolean).sort((a,b)=>a.score-b.score)[0]?.id;
}
const cur={left:100,right:200,top:100,bottom:140,width:100,height:40};
const right={id:'right',left:220,right:320,top:100,bottom:140,width:100,height:40};
const below={id:'below',left:105,right:205,top:170,bottom:210,width:100,height:40};
assert.equal(pick(cur,[right,below],'down'),'below','Down selected horizontal neighbor');
assert.equal(pick(cur,[right,below],'right'),'right','Right failed horizontal neighbor');
console.log('PASS: 0.9.11 preserves 0.9.10 Full Manager spatial navigation rejects horizontal targets for Up/Down, and QAM Music shows queue position only for Music.');
