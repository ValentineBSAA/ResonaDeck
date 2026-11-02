const fs=require('fs'),vm=require('vm'),assert=require('assert');
const code=fs.readFileSync(require('node:path').join(__dirname,'..','dist','index.js'),'utf8');
const begin=code.indexOf('class ResonaAudioEngine {');const end=code.indexOf('\nfunction getAudioEngine()',begin);
if(begin<0||end<0)throw new Error('engine class markers missing');
const klass=code.slice(begin,end);
let clock=1000,nextTimer=1,timers=new Map(),intervals=new Map();
const engineCtx={console,Math,Promise,Number,Boolean,String,Date:{now:()=>clock},
 rdReadMusicModesV912:()=>({shuffle:false,repeatMode:'off'}),
 rdSetGtmAudioFocusV85:()=>{},RD_DISCOVERY_V11:{},rdV134CorsOptedIn:()=>false,
 clamp:(v,a,b)=>Math.max(a,Math.min(b,Number(v))),
 setTimeout:(fn,ms)=>{const id=nextTimer++;timers.set(id,{fn,at:clock+ms});return id;},
 clearTimeout:(id)=>timers.delete(id),
 setInterval:(fn,ms)=>{const id=nextTimer++;intervals.set(id,{fn,ms});return id;},
 clearInterval:(id)=>intervals.delete(id),
 call:async()=>({success:true,url:'https://example.invalid/audio'}),
};vm.createContext(engineCtx);vm.runInContext(klass+'\nthis.ResonaAudioEngine=ResonaAudioEngine;',engineCtx);
async function advance(ms){clock+=ms;let due=[...timers].filter(([id,t])=>t.at<=clock);for(const [id,t] of due){timers.delete(id);await t.fn();}await Promise.resolve();}
function setup(playing=true){timers.clear();intervals.clear();clock=1000;let plays=0,pauses=0;const e=new engineCtx.ResonaAudioEngine();e.current={ratingKey:'track-123'};e.queue=[e.current];e.index=0;e.desiredAutoplay=playing;e.snapshot.state=playing?'playing':'paused';e.snapshot.position=79;e.preferences.playerVolume=.75;e.preferences.sleepWakeAutoResume=true;e.preferences.sleepWakeDelaySeconds=12;
 const audio={src:'https://example.invalid/play',paused:!playing,volume:.75,currentTime:79,play:async function(){plays++;this.paused=false;},pause:function(){pauses++;this.paused=true;}};
 e.audio=audio;e.cancelCrossfadeV11=()=>{};e.stopCrossfadePulseV116=()=>{};e.clearStartupFallback=()=>{};e.stopReporting=()=>{};e.trace=()=>{};e.publish=()=>{};e.startReporting=()=>{};e.startCrossfadePulseV116=()=>{};return {e,audio,counts:()=>({plays,pauses})};}
(async()=>{
 // Sleep while playing, resume from same audio element/position only AFTER 12 seconds.
 let {e,audio,counts}=setup(true);e.rd140SleepSuspend();assert.equal(audio.paused,true);assert.equal(e.rd140Sleep.intent,true);assert.equal(e.desiredAutoplay,true);e.rd140SleepWake();assert.equal(e.rd140SleepBlocked(),true);await advance(11999);assert.equal(counts().plays,0);await advance(1);assert.equal(counts().plays,1);assert.equal(audio.paused,false);assert.equal(audio.currentTime,79);assert.equal(e.index,0);console.log('PASS: playing -> sleep -> 12s wake -> same track/position resumed');
 // User-paused audio must stay paused throughout sleep and wake.
 ({e,audio,counts}=setup(false));e.rd140SleepSuspend();e.rd140SleepWake();await advance(20000);assert.equal(counts().plays,0);console.log('PASS: manual pause never auto-resumes');
 // Manual pause after wake cancels any scheduled play.
 ({e,audio,counts}=setup(true));e.rd140SleepSuspend();e.rd140SleepWake();e.rd140SleepCancel();e.desiredAutoplay=false;await advance(20000);assert.equal(counts().plays,0);console.log('PASS: stop / manual-pause cancels pending resume');
 // Restart/OS missed suspend path uses active play intent rather than blank pause state.
 ({e,audio,counts}=setup(true));audio.paused=true;e.snapshot.state='paused';e.rd140SleepWake();await advance(12000);assert.equal(counts().plays,1);console.log('PASS: missed suspend signal with playback intent recovers');
 // Feature OFF avoids sleep guards entirely, no extra pause/resume.
 ({e,audio,counts}=setup(true));e.preferences.sleepWakeAutoResume=false;e.rd140SleepSuspend();e.rd140SleepWake();assert.equal(audio.paused,false);await advance(20000);assert.equal(counts().plays,0);console.log('PASS: disabled sleep protection leaves existing playback alone');
 // User-configurable 5s and 60s boundaries.
 for(const secs of [5,60]){({e,audio,counts}=setup(true));e.preferences.sleepWakeDelaySeconds=secs;e.rd140SleepSuspend();e.rd140SleepWake();await advance(secs*1000-1);assert.equal(counts().plays,0);await advance(1);assert.equal(counts().plays,1);console.log('PASS: user delay '+secs+' seconds');}
 console.log('ALL RESONADECK 1.4.0 SLEEP TESTS PASSED');
})().catch(e=>{console.error(e);process.exitCode=1});
