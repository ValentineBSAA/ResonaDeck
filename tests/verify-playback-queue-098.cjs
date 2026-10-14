const fs=require('fs'),vm=require('vm'),assert=require('assert/strict'),path=require('path');
const src=fs.readFileSync(path.join(__dirname,'../src/index.js'),'utf8');
const start=src.indexOf('class ResonaAudioEngine {'), end=src.indexOf('\nfunction getAudioEngine()',start);
assert(start>=0&&end>start,'ResonaAudioEngine class not found');
const ctx={console,Date,Math,Map,Set,Promise,setTimeout:()=>0,clearTimeout:()=>{},call:async()=>({}),rdSetGtmAudioFocusV85:()=>{},clamp:(n,a,b)=>Math.max(a,Math.min(b,n)),rdReadMusicModesV912:()=>({shuffle:false,repeatMode:'off'}),rdWriteMusicModesV912:()=>{}};
vm.createContext(ctx);vm.runInContext(src.slice(start,end)+'\nthis.Engine=ResonaAudioEngine;',ctx);
const make=()=>{const e=new ctx.Engine();e.trace=()=>{};let stopped=0,loads=[];e.stop=async()=>{stopped++};e.loadIndex=async(i,...rest)=>{loads.push([i,...rest]);e.index=i};return {e,get stopped(){return stopped},loads};};
(async()=>{
  // The hardware regression: one-track Music album must not restart itself on natural ended.
  let t=make();t.e.kind='music';t.e.queue=[{ratingKey:'only'}];t.e.index=0;await t.e.advance(1,true);assert.equal(t.stopped,1);assert.equal(t.loads.length,0);
  // A multi-track album still advances naturally until the final track.
  t=make();t.e.kind='music';t.e.queue=[{ratingKey:'a'},{ratingKey:'b'}];t.e.index=0;await t.e.advance(1,true);assert.equal(t.stopped,0);assert.equal(t.loads[0][0],1);
  await t.e.advance(1,true);assert.equal(t.stopped,1);assert.equal(t.loads.length,1);
  // Repeat Off manual Next at the final track must not wrap back to track 1.
  t=make();t.e.kind='music';t.e.repeatMode='off';t.e.queue=[{ratingKey:'a'},{ratingKey:'b'}];t.e.index=1;t.e.publish=()=>{};await t.e.advance(1,false);assert.equal(t.stopped,0);assert.equal(t.loads.length,0);assert.equal(t.e.index,1);
  // Repeat All remains the only manual wrap mode.
  t.e.repeatMode='all';await t.e.advance(1,false);assert.equal(t.loads[0][0],0);
  console.log('PASS: natural queue end stops one-track/final-track Music, Repeat Off manual boundaries do not wrap, and Repeat All owns wrapping.');
})().catch(e=>{console.error(e);process.exit(1)});
