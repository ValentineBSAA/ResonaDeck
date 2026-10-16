'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const src=fs.readFileSync('src/index.js','utf8');
assert.equal(src,fs.readFileSync('dist/index.js','utf8'));
assert(src.includes("const RD_VERSION = '1.1.5'"));
assert(src.includes("MUSIC CROSSFADE · TWO PLAYERS (SECONDS)"));
assert(src.includes("rd-v115-crossfade-health"));
assert(src.includes("this.crossfadeTrackDurationV115(ghost,before.current)"));
assert(src.includes('onSecondaryButton:toggleDiscoverySettings'));
const read=(a,b)=>{const i=src.indexOf(a),j=src.indexOf(b,i+1);assert(i>=0&&j>i,a);return src.slice(i,j)};
let now=100000,requests=[],ids=0;const intervals=new Map(),timers=new Map();
class MockAudio {
 constructor(){this.src='';this.readyState=0;this.volume=1;this.paused=true;this.ended=false;this.currentTime=0;this.duration=Infinity;this.events=new Map();this.loadCalls=0;MockAudio.all.push(this);}
 addEventListener(e,fn){if(!this.events.has(e))this.events.set(e,new Set());this.events.get(e).add(fn)}
 removeEventListener(e,fn){this.events.get(e)?.delete(fn)}
 emit(e){for(const fn of [...(this.events.get(e)||[])])fn()}
 load(){this.loadCalls++;this.readyState=0}
 makeReady(){this.readyState=3;this.emit('loadeddata');this.emit('canplay')}
 pause(){this.paused=true}
 async play(){if(this.failPlay)throw Object.assign(new Error('Autoplay denied'),{name:'NotAllowedError'});this.paused=false}
 getAttribute(key){return key==='src'?this.src:null}
 removeAttribute(key){if(key==='src')this.src=''}
}
MockAudio.all=[];
const context={Math,Promise,String,Number,Boolean,Error,console,Map,Set,Audio:MockAudio,
 Date:class extends Date{static now(){return now}},clamp:(n,lo,hi)=>Math.min(hi,Math.max(lo,n)),
 RD_DISCOVERY_V11:{state:{preferences:{crossfade:8}}},rdSurpriseDurationCompleteV111:()=>false,
 setInterval(fn){intervals.set(++ids,fn);return ids},clearInterval(id){intervals.delete(id)},
 setTimeout(fn){timers.set(++ids,fn);return ids},clearTimeout(id){timers.delete(id)},
 call:async()=>null};
