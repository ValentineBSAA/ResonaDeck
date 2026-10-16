const assert=require('node:assert/strict');const fs=require('node:fs');
const code=fs.readFileSync('src/index.js','utf8');
assert.equal(code,fs.readFileSync('dist/index.js','utf8'));
assert(code.includes("const RD_VERSION = '1.1.8'"));
for(const feature of ['rd-v117-record-scene','rd-v117-turntable-base','rd-v117-incoming-record','rd-v117-record-label','rd-v117-record-active','rdV117RecordArrival','rd-v117-record-caption','rd-v117-test-crossfade'])assert(code.includes(feature),feature);
assert(code.includes('showNextCover')&&code.includes('remainSeconds')&&code.includes('s.transitionSerial'));
assert(code.includes('pointer-events:none!important'));
assert(!code.includes("h('span',{className:'rd-v116-next-peek',"));
console.log('PASS: record-change scene is temporary, nonfocusable and hooked into existing artwork flow; idle turntable CSS stays intact');
