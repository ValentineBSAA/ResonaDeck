'use strict';
const fs=require('fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const src=fs.readFileSync('src/index.js','utf8');
assert.equal(src,fs.readFileSync('dist/index.js','utf8'));
assert(src.includes("const RD_VERSION = '1.1.4'"));
const read=(a,b)=>{const i=src.indexOf(a),j=src.indexOf(b,i+1);assert(i>=0&&j>i,a);return src.slice(i,j)};
assert(src.includes('onSecondaryButton:toggleDiscoverySettings'),'X art opens settings');
assert(src.includes('onClick:toggleDiscoverySettings'),'A art opens settings');
assert(src.includes('onSecondaryButton:onToggle,onOptionsButton:onToggle'),'X closes settings from selected options');
assert(src.includes('settingsStateRef.current){closeDiscoverySettings();return;}'),'art toggle closes open settings');
assert(src.includes('showFavorites?h(DiscoveryLibraryV11,{compact:true,onXClose:onToggle||onClose}):null'),'favorites X close');
assert(src.includes('onSecondaryButton:onXClose,onOptionsButton:onXClose'),'favorite actions allow X close');
assert(src.includes('rdQamFocusV7(e,\'[data-rd-qam-stop="1"]\')'),'art routes right to Stop');
assert(src.includes('left:\'[data-rd-qam-surprise-art="1"]\''),'Stop routes left to art');
const css=src.slice(src.indexOf('/* 1.1.4: square real/fallback music artwork'),src.indexOf('/* 1.1.4: square real/fallback music artwork')+1700);
assert(css.includes('aspect-ratio:1/1!important'),'square artwork');
assert(css.includes('object-fit:cover!important'),'fallback and Plex crop to fill');
assert(!css.includes('.rd-v105-turntable{'),'no modification of idle turntable');

let clock=100000,network=0,ids=0;
const intervals=new Map();
class FakeAudio {
 constructor(){this.paused=true;this.ended=false;this.readyState=2;this.volume=1;this.src='';this.loadCount=0;}
 load(){this.loadCount++;}pause(){this.paused=true;}removeAttribute(k){if(k==='src')this.src='';}
 getAttribute(k){if(k==='src')return this.src;return null;}
}
const context={Date:class extends Date{static now(){return clock;}},Math,Number,Boolean,String,Set,Map,Promise,console,Audio:FakeAudio,
 RD_AUDIO_CAPS_V6:{},rdSurpriseDurationCompleteV111:()=>false,RD_DISCOVERY_V11:{state:{preferences:{crossfade:10}}},clamp:(v,min,max)=>Math.max(min,Math.min(max,v)),
 setInterval(fn){intervals.set(++ids,fn);return ids;},clearInterval(n){intervals.delete(n);},
 call:async(method,id)=>{assert.equal(method,'get_stream_url');network++;return {success:true,url:'https://plex.local/music/'+id,directPlay:true,expiresAt:clock/1000+120};}};
vm.createContext(context);
const methods=read('  disposeCrossfadeWarmV114(){','  applyBoost(){')+read('  async transportPlan(','  async applyTransport(');
vm.runInContext(`class Harness{${methods}}this.Harness=Harness;`,context);
const old=()=>({paused:false,ended:false,duration:120,currentTime:80,volume:.8,pause(){this.paused=true},removeAttribute(){},load(){}});
const wait=async(n=12)=>{for(let i=0;i<n;i++)await Promise.resolve();};
function engine(){const e=new context.Harness();Object.assign(e,{
 audio:old(),queue:[{ratingKey:'A',libraryRole:'music'},{ratingKey:'B',libraryRole:'music'}],current:{ratingKey:'A'},index:0,kind:'music',
 bookContext:null,repeatMode:'off',crossfadeWarmV114:null,crossfadeGhost:null,crossfadeTimer:null,crossfadeBusy:false,crossfadePending:false,crossfadeSerial:0,crossfadeBlend:0,
 snapshot:{state:'playing'},preferences:{playerVolume:.8,preferDirectPlay:true},generation:0,preparedPlans:new Map(),
 trace(){},publish(){},queueItemKey(item){return String(item?.ratingKey||'');},
 async loadIndex(target,autoplay,startAt,options){assert.equal(target,1);assert.equal(autoplay,true);assert(options.crossfadePreparedV114?.audio instanceof FakeAudio);
   this.generation++;this.index=target;this.current=this.queue[target];this.audio=options.crossfadePreparedV114.audio;
   this.audio.paused=false;this.snapshot.state='playing';}
 });return e;}
(async()=>{
 const e=engine(),ghost=e.audio;
 e.maybeCrossfadeV11(ghost);await wait();
 assert.equal(network,1,'Plex plan starts early while 40 seconds remain');
 assert.equal(e.crossfadeWarmV114?.state,'ready','incoming audio is preloaded');
 const warm=e.crossfadeWarmV114.audio;
 assert.notEqual(warm,ghost,'two independent audio elements');
 assert.equal(warm.volume,0,'preloader must be silent');assert.equal(warm.loadCount,1,'preloader started buffering');
 ghost.currentTime=109.5;e.maybeCrossfadeV11(ghost);await wait();
 assert.equal(network,1,'prepared stream reused without late second Plex request');
 assert.equal(e.audio,warm,'player takes ownership of ready second audio');
 assert.equal(e.crossfadeGhost,ghost,'old audio continues underneath');
 assert.equal(intervals.size,1);
 clock+=5000;for(const fn of [...intervals.values()])fn();
 assert(e.audio.volume>.55&&e.audio.volume<.61);
 assert(ghost.volume>.55&&ghost.volume<.61);
 clock+=6000;for(const fn of [...intervals.values()])fn();
 assert(ghost.paused,'old track released after fade');
 assert.equal(intervals.size,0);assert.equal(e.audio.volume,.8);
 const off=engine();context.RD_DISCOVERY_V11.state.preferences.crossfade=0;off.maybeCrossfadeV11(off.audio);assert.equal(off.crossfadeBusy,false);
 context.RD_DISCOVERY_V11.state.preferences.crossfade=10;
 const book=engine();book.kind='audiobook';book.maybeCrossfadeV11(book.audio);assert.equal(book.crossfadeWarmV114,null);
 const repeat=engine();repeat.repeatMode='one';repeat.maybeCrossfadeV11(repeat.audio);assert.equal(repeat.crossfadeWarmV114,null);
 const stopped=engine();stopped.crossfadeWarmV114={audio:new FakeAudio()};stopped.crossfadeGhost=old();stopped.crossfadeTimer=context.setInterval(()=>{});
 stopped.cancelCrossfadeV11();assert.equal(stopped.crossfadeWarmV114,null);assert.equal(stopped.crossfadeGhost,null);assert.equal(stopped.crossfadeTimer,null);assert.equal(stopped.audio.volume,.8);
 console.log('PASS: X/settings hooks, square fallback/covers, unchanged idle turntable, early muted second-stream preload, 10s equal-power fade, Off/book/repeat gates, cleanup');
})().catch(e=>{console.error(e);process.exit(1)});