vm.createContext(context);
const crossfade=read('  // Crossfade health is intentionally shown in settings','  applyBoost(){');
const apply=read('  async applyTransport(','  async loadIndex(');
vm.runInContext(`class Harness{${crossfade}${apply}}this.Harness=Harness`,context);
const flush=async()=>{for(let i=0;i<12;i++)await Promise.resolve()};
function engine(){
 const e=new context.Harness(),old=new MockAudio();old.paused=false;old.currentTime=65;old.duration=Infinity;old.volume=.9;
 Object.assign(e,{audio:old,queue:[{ratingKey:'old',libraryRole:'music',duration:120000},{ratingKey:'new',libraryRole:'music',duration:130000}],index:0,current:{ratingKey:'old',libraryRole:'music',duration:120000},kind:'music',
 bookContext:null,repeatMode:'off',crossfadeWarmV114:null,crossfadeGhost:null,crossfadeBusy:false,crossfadePending:false,crossfadeSerial:0,crossfadeBlend:0,generation:1,
 preferences:{playerVolume:.9,preferDirectPlay:true},snapshot:{state:'playing',duration:120,volume:.9},crossfadeHealthV115:{phase:'off',detail:''},traceLog:[],
 trace(name,payload){this.traceLog.push({name,payload})},publish(obj={}){Object.assign(this.snapshot,obj)},queueItemKey(x){return x?.ratingKey||''},
 clearStartupFallback(){},clearSeekFallback(){},armStartupFallback(){},
 ensureAudio(warm){if(this.audio)return this.audio;this.audio=warm||new MockAudio();this.audio.volume=this.crossfadePending?0:.9;return this.audio},
 async play(){await this.audio.play();this.snapshot.state='playing'},
 async loadIndex(target,autoplay,startAt,opts){assert.equal(target,1);assert.equal(autoplay,true);assert(opts.crossfadePreparedV114?.audio instanceof MockAudio);this.generation++;this.index=target;this.current=this.queue[target];this.snapshot.state='loading';this.crossfadeIncomingAudioV114=opts.crossfadePreparedV114.audio;await this.applyTransport(opts.crossfadePreparedV114.stream,0,true)}
 });
 e.transportPlan=async(item,force)=>{requests.push({item:item.ratingKey,force});return {success:true,url:'https://plex.invalid/'+item.ratingKey+(force?'/mp3':''),selected:force?'mp3':'direct',directPlay:!force,transcoded:force}};
 return {e,old};
}
(async()=>{
 const {e,old}=engine();
 e.maybeCrossfadeV11(old);
 assert.equal(requests.length,1,'should prewarm 55 seconds before end even when native duration is Infinity');
 await flush();
 assert.equal(e.crossfadeWarmV114?.state,'loading','Plex URL alone MUST NOT mean ready');
 assert.equal(e.crossfadeHealthV115.phase,'preparing');
 const next=e.crossfadeWarmV114.audio;assert(next&&next!==old,'create two independent audio players');assert.equal(next.volume,0);
 old.currentTime=110;e.maybeCrossfadeV11(old);assert.equal(e.crossfadeBusy,false,'do not crossfade into an unbuffered player');
 next.makeReady();await flush();
 assert.equal(e.crossfadeWarmV114,null,'prepared audio transfers ownership');
 assert.equal(e.audio,next,'prepared next stream becomes the active audio');
 assert.equal(e.crossfadeGhost,old,'old stream remains playing during overlap');
 assert.equal(old.paused,false);assert.equal(next.paused,false);
 assert.equal(e.crossfadeHealthV115.phase,'fading');
 assert.equal(requests.length,1,'no second Plex request at the fade boundary');
 assert(e.traceLog.find(x=>x.name==='crossfade-started')?.payload?.twoStreams,'actual engine confirms both audio streams simultaneously active');
 const actual=e.traceLog.find(x=>x.name==='crossfade-started').payload.actual;
 assert(actual>=7.5&&actual<=8,'should get full requested 8-second fade, not near-instant swap');
 now+=4000;for(const fn of [...intervals.values()])fn();
 assert(e.audio.volume>0.5&&e.audio.volume<0.8,'new stream fades in');
 assert(old.volume>0.5&&old.volume<0.8,'old stream fades out');
 now+=4500;for(const fn of [...intervals.values()])fn();
 assert.equal(old.paused,true);assert.equal(e.audio.volume,.9);assert.equal(e.crossfadeHealthV115.phase,'complete');assert.equal(intervals.size,0);

 requests=[];const f=engine();f.e.audio.currentTime=70;f.e.maybeCrossfadeV11(f.old);await flush();
 const warm=f.e.crossfadeWarmV114,oldDirect=warm.audio;oldDirect.emit('error');await flush();
 assert.equal(requests.length,2,'failed direct decode triggers MP3 Plex retry');
 const mp3=f.e.crossfadeWarmV114.audio;assert.notEqual(mp3,oldDirect,'forced MP3 gets a fresh player');
 mp3.makeReady();await flush();assert.equal(f.e.crossfadeWarmV114.state,'ready');
 f.e.cancelCrossfadeV11();assert(mp3.paused,'stop or pause disposes warm audio');


 // Chromium's late autoplay rejection must NOT sacrifice the outgoing song.
 requests=[];const denied=engine();denied.e.maybeCrossfadeV11(denied.old);await flush();
 const blocked=denied.e.crossfadeWarmV114.audio;blocked.failPlay=true;
 denied.old.currentTime=110;blocked.makeReady();await flush();
 assert.equal(denied.e.audio,denied.old,'old song restored after next audio play rejected');
 assert.equal(denied.e.current.ratingKey,'old','track metadata restored after failed handoff');
 assert.equal(denied.old.paused,false,'outgoing song continues normally after failed crossfade');
 assert.equal(denied.e.crossfadeHealthV115.phase,'failed','shows truthful crossfade failure in settings');


 // All exposed durations must actually drive the same two-player path.
 for(const secs of [3,5,10]){
   context.RD_DISCOVERY_V11.state.preferences.crossfade=secs;
   const sample=engine();sample.old.currentTime=68;sample.e.maybeCrossfadeV11(sample.old);await flush();
   const nextAudio=sample.e.crossfadeWarmV114.audio;
   sample.old.currentTime=120-secs-2;nextAudio.makeReady();await flush();
   const started=sample.e.traceLog.find(x=>x.name==='crossfade-started')?.payload;
   assert(started,`fade starts for ${secs}s`);
   assert(Math.abs(started.actual-secs)<0.01,`actual ${secs}s overlap`);
   sample.e.cancelCrossfadeV11();
 }

 context.RD_DISCOVERY_V11.state.preferences.crossfade=0;const disabled=engine().e;disabled.maybeCrossfadeV11(disabled.audio);assert.equal(disabled.crossfadeWarmV114,null);
 context.RD_DISCOVERY_V11.state.preferences.crossfade=8;const book=engine().e;book.kind='audiobook';book.maybeCrossfadeV11(book.audio);assert.equal(book.crossfadeWarmV114,null);
 const repeat=engine().e;repeat.repeatMode='one';repeat.maybeCrossfadeV11(repeat.audio);assert.equal(repeat.crossfadeWarmV114,null);
 console.log('PASS: infinite-duration Plex fallback, 2 buffered streams, full 8s equal-power fade, no early unbuffered start, no duplicate Plex plan, direct-decode-to-MP3 recovery, cleanup, disabled/nonmusic/repeat guards');
})().catch(e=>{console.error(e);process.exitCode=1});
