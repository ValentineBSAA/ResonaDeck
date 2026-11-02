'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const src=fs.readFileSync(path.join(__dirname,'../dist/index.js'),'utf8');
const a=src.indexOf('const RD134_VIS_KEY='),b=src.indexOf('// END 1.3.4 GTM VISUALIZER BRIDGE.',a);
assert(a>0&&b>a);const bridgeCode=src.slice(a,b);
function fixture(options={}){
 const events=[],packets=[],calls=[];let now=5000, level=options.level??100, nextTimer=0;
 const timers=new Map(),storage=new Map();
 const DateClock=class extends Date{static now(){return now}};
 const host={location:{origin:'http://localhost'},window:null,document:{addEventListener(){},removeEventListener(){}},
 localStorage:{getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,v)},
 GameThemeMusicVisualizerBridgeV1:{version:1,publishExternalTelemetry(pkt){packets.push(pkt);return true},stopExternalTelemetry(){packets.push({active:false});return true}},
 CustomEvent:class{constructor(type){this.type=type}},dispatchEvent(e){events.push(e.type)},postMessage(){},
 addEventListener(){},removeEventListener(){},
 AudioContext:class {constructor(){this.state='running';this.sampleRate=48000;this.destination={name:'SPEAKERS'};calls.push('context')}
 createAnalyser(){calls.push('analyser');return {frequencyBinCount:1024,getByteFrequencyData(buf){buf.fill(level)},disconnect(){calls.push('disconnect-analyser')}}}
 createMediaStreamTrackSource(){return {connect(x){calls.push('capture-to-'+(x?.name||'analyser'))},disconnect(){calls.push('disconnect-capture')}}}
 createMediaElementSource(){calls.push('media-source');return {connect(x){calls.push('media-to-'+(x?.name||'analyser'))},disconnect(x){calls.push('disconnect-media-'+(x?.name||'analyser'))}}}
 close(){calls.push('context-closed');return Promise.resolve()}}
 };host.window=host;
 const audio={volume:.75,paused:false,muted:false,crossOrigin:options.crossOrigin||null,src:'http://127.0.0.1:19400/media/SECRET/sid'};
 if(options.capture==='tracks')audio.captureStream=()=>({getAudioTracks:()=>[{readyState:'live',muted:false}]});
 if(options.capture==='zero')audio.captureStream=()=>({getAudioTracks:()=>[]});
 if(options.capture==='muted')audio.captureStream=()=>({getAudioTracks:()=>[{readyState:'live',muted:true}]});
 const engine={kind:'music',bookContext:null,snapshot:{state:'playing'},audio,crossfadeGhost:null};
 const context={window:host,globalThis:host,rdGtmHostsV84:()=>[host],runtimeHost:()=>host,audioEngine:engine,Date:DateClock,Math,Uint8Array,
 setInterval:(cb,ms)=>{const id=++nextTimer;timers.set(id,cb);return id},clearInterval:(id)=>timers.delete(id),console};
 vm.createContext(context);vm.runInContext(bridgeCode+'\nthis.api=rdV134VisualBridge;',context);
 const tick=(n=1)=>{for(let i=0;i<n;i++){now+=180;for(const cb of timers.values())cb()}};
 return {api:context.api,audio,engine,host,packets,calls,events,tick,setLevel(v){level=v}};
}
// Previously hidden cause: WebAudio running yet no audio track. It must reveal
// the issue and not claim it sent real PCM.
let t=fixture({capture:'zero'});t.tick(6);
assert.match(t.api.getStatus().captureStage,/zero tracks/i);
assert.equal(t.api.getStatus().captureTracks,0);assert.equal(t.api.getStatus().signalRecent,false);
assert.equal(t.calls.includes('media-source'),false,'fallback must not silently reroute output');
t.api.destroy();
// A muted audio track must be reported distinctly rather than masked by a
// generic 'waiting for PCM' status.
t=fixture({capture:'muted'});t.tick(4);
assert.equal(t.api.getStatus().captureMuted,true);
assert.match(t.api.getStatus().captureStage,/muted/i);t.api.destroy();
// User opted into fallback, but current track predates CORS: leave it audible
// and ask for next song instead of creating a risky cross-origin source.
t=fixture({capture:'zero'});t.api.allowFallback();t.tick(5);
assert.match(t.api.getStatus().captureStage,/next song/i);
assert.equal(t.calls.includes('media-source'),false);t.api.destroy();
// Future CORS-enabled local proxy streams can use media element source.
t=fixture({capture:'zero',crossOrigin:'anonymous'});t.api.allowFallback();t.tick(5);
assert.equal(t.api.getStatus().signalRecent,true,'receives nonzero measured audio bands');
assert.equal(t.api.getStatus().captureMode,'media-element');
assert(t.packets.some(x=>x.active&&x.bands.length===12&&x.rms>.01));
assert(t.calls.indexOf('media-to-SPEAKERS')>=0,'output must be connected');
assert(t.calls.indexOf('media-to-SPEAKERS')<t.calls.indexOf('media-to-analyser'),'output route is built before tapping');
assert.equal(t.audio.volume,.75,'does not overwrite original player volume');
const previous=t.packets.length;
t.engine.audio.paused=true;t.engine.snapshot.state='paused';t.tick();
assert(t.packets.slice(previous).some(x=>x.active===false),'pause clears GTM data');
assert.equal(t.calls.includes('disconnect-media-SPEAKERS'),false,'never disconnect speaker output');
t.api.destroy();assert.equal(t.calls.includes('context-closed'),false,'cannot close a context used for audio output');
// The passive method stays preferred and does not connect to speakers.
t=fixture({capture:'tracks',crossOrigin:'anonymous'});t.tick(5);
assert.equal(t.api.getStatus().captureMode,'captureStream');
assert.equal(t.calls.includes('media-to-SPEAKERS'),false);assert.equal(t.api.getStatus().signalRecent,true);t.api.destroy();
// Silent stream capture must eventually give up and switch to opted-in fallback.
t=fixture({capture:'tracks',crossOrigin:'anonymous',level:0});t.api.allowFallback();t.tick(18);
assert.equal(t.api.getStatus().captureMode,'media-element');
assert.equal(t.api.getStatus().signalRecent,false,'never fabricate PCM during silence');
t.setLevel(120);t.tick(4);
assert.equal(t.api.getStatus().signalRecent,true);
t.api.destroy();
// metadata & opt-in settings must be accurately versioned.
const pkg=JSON.parse(fs.readFileSync(path.join(__dirname,'../package.json'),'utf8'));
const plugin=JSON.parse(fs.readFileSync(path.join(__dirname,'../plugin.json'),'utf8'));
assert.equal(pkg.version,'1.4.1');assert.equal(plugin.version,'1.4.1');
assert(src.includes("const RD_VERSION = '1.4.1';"));
assert(src.includes("this.kind==='music'&&rdV134CorsOptedIn()&&a.crossOrigin!=='anonymous'"),'future transport gets CORS enabled');
// New 1.3.5 track metadata: anonymous counter changes once per logical song.
t=fixture({capture:'zero',crossOrigin:'anonymous'});
t.api.allowFallback();t.engine.playSessionId='local-private-song-a';t.tick(5);
let musicPackets=t.packets.filter(p=>p.active&&p.trackSequence>0);
assert(musicPackets.length>0,'new PCM packets include a numeric track counter');
assert.equal(musicPackets.at(-1).trackSequence,1);
assert.equal(typeof musicPackets.at(-1).bridgeSession,'number');
assert(!Object.keys(musicPackets.at(-1)).some(k=>['ratingKey','title','url','artist','trackId'].includes(k)));
t.tick(10);assert.equal(t.packets.filter(p=>p.active).at(-1).trackSequence,1,'no extra increments for PCM ticks');
t.engine.playSessionId='local-private-song-b';t.tick(4);
assert.equal(t.packets.filter(p=>p.active).at(-1).trackSequence,2,'song changed once');
assert.equal(t.api.getStatus().trackChanges,1);
t.engine.snapshot.state='paused';t.engine.audio.paused=true;t.tick();
t.engine.snapshot.state='playing';t.engine.audio.paused=false;t.tick(3);
assert.equal(t.packets.filter(p=>p.active).at(-1).trackSequence,2,'resume is not a song change');
t.api.destroy();
console.log('PASS ResonaDeck 1.3.5: diagnostic reasons, safe opt-in, captureStream priority, fallback output preservation, measured PCM, silent audio, pause, version');
