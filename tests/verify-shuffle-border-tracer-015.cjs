const fs=require('fs'),assert=require('assert/strict'),path=require('path');
const src=fs.readFileSync(path.join(__dirname,'../src/index.js'),'utf8');
const dist=fs.readFileSync(path.join(__dirname,'../dist/index.js'),'utf8');
assert.equal(src,dist,'src/dist differ');
assert(src.includes("const RD_VERSION = '1.0.8'"),'current frontend version missing');
for(const token of [
  "s.shuffle?'SHUFFLE · ON':'SHUFFLE · OFF'",
  '.rd-v912-secondary-controls .rd-v913-shuffle.active::before{content:',
  '.rd-v912-secondary-controls .rd-v913-shuffle.active::after{content:',
  'offset-path:inset(-2px round 11px)','offset-distance:100%','@keyframes rdV922ShuffleTrace',
  'var(--rd-accent)','@supports not (offset-path:inset(0 round 1px))','prefers-reduced-motion:reduce'
]) assert(src.includes(token),`missing current border tracer hook: ${token}`);
assert(!src.includes('QamShuffleBorderTraceV915'),'legacy SVG tracer component must be removed from the render path');
assert(!src.includes('rd-v915-shuffle-border'),'legacy SVG tracer CSS must be removed');
assert(!src.includes('conic-gradient(from 0deg'),'tracer must not become a circular spinner');
assert(!src.includes('rdV913ShuffleAura'),'old breathing aura must stay removed');
const shuffleStart=src.indexOf('toggleShuffle(force=null)'),shuffleEnd=src.indexOf('toggleRepeat(force=null)',shuffleStart);
assert(!src.slice(shuffleStart,shuffleEnd).includes('transitionSerial'),'Shuffle toggle must not trigger track-change cover motion');
console.log('PASS: 0.9.22 keeps a theme-aware rounded-button perimeter tracer without SVG, conic spin, or breathing.');
