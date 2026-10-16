const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const src=fs.readFileSync('src/index.js','utf8');
const a=src.indexOf('  cancelCrossfadeV11(){'),b=src.indexOf('  applyBoost(){',a);assert(a>0&&b>a);
const methods=src.slice(a,b);let clock=1000,intervals=new Map(),intervalId=0;
const context={Date:class extends Date{static now(){return clock;}},Math,Number,Boolean,String,Set,Map,console,clamp:(n,low,high)=>Math.max(low,Math.min(high,n)),RD_DISCOVERY_V11:{state:{preferences:{crossfade:10}}},setInterval(fn){const id=++intervalId;intervals.set(id,fn);return id;},clearInterval(id){intervals.delete(id);}};
vm.createContext(context);vm.runInContext(`class Harness {${methods}};this.Harness=Harness;`,context);
async function tick(n=1){for(let i=0;i<n;i++)await Promise.resolve();}
const old=()=>({paused:false,ended:false,duration:120,currentTime:109,volume:.8,events:[],pause(){this.paused=true;},removeAttribute(){this.src='';},load(){}});
const engine=()=>{const e=new context.Harness();Object.assign(e,{audio:old(),preferences:{playerVolume:.8},queue:[{ratingKey:'A',libraryRole:'music'},{ratingKey:'B',libraryRole:'music'}],index:0,kind:'music',bookContext:null,repeatMode:'off',snapshot:{state:'playing'},current:{ratingKey:'A'},crossfadeGhost:null,crossfadeBusy:false,crossfadePending:false,crossfadeBlend:0,crossfadeSerial:0,crossfadeTimer:null,cancelLog:[],trace:(...args)=>{},publish(){},generation:0,async loadIndex(index,autoplay){assert.equal(index,1);assert.equal(autoplay,true);this.index=index;this.current=this.queue[index];this.audio={paused:false,volume:0};this.snapshot.state='playing';}});return e;};
(async()=>{
 const e=engine(),ghost=e.audio;e.maybeCrossfadeV11(ghost);await tick(7);
 assert(e.crossfadeGhost===ghost,'old track must remain playing in independent ghost');assert(e.audio!==ghost,'second HTML audio must replace active primary');assert.equal(e.audio.volume,0,'new track must start silent');assert.equal(intervals.size,1);
 clock+=5000;for(const fn of intervals.values())fn();assert(e.audio.volume>0.55&&e.audio.volume<0.6,'incoming at equal-power midpoint');assert(ghost.volume>0.55&&ghost.volume<0.6,'outgoing at equal-power midpoint');
 clock+=5000;for(const fn of [...intervals.values()])fn();assert.equal(e.audio.volume,.8,'new music should reach saved volume');assert(ghost.paused,'old track must release');assert.equal(intervals.size,0,'crossfade timer cleanup');
 const off=engine();context.RD_DISCOVERY_V11.state.preferences.crossfade=0;off.maybeCrossfadeV11(off.audio);assert.equal(off.crossfadeBusy,false,'crossfade must default off');
 context.RD_DISCOVERY_V11.state.preferences.crossfade=10;const book=engine();book.kind='audiobook';book.maybeCrossfadeV11(book.audio);assert.equal(book.crossfadeBusy,false,'never overlap audiobook speech');
 const repeat=engine();repeat.repeatMode='one';repeat.maybeCrossfadeV11(repeat.audio);assert.equal(repeat.crossfadeBusy,false,'repeat-one must not fade to next track');
 const bad=engine();bad.loadIndex=async()=>{throw new Error('Plex unavailable')};const original=bad.audio;bad.maybeCrossfadeV11(original);await tick(8);assert.equal(bad.audio,original,'failed stream must restore original player');assert.equal(bad.crossfadeBusy,false,'failed stream unlocks crossfade');assert.equal(bad.snapshot.state,'playing','failed stream keeps outgoing song active');
 const stop=engine();stop.crossfadeGhost=old();stop.crossfadeTimer=context.setInterval(()=>{});stop.cancelCrossfadeV11();assert(stop.crossfadeGhost===null&&stop.crossfadeTimer===null&&stop.audio.volume===.8,'Stop should clean both audio streams');
 console.log('PASS: real dual-element equal-power crossfade at 10 seconds; Off/book/repeat gates; Plex failure fallback; Stop cleanup');
})().catch(e=>{console.error(e);process.exit(1)});
