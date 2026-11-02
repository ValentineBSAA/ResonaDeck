const fs=require('fs'),vm=require('vm'),assert=require('assert').strict;
const js=fs.readFileSync(require('node:path').join(__dirname,'..','dist','index.js'),'utf8');
const start=js.indexOf('const RD_DISCOVERY_DEFAULT_V11=');const end=js.indexOf('function rdDiscoveryItemV11(',start);
assert(start>0&&end>start);
const source=js.slice(start,end);
let storage={success:true,state:{preferences:{sessionLength:'20',crossfade:0},recentIds:[]}};
let delayLoad=false;let loadResolve=null;
const writes=[],calls=[];
const audioEngine={kind:'music',current:{ratingKey:'r7',title:'Now Playing',libraryRole:'music'},
 queue:[{ratingKey:'r7',libraryRole:'music'},{ratingKey:'r8',libraryRole:'music'}],snapshot:{state:'playing'},
 audio:{paused:false},crossfadeWarmV114:null,disposed:0,maybe:0,health:[],
 disposeCrossfadeWarmV114(){this.disposed++;},setCrossfadeHealthV115(...args){this.health.push(args);},
 maybeCrossfadeV11(){this.maybe++;}
};
let nRefills=0;let nSessionStarts=0;const ctx={
 audioEngine,Promise,Date,Number,Boolean,Math,Set,String,
 setTimeout,clearTimeout,onceToast(...a){calls.push(['toast',...a]);},
 async call(...args){calls.push(args);
  if(args[0]==='get_discovery_state'){
   if(delayLoad)return new Promise(res=>{loadResolve=res;});
   return storage;
  }
  if(args[0]==='save_discovery_state'){await new Promise(res=>setTimeout(res,5));return {success:true};}
  if(args[0]==='save_discovery_choice'){writes.push([args[1],args[2]]);return {success:true};}
  throw Error(args[0]);
 },
 rdSurpriseNewSessionV111(engine,rows,cfg){nSessionStarts++;ctx.RD_DISCOVERY_V11.activeSession={engine,mode:'endless'};},
 rdEnsureSurpriseRunwayV111(engine,urgent){assert(urgent);nRefills++;return Promise.resolve(true);}
};
vm.createContext(ctx);
vm.runInContext(source+'\nthis.RD_DISCOVERY_V11=RD_DISCOVERY_V11;this.RD_DISCOVERY_DEFAULT_V11=RD_DISCOVERY_DEFAULT_V11;',ctx);
const ctl=ctx.RD_DISCOVERY_V11;
(async()=>{
 await ctl.init();assert.equal(ctl.state.preferences.sessionLength,'20');
 ctl.setting('sessionLength','endless');assert.equal(nSessionStarts,1);assert.equal(nRefills,1);
 assert.equal(ctl.state.preferences.sessionLength,'endless');assert.equal(ctl.activeSession.mode,'endless');
 ctl.setting('crossfade',8);assert.equal(audioEngine.maybe,1);
 ctl.setting('crossfade',0);assert.equal(audioEngine.disposed,1);
 ctl.setting('crossfade',5);
 ctl.setting('sessionLength','40');assert.equal(ctl.activeSession,null);assert.equal(nRefills,1);
 await ctl.rd141ChoiceQueue;assert.deepEqual(writes.map(x=>x.join('=')),['sessionLength=endless','crossfade=8','crossfade=0','crossfade=5','sessionLength=40']);
 // Simulate save + reopen. Backend independently returned durable choices.
 storage={success:true,state:{preferences:{sessionLength:'endless',crossfade:5}}};
 ctl.ready=false;await ctl.init();assert.equal(ctl.state.preferences.sessionLength,'endless');assert.equal(ctl.state.preferences.crossfade,5);
 // Simulate the initial state RPC arriving AFTER an immediate setting change.
 storage={success:true,state:{preferences:{sessionLength:'20',crossfade:0}}};
 delayLoad=true;ctl.ready=false;const pending=ctl.init();ctl.setting('sessionLength','endless');ctl.setting('crossfade',10);
 loadResolve(storage);await pending;assert.equal(ctl.state.preferences.sessionLength,'endless');assert.equal(ctl.state.preferences.crossfade,10);
 await ctl.rd141ChoiceQueue;
 console.log('PASS UI: Keep Playing selection triggers live refill, crossfade immediate, OFF stops refill, async load cannot reset choices, ordered backend writes');
})().catch(e=>{console.error(e);process.exitCode=1}).finally(()=>setTimeout(()=>process.exit(),5));
