'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const gtmdir=process.argv[2],rddir=process.argv[3];
const gsrc=fs.readFileSync(path.join(gtmdir,'dist/index.js'),'utf8');
const rsrc=fs.readFileSync(path.join(rddir,'dist/index.js'),'utf8');
assert.match(gsrc,/const GTM_VERSION = "4\.1\.2";/);
assert.match(rsrc,/const RD_VERSION = '1\.4\.1';/);
assert.equal(rsrc,fs.readFileSync(path.join(rddir,'src/index.js'),'utf8'));
for(const [p,v] of [[gtmdir,'4.1.2'],[rddir,'1.4.1']]){
 assert.equal(JSON.parse(fs.readFileSync(path.join(p,'package.json'))).version,v);
 assert.equal(JSON.parse(fs.readFileSync(path.join(p,'plugin.json'))).version,v);
 assert(!/private|test/i.test(JSON.parse(fs.readFileSync(path.join(p,'plugin.json'))).description));
}
// Evaluate the *real GTM receiver*, not a simplified mock.
const a=gsrc.indexOf('const GTM404_VISUAL_SHUFFLE =');
const b=gsrc.indexOf('async function gtm404RefreshPacks()',a);
assert(a>0&&b>a);
let now=12000;const events=[],scenes=[],focusCalls=[];
const context={Math,Date,Number,console,performance:{now:()=>now},
 gtm408ReadLiveResonaFocus:()=>({known:true,active:true,session:'resonadeck'}),
 gtm408ExternalOwnsAudio:()=>true,gtm408ReconcileResonaFocus:()=>{},
 gtmResonaDeckFocus:{active:true},setResonaDeckAudioFocus:(...args)=>focusCalls.push(args),
 window:{location:{origin:'http://localhost'},addEventListener(){},dispatchEvent(e){events.push(e.type)},postMessage(){}},
 CustomEvent:class{constructor(type){this.type=type}},
 GTM_V371_MODES:['retro_a','retro_b','off'],GTM_V376_GROUPS:[{id:'retro',modes:['retro_a','retro_b']}],
 snapshot$1:{homeReactiveVisualizerShuffleAll:true,homeReactiveVisualizerEnabled:true,homeReactiveVisualizerMode:'retro_a'},
 settingsLoaded:true,setGlobalSetting:async(k,v)=>{scenes.push(v);context.snapshot$1.homeReactiveVisualizerMode=v},
 gtm404Clamp:(n,min=0,max=1)=>Math.min(max,Math.max(min,Number(n)||0))
};
vm.createContext(context);vm.runInContext(gsrc.slice(a,b)+'\nthis.receiver=gtm405ReceiveExternal;this.external=gtm404External;this.grace=gtm406ExternalVisualGrace;this.ready=gtm404ExternalReady;this.control=gtm410Sharing;',context);
const receiver=context.receiver;
const pcm=(epoch,seq)=>({source:'resonadeck',protocol:1,active:true,bridgeSession:12345,sharingEpoch:epoch,trackSequence:seq,
 bands:Array(12).fill(.4),rms:.4,low:.4,mid:.3,high:.2,beat:.2});
assert.equal(receiver(pcm(1,1)),true);
assert.equal(context.ready(),true);assert.equal(context.grace(),true);
// Simulates actual Quick Access OFF while *Plex still holds audio focus*.
const control=(sharing,epoch)=>({source:'resonadeck',protocol:1,bridgeSession:12345,sharingEpoch:epoch,active:false,sharing});
const before=events.length;
assert.equal(receiver(control('disabled',2)),true);
assert.equal(context.ready(),false);
assert.equal(context.grace(),false,'bypasses 18 second old-PCM footer grace immediately');
assert.equal(context.external.active,false);
assert.equal(focusCalls.length,0,'OFF does not release ResonaDeck audio focus');
assert(events.length>before,'forces an immediate UI update event');
assert.equal(receiver(pcm(1,2)),false,'old in-flight PCM cannot re-enable visuals');
assert.equal(context.grace(),false);
// reordering: duplicate OFF later must not disable newly re-enabled visuals.
assert.equal(receiver(control('enabled',3)),true);
assert.equal(receiver(control('disabled',2)),false);
assert.equal(receiver(pcm(3,2)),true);
assert.equal(context.ready(),true);
assert.equal(context.grace(),true);
assert.equal(context.control.disabled,false);
assert.equal(focusCalls.length,0);
// A natural dropout is still held while Plex audio remains active.
assert.equal(receiver({active:false}),true);
assert.equal(context.grace(),true,'ordinary crossfade dropout preserves grace');
assert.equal(focusCalls.length,0);
// OFF again has no grace.
assert.equal(receiver(control('disabled',4)),true);
assert.equal(context.grace(),false);
assert(gsrc.includes("window.addEventListener('gtm404-external-telemetry-updated',check)"),'footer listens to direct OFF');
assert(gsrc.includes("window.removeEventListener('gtm404-external-telemetry-updated',check)"));
assert(gsrc.includes("const ownVisual=(playing||trackHandoff)&&"));

