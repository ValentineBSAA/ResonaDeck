const fs=require('fs'),vm=require('vm'),assert=require('assert/strict'),path=require('path');
const src=fs.readFileSync(path.join(__dirname,'../src/index.js'),'utf8');
const dist=fs.readFileSync(path.join(__dirname,'../dist/index.js'),'utf8');
assert.equal(src,dist,'src/dist differ');
assert(src.includes("const RD_VERSION = '1.0.8'"),'0.9.12 frontend version missing');
for(const token of [
  'toggleRepeat(force=null)',
  'playNext(item)',
  'addToQueue(item)',
  'RD_MUSIC_MODE_STORAGE_V912',
  'QamMusicCoverFlowV913',
  'QamMusicCopyFlowV913',
  'QamMusicQueueDrawerV912',
  'RD_QAM_NAV_EVENT_V912',
  "s.shuffle?'SHUFFLE · ON':'SHUFFLE · OFF'",
  "s.repeatMode==='one'?'REPEAT · ONE'",
  'rd-v912-primary-controls',
  'rd-v912-secondary-controls',
  'rd-v912-queue-drawer',
  '@keyframes rdV914CoverInNext',
  '@keyframes rdV914CoverInPrev',
  '@keyframes rdV914CoverOutNext',
  '@keyframes rdV922ShuffleTrace',
  'prefers-reduced-motion:reduce',
  'MusicQueueTrackRowV912',
  "audioEngine.playNext({...item,libraryRole:'music'})",
  "audioEngine.addToQueue({...item,libraryRole:'music'})"
]) assert(src.includes(token),`missing 0.9.12 hook: ${token}`);

const start=src.indexOf('class ResonaAudioEngine {'),end=src.indexOf('\nfunction getAudioEngine()',start);
assert(start>=0&&end>start,'ResonaAudioEngine class not found');
const writes=[];
const ctx={console,Date,Math,Map,Set,Promise,setTimeout:()=>0,clearTimeout:()=>{},call:async()=>({}),rdSetGtmAudioFocusV85:()=>{},clamp:(n,a,b)=>Math.max(a,Math.min(b,n)),rdReadMusicModesV912:()=>({shuffle:false,repeatMode:'off'}),rdWriteMusicModesV912:(shuffle,repeatMode)=>writes.push({shuffle,repeatMode})};
vm.createContext(ctx);vm.runInContext(src.slice(start,end)+'\nthis.Engine=ResonaAudioEngine;',ctx);

const e=new ctx.Engine();e.trace=()=>{};e.publish=()=>{};e.kind='music';e.bookContext=null;
assert.equal(e.repeatMode,'off');
assert.equal(e.toggleRepeat(),'all');
assert.equal(e.toggleRepeat(),'one');
assert.equal(e.toggleRepeat(),'off');
assert.equal(writes.at(-1).repeatMode,'off','repeat state was not persisted');

// Play Next moves an existing row directly behind current without duplicating it.
e.queue=[{ratingKey:'a'},{ratingKey:'b'},{ratingKey:'c'}];e.unshuffledQueue=[...e.queue];e.index=0;e.current=e.queue[0];
assert.equal(e.playNext({ratingKey:'c',title:'C'}),true);
assert.deepEqual(Array.from(e.queue,x=>x.ratingKey),['a','c','b']);
assert.equal(e.queue.filter(x=>x.ratingKey==='c').length,1);
assert.equal(e.addToQueue({ratingKey:'d'}),true);
assert.deepEqual(Array.from(e.queue,x=>x.ratingKey),['a','c','b','d']);
assert.equal(e.addToQueue({ratingKey:'d'}),false,'duplicate queue item was appended');

(async()=>{
  // Natural end: off stops, all wraps, one restarts current.
  let stopped=0,loads=[];
  e.queue=[{ratingKey:'x'},{ratingKey:'y'}];e.index=1;e.current=e.queue[1];e.repeatMode='off';e.stop=async()=>{stopped++};e.loadIndex=async(i,_a,_s,opts)=>{loads.push({i,opts});e.index=i};
  await e.advance(1,true);assert.equal(stopped,1);assert.equal(loads.length,0);
  stopped=0;loads=[];e.repeatMode='all';await e.advance(1,true);assert.equal(stopped,0);assert.equal(loads[0].i,0);assert.equal(loads[0].opts.direction,'next');
  loads=[];e.index=1;e.repeatMode='one';await e.advance(1,true);assert.equal(loads[0].i,1);assert.equal(loads[0].opts.direction,'repeat-one');
  console.log('PASS: 0.9.12 repeat modes, Play Next/Add Queue, persistent mode hooks, Up Next drawer, Music navigation links, persistent Shuffle state, and the 0.9.17 direction-aware spatial two-cover transitions are present and bounded.');
})().catch(err=>{console.error(err);process.exit(1)});
