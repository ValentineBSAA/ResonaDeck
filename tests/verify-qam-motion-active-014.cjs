const fs=require('fs'),assert=require('assert/strict'),path=require('path');
const src=fs.readFileSync(path.join(__dirname,'../src/index.js'),'utf8');
const dist=fs.readFileSync(path.join(__dirname,'../dist/index.js'),'utf8');
assert.equal(src,dist,'src/dist differ');
assert(src.includes("const RD_VERSION = '1.0.0'"),'current frontend version missing');
for(const token of ['@keyframes rdV914CoverInNext','@keyframes rdV914CoverOutNext','@keyframes rdV914CoverInPrev','@keyframes rdV914CoverOutPrev','translate3d(114px,0,-150px)','translate3d(-106px,0,-132px)','@keyframes rdV922ShuffleTrace','var(--rd-accent)','prefers-reduced-motion:reduce']) assert(src.includes(token),`missing retained 0.9.14+ visual hook: ${token}`);
assert(!src.includes('rdV913ShuffleAura'),'legacy breathing Shuffle aura must stay removed');
assert(!src.includes('conic-gradient(from 0deg'),'Shuffle must not regress to circular spinner');
console.log('PASS: large mirrored Cover Flow remains while Shuffle uses the current rounded-button tracer.');
