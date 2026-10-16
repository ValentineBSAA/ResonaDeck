const fs=require('fs'),vm=require('vm'),assert=require('assert/strict'),path=require('path');
const src=fs.readFileSync(path.join(__dirname,'../src/index.js'),'utf8');
const dist=fs.readFileSync(path.join(__dirname,'../dist/index.js'),'utf8');
assert.equal(src,dist,'src/dist differ');
assert(src.includes("const RD_VERSION = '1.0.8'"),'current frontend version missing');
for(const token of [
  "'REPEAT · OFF'","'REPEAT · ALL'","'REPEAT · ONE'",
  'a.loop=false',
  "music&&this.repeatMode==='all'",
  "fromEnded?'queue-ended':'queue-boundary'",
  "s.shuffle?'SHUFFLE · ON':'SHUFFLE · OFF'",
  '@keyframes rdV922ShuffleTrace',
  'left:28px!important;top:12px!important',
  'translate3d(114px,0,-150px)'
]) assert(src.includes(token),`missing retained Repeat/Shuffle repair hook: ${token}`);
const start=src.indexOf('class ResonaAudioEngine {'),end=src.indexOf('\nfunction getAudioEngine()',start);
assert(start>=0&&end>start,'ResonaAudioEngine class not found');
const writes=[];
const ctx={console,Date,Math,Map,Set,Promise,setTimeout:()=>0,clearTimeout:()=>{},call:async()=>({}),rdSetGtmAudioFocusV85:()=>{},clamp:(n,a,b)=>Math.max(a,Math.min(b,n)),rdReadMusicModesV912:()=>({shuffle:false,repeatMode:'off'}),rdWriteMusicModesV912:(shuffle,repeatMode)=>writes.push({shuffle,repeatMode})};
vm.createContext(ctx);vm.runInContext(src.slice(start,end)+'\nthis.Engine=ResonaAudioEngine;',ctx);
const e=new ctx.Engine();e.trace=()=>{};e.publish=()=>{};e.kind='music';e.bookContext=null;
assert.equal(e.toggleRepeat(),'all');assert.equal(e.toggleRepeat(),'one');assert.equal(e.toggleRepeat(),'off');assert.equal(writes.at(-1).repeatMode,'off');
(async()=>{
  let loads=[],stopped=0;
  e.loadIndex=async(i,_a,_s,opts)=>{loads.push({i,opts});e.index=i};e.stop=async()=>{stopped++};
  e.queue=[{ratingKey:'1'},{ratingKey:'2'},{ratingKey:'3'}];e.index=2;e.current=e.queue[2];
  e.repeatMode='off';loads=[];stopped=0;await e.advance(1,false);assert.equal(loads.length,0,'Repeat Off manual Next wrapped');assert.equal(stopped,0);assert.equal(e.index,2);
  await e.advance(1,true);assert.equal(loads.length,0,'Repeat Off natural end wrapped');assert.equal(stopped,1,'Repeat Off natural end must stop');
  e.index=2;e.current=e.queue[2];e.repeatMode='all';loads=[];stopped=0;await e.advance(1,false);assert.equal(loads[0].i,0,'Repeat All manual Next did not wrap');
  e.index=2;loads=[];await e.advance(1,true);assert.equal(loads[0].i,0,'Repeat All natural end did not wrap');
  e.index=2;e.repeatMode='one';loads=[];await e.advance(1,true);assert.equal(loads[0].i,2,'Repeat One did not restart current');assert.equal(loads[0].opts.direction,'repeat-one');
  loads=[];await e.advance(1,false);assert.equal(loads.length,0,'Repeat One manual boundary must not wrap');
  e.index=0;e.repeatMode='off';loads=[];await e.advance(-1,false);assert.equal(loads.length,0,'Repeat Off manual Previous wrapped');
  e.repeatMode='all';loads=[];await e.advance(-1,false);assert.equal(loads[0].i,2,'Repeat All manual Previous did not wrap');
  console.log('PASS: retained Repeat Off/All/One queue-boundary semantics remain intact and the Shuffle control uses native raw Decky text with the CSS perimeter tracer.');
})().catch(e=>{console.error(e);process.exit(1)});
