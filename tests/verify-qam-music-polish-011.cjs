const fs=require('fs'),vm=require('vm'),assert=require('assert/strict'),path=require('path');
const src=fs.readFileSync(path.join(__dirname,'../src/index.js'),'utf8');
const dist=fs.readFileSync(path.join(__dirname,'../dist/index.js'),'utf8');
assert.equal(src,dist,'src/dist differ');
assert(src.includes("const RD_VERSION = '1.0.0'"),'current frontend version missing');
assert(src.includes('toggleShuffle(force=null)'),'shuffle engine method missing');
assert(src.includes('shuffledMusicQueue(items,currentItem=null)'),'shuffle queue helper missing');
assert(src.includes("s.shuffle?'SHUFFLE · ON':'SHUFFLE · OFF'"),'QAM persistent shuffle toggle missing');
assert(src.includes('rd-v911-music-player rd-v912-music-player'),'Music-only polished player class missing');
assert(src.includes('QamMusicCoverFlowV913'),'current spatial cover-flow component missing');
assert(src.includes('@keyframes rdV914CoverInNext'),'directional cover-flow animation missing');
assert(src.includes('@media(prefers-reduced-motion:reduce)'),'reduced-motion guard missing');
assert(src.includes('rd-v912-primary-controls'),'Music primary transport hierarchy missing');
assert(src.includes('rd-v912-viz'),'Music visualizer polish missing');

const start=src.indexOf('class ResonaAudioEngine {'),end=src.indexOf('\nfunction getAudioEngine()',start);
assert(start>=0&&end>start,'ResonaAudioEngine class not found');
const ctx={console,Date,Math,Map,Set,Promise,setTimeout:()=>0,clearTimeout:()=>{},call:async()=>({}),rdSetGtmAudioFocusV85:()=>{},clamp:(n,a,b)=>Math.max(a,Math.min(b,n)),rdReadMusicModesV912:()=>({shuffle:false,repeatMode:'off'}),rdWriteMusicModesV912:()=>{}};
vm.createContext(ctx);vm.runInContext(src.slice(start,end)+'\nthis.Engine=ResonaAudioEngine;',ctx);
const e=new ctx.Engine();e.trace=()=>{};e.publish=()=>{};
const original=[{ratingKey:'a'},{ratingKey:'b'},{ratingKey:'c'},{ratingKey:'d'}];
e.kind='music';e.queue=[...original];e.unshuffledQueue=[...original];e.index=1;e.current=e.queue[1];
assert.equal(e.toggleShuffle(true),true,'shuffle did not enable');
assert.equal(e.shuffle,true);assert.equal(e.current.ratingKey,'b','current item changed when shuffle enabled');assert.equal(e.queue[e.index].ratingKey,'b','current item not active after shuffle');
assert.deepEqual(new Set(e.queue.map(x=>x.ratingKey)),new Set(original.map(x=>x.ratingKey)),'shuffle changed queue membership');
assert.equal(e.toggleShuffle(false),false,'shuffle did not disable');
assert.deepEqual(Array.from(e.queue,x=>x.ratingKey),original.map(x=>x.ratingKey),'unshuffle did not restore semantic order');assert.equal(e.index,1,'unshuffle did not restore current semantic position');
e.kind='podcast';e.shuffle=false;assert.equal(e.toggleShuffle(true),false,'podcast must not enable Music shuffle');

// Natural end behavior remains stop-at-end even when the active Music queue is shuffled.
let stopped=0,loads=[];e.kind='music';e.shuffle=true;e.bookContext=null;e.queue=[{ratingKey:'x'},{ratingKey:'y'}];e.index=1;e.stop=async()=>{stopped++};e.loadIndex=async i=>{loads.push(i);e.index=i};
(async()=>{await e.advance(1,true);assert.equal(stopped,1,'shuffled queue repeated at natural end');assert.equal(loads.length,0);console.log('PASS: 0.9.12 preserves 0.9.11 Music shuffle semantics and natural stop behavior while the new two-cover flow hooks are present.');})().catch(err=>{console.error(err);process.exit(1)});
