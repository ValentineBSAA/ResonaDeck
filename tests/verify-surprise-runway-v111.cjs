'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('src/index.js','utf8');
const cut=(a,b)=>{const i=source.indexOf(a),j=source.indexOf(b,i+1);assert(i>=0&&j>i,a);return source.slice(i,j);};
assert(source.includes("sessionLength:'20'"),'default track count unchanged');
assert(source.includes("['30m','30 min']")&&source.includes("['60m','1 hour']")&&source.includes("['120m','2 hours']")&&source.includes("['endless','Keep Playing']"),'duration controls');
assert(source.includes("async advance(delta=1,fromEnded=false){this.cancelCrossfadeV11();if(delta>0&&this.kind==='music'&&this.index+delta>=this.queue.length)await rdEnsureSurpriseRunwayV111(this,true);"),'manual Next must request refill before boundary');
assert(source.includes('void rdEnsureSurpriseRunwayV111(this,false);this.maybeCrossfadeV11(a);'),'prefetch before the queue is empty');
assert(source.includes('async stop(force=false){RD_DISCOVERY_V11.activeSession=null;'),'stop cancels extension');
assert(source.includes("this.artUrl=rdArtworkFastCoverV947(item,role,artPath)||''"),'try warm cached cover before remote lookup');
assert(source.includes("void this.report('stopped');this.stopReporting();"),'old Plex reporting cannot hold up song transition');
const state={preferences:{},favorites:[],recentIds:[]};const track=(n)=>({ratingKey:String(n),title:'Song '+n,libraryRole:'music',duration:180000,thumb:'/music/'+n});
let calls=0,latency=null;
const context={Math,Number,String,Set,Boolean,console,Infinity,onceToast(){},
  RD_DISCOVERY_V11:{state,activeSession:null,remember(rows){this.state.recentIds.push(...rows.map(x=>x.ratingKey));}},
  call:async(method,...args)=>{assert.equal(method,'browse_cached');calls++;if(latency)await latency;const offset=Number(args[2]);return {success:true,items:Array.from({length:40},(_,i)=>track(offset+i+1)),total:900};},
  rdDiscoveryPickV11:()=>{},
};
vm.createContext(context);
vm.runInContext(cut('function rdDiscoveryPickV11(','async function rdSurpriseMeV11('),context);
vm.runInContext(cut('const RD_SURPRISE_LENGTHS_V111=','/* 1.1.1: independently painted glass'),context);
assert.equal(context.rdSurpriseTrackSecondsV111({duration:180000}),180);
assert.equal(context.rdSurpriseTrackSecondsV111({duration:180}),180);
assert.equal(context.rdSurpriseLengthLabelV111({sessionLength:'60m'}),'1 hour');
const makeEngine=(rows,idx)=>({kind:'music',queue:[...rows],unshuffledQueue:[...rows],index:idx,publish(){this.pub=(this.pub||0)+1;}});
(async()=>{
  const base=Array.from({length:20},(_,i)=>track(i+1));
  const counted=makeEngine(base,18);context.rdSurpriseNewSessionV111(counted,base,{category:'music',sessionLength:'20',musicMode:'tracks'});
  assert.equal(context.RD_DISCOVERY_V11.activeSession,null,'fixed track-count should remain finite');
  const timed=makeEngine(base,15);
  context.rdSurpriseNewSessionV111(timed,base,{category:'music',sessionLength:'120m',musicMode:'tracks'});
  assert.equal(context.RD_DISCOVERY_V11.activeSession.goalSeconds,7200);
  assert.equal(context.RD_DISCOVERY_V11.activeSession.plannedSeconds,3600);
  assert.equal(await context.rdEnsureSurpriseRunwayV111(timed,false),false,'do not fetch 4+ tracks early');
  assert.equal(calls,0);
  timed.index=18;
  assert.equal(await context.rdEnsureSurpriseRunwayV111(timed,false),true,'must refill with 2 songs remaining');
  assert(timed.queue.length>20,'queue extends for 2-hour session');
  assert.equal(new Set(timed.queue.map(x=>x.ratingKey)).size,timed.queue.length,'no duplicate active songs');
  assert(context.RD_DISCOVERY_V11.activeSession.plannedSeconds>=7200,'time budget covered');
  const prevCalls=calls;
  assert.equal(await context.rdEnsureSurpriseRunwayV111(timed,true),false,'no more fetching once timed goal is satisfied');
  assert.equal(calls,prevCalls);
  const continuous=makeEngine(base,18);context.rdSurpriseNewSessionV111(continuous,base,{category:'music',sessionLength:'endless',musicMode:'tracks'});
  assert.equal(await context.rdEnsureSurpriseRunwayV111(continuous,false),true);
  assert(continuous.queue.length>20);
  let max=continuous.queue.length;
  for(let i=0;i<8;i++){
    continuous.index=continuous.queue.length-2;
    await context.rdEnsureSurpriseRunwayV111(continuous,false);
    max=Math.max(max,continuous.queue.length);
  }
  assert(max<=55,'endless mode queue stays bounded');
  assert(continuous.index<continuous.queue.length,'current index remains valid');
  const shorter=Array.from({length:20},(_,i)=>({...track(i+1),duration:300000}));
  assert.equal(context.rdSurpriseInitialRowsV111(shorter,{sessionLength:'30m',musicMode:'tracks'}).length,6,'30-minute session should not queue all 20 long songs');
  assert.equal(context.rdSurpriseInitialRowsV111(shorter,{sessionLength:'60m',musicMode:'tracks'}).length,12,'one-hour queue should follow track durations');
  state.favorites=base.slice(0,10);
  const favorite=makeEngine(base.slice(0,10),8);context.rdSurpriseNewSessionV111(favorite,favorite.queue,{category:'music',sessionLength:'endless',musicMode:'tracks',favoritesOnly:true});
  assert.equal(await context.rdEnsureSurpriseRunwayV111(favorite,false),true,'Keep Playing must recycle listened favorites when library is exhausted');
  assert(favorite.queue.length>10,'recycled favorites appended for small collections');
  state.favorites=[];
  const stale=makeEngine(base,18);context.rdSurpriseNewSessionV111(stale,base,{category:'music',sessionLength:'endless',musicMode:'tracks'});
  let resolve;latency=new Promise(r=>resolve=r);const pending=context.rdEnsureSurpriseRunwayV111(stale,false);
  await Promise.resolve();context.RD_DISCOVERY_V11.activeSession=null;resolve();await pending;
  assert.equal(stale.queue.length,20,'Stop must reject a late asynchronous refill');
  console.log('PASS: persistent 10/20/40 + timed choices; 2h refill; stop at duration; continuous bounded queues, dedupe and Stop race');
})().catch(e=>{console.error(e);process.exit(1)});
