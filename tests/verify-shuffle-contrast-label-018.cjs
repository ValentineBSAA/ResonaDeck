const fs=require('fs'),assert=require('assert/strict'),path=require('path');
const src=fs.readFileSync(path.join(__dirname,'../src/index.js'),'utf8');
const dist=fs.readFileSync(path.join(__dirname,'../dist/index.js'),'utf8');
assert.equal(src,dist,'src/dist differ');
assert(src.includes("const RD_VERSION = '1.0.0'"),'current frontend version missing');
for(const token of [
  "s.shuffle?'SHUFFLE · ON':'SHUFFLE · OFF'",
  '.rd-v912-secondary-controls .rd-v913-shuffle{position:relative;overflow:visible!important;color:var(--rd-muted)!important',
  '.rd-v913-shuffle.active{z-index:3;color:var(--rd-text)!important',
  '.rd-v913-shuffle.gpfocus,.rd-root.rd-v7-qam .rd-v913-shuffle:focus-visible{color:var(--rd-text)!important',
  'var(--rd-accent)','@keyframes rdV922ShuffleTrace',
  'translate3d(114px,0,-150px)','left:28px!important;top:12px!important',"'REPEAT · OFF'"
]) assert(src.includes(token),`missing native Shuffle contrast hook: ${token}`);
assert(!src.includes('rd-v921-shuffle-label'),'custom sibling Shuffle label must be removed');
assert(!src.includes('rd-v921-shuffle-wrap'),'custom Shuffle wrapper must be removed');
assert(!src.includes('color:transparent!important;text-shadow:none!important}.rd-root.rd-v7-qam .rd-v921'),'transparent button-text hack must be removed');
assert(!src.includes('conic-gradient(from 0deg'),'tracer must not be circular');
console.log('PASS: Shuffle OFF/ON now uses raw Decky button text with readable theme colors and no independent text layer.');