// Evaluate ResonaDeck's real bridge in a fake browser and connect it directly
// to the GTM receiver above. Its toggle cannot touch the audio element.
const ra=rsrc.indexOf('const RD134_VIS_KEY='),rb=rsrc.indexOf('// END 1.3.4 GTM VISUALIZER BRIDGE.',ra);
assert(ra>0&&rb>ra);
let clock=5000,vol=.7,paused=false,playing=true,nowTimers=0;
const storage=new Map(),pending=[],sent=[];
const C=class extends Date{static now(){return clock}};
const host={window:null,location:{origin:'http://localhost'},document:{addEventListener(){},removeEventListener(){}},
 localStorage:{getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,v)},
 GameThemeMusicVisualizerBridgeV1:{version:1,publishExternalTelemetry:p=>{sent.push(p);return receiver(p)},stopExternalTelemetry:()=>receiver({active:false})},
 addEventListener(){},removeEventListener(){},dispatchEvent(){},
 CustomEvent:class{constructor(type){this.type=type}},postMessage(){},
 setTimeout:(fn,delay)=>{pending.push({fn,at:clock+delay})},
 AudioContext:class{constructor(){this.state='running';this.sampleRate=48000;this.destination={speaker:true}}
 createAnalyser(){return {frequencyBinCount:1024,getByteFrequencyData(b){b.fill(126)},disconnect(){}}}
 createMediaElementSource(){return {connect(){},disconnect(){}}}
 createMediaStreamTrackSource(){return {connect(){},disconnect(){}}}
 }
};host.window=host;
const audio={get volume(){return vol},set volume(v){vol=v},get paused(){return paused},set paused(v){paused=v},muted:false,crossOrigin:'anonymous',src:'http://127.0.0.1/media'};
audio.captureStream=()=>({getAudioTracks:()=>[]});
const eng={kind:'music',bookContext:null,snapshot:{get state(){return playing?'playing':'paused'}},audio,crossfadeGhost:null,playSessionId:'session_A'};
const rcontext={Math,Number,Date:C,Uint8Array,console,globalThis:host,window:host,
 rdGtmHostsV84:()=>[host],runtimeHost:()=>host,audioEngine:eng,
 setInterval:()=>++nowTimers,clearInterval(){},setTimeout:host.setTimeout};
vm.createContext(rcontext);vm.runInContext(rsrc.slice(ra,rb)+'\nthis.bridge=rdV134VisualBridge;this.setEnabled=rdV134SetEnabled;',rcontext);
const bridge=rcontext.bridge;
bridge.allowFallback();bridge.tick();
assert(sent.some(p=>p.active===true),'real PCM is sent');
assert.equal(context.ready(),true,'real PCM reconnected from new bridge session');
const pcmStart=sent.filter(p=>p.active===true).length;
const volumeBefore=audio.volume;
assert.equal(rcontext.setEnabled(false),false);
assert(sent.some(p=>p.sharing==='disabled'&&p.active===false),'OFF has explicit disabling reason');
assert.equal(context.grace(),false,'real toggle OFF closes GTM footer without waiting');
assert.equal(audio.volume,volumeBefore,'visualizer OFF never changes Plex volume');
assert.equal(audio.paused,false,'visualizer OFF never pauses Plex');
clock+=180;bridge.tick();
assert.equal(sent.filter(p=>p.active===true).length,pcmStart,'no more telemetry after OFF');
assert.equal(rcontext.setEnabled(true),true);
assert(sent.some(p=>p.sharing==='enabled'));
bridge.tick();
assert.equal(context.ready(),true,'ON restores active GTM telemetry without pausing song');
const latest=sent.filter(p=>p.active===true).at(-1);
assert.equal(latest.sharingEpoch,bridge.getStatus().sharingEpoch,'PCM epoch matches toggle');
// Delayed OFF retransmits from older epoch must be canceled.
const extra=sent.length;
for(const task of pending)task.fn();
assert(!sent.slice(extra).some(p=>p.sharing==='disabled'));
assert.equal(audio.volume,volumeBefore);
assert.equal(audio.paused,false);
bridge.destroy();
console.log('PASS 1.3.8 + 4.1.0: direct OFF immediate, no 18s grace, audio focus untouched, old packets blocked, ON restores PCM, stale retries canceled, ordinary crossfade dropout protected.');
