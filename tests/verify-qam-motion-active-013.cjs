const fs=require('fs'),assert=require('assert/strict'),path=require('path');
const src=fs.readFileSync(path.join(__dirname,'../src/index.js'),'utf8');
const dist=fs.readFileSync(path.join(__dirname,'../dist/index.js'),'utf8');
assert.equal(src,dist,'src/dist differ');
assert(src.includes("const RD_VERSION = '1.0.0'"),'current frontend version missing');
for(const token of [
  'QamMusicCoverFlowV913','QamMusicCopyFlowV913','rd-v913-cover-viewport',
  '@keyframes rdV914CoverInNext','@keyframes rdV914CoverOutNext',
  '@keyframes rdV914CoverInPrev','@keyframes rdV914CoverOutPrev',
  'translate3d(114px,0,-150px)','translate3d(-106px,0,-132px)',
  'rd-v913-copy-in.next','rd-v913-viz-flow','key:music?`viz-${s.transitionSerial}`',
  'rd-v913-mode-control rd-v913-shuffle','rd-v913-mode-control rd-v913-repeat',
  '@keyframes rdV922ShuffleTrace','offset-path:inset(-2px round 11px)','prefers-reduced-motion:reduce'
]) assert(src.includes(token),`missing retained motion/active-state hook: ${token}`);
const shuffleStart=src.indexOf('toggleShuffle(force=null)'),shuffleEnd=src.indexOf('toggleRepeat(force=null)',shuffleStart);
const repeatEnd=src.indexOf('addToQueue(item)',shuffleEnd);
assert(!src.slice(shuffleStart,shuffleEnd).includes('transitionSerial'),'Shuffle must not trigger cover motion');
assert(!src.slice(shuffleEnd,repeatEnd).includes('transitionSerial'),'Repeat must not trigger cover motion');
assert(src.includes("if(nextKey!==previousKey){this.transitionDirection=String(opts?.direction||'replace');this.transitionSerial=Number(this.transitionSerial||0)+1;}"),'track identity must remain the transition trigger');
console.log('PASS: retained Cover Flow/copy/visualizer motion survives with the 0.9.22 native Shuffle tracer and no mode-toggle track animation.');
