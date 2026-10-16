const fs=require('fs'),assert=require('assert/strict'),path=require('path');
const src=fs.readFileSync(path.join(__dirname,'../src/index.js'),'utf8');
const dist=fs.readFileSync(path.join(__dirname,'../dist/index.js'),'utf8');
assert.equal(src,dist,'src/dist differ');
assert(src.includes("const RD_VERSION = '1.0.8'"),'current frontend version missing');
for(const token of [
  'browser=globalThis.SteamClient?.Browser','browser?.HideCursorUntilMouseEvent?.()',
  "['pointermove','mousemove','pointerdown','mousedown','touchstart']",'idleTimer=win.setTimeout(hide,700)',
  'doc.addEventListener?.(type,arm,{passive:true,capture:true})','doc.removeEventListener?.(type,arm,true)',
  "s.shuffle?'SHUFFLE · ON':'SHUFFLE · OFF'","'REPEAT · OFF'",'translate3d(114px,0,-150px)','left:28px!important;top:12px!important'
]) assert(src.includes(token),`missing Steam browser-native cursor/preservation hook: ${token}`);
assert(!src.includes('SetMousePosition?.('),'coordinate cursor parking must be removed');
assert(!src.includes('rd-v921-qam-cursor-hidden'),'CSS cursor-hiding class must be removed');
const managerStart=src.indexOf('function ManagerV7()'),managerEnd=src.indexOf('function QAMV7()',managerStart),managerBlock=src.slice(managerStart,managerEnd);
assert(!managerBlock.includes('HideCursorUntilMouseEvent'),'Full Manager must not own QAM cursor hiding');
console.log('PASS: QAM now uses Steam browser-native HideCursorUntilMouseEvent and removes failed CSS/coordinate parking.');
