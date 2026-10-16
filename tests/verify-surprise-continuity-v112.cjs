'use strict';
const fs=require('node:fs'), vm=require('node:vm'), assert=require('node:assert/strict');
const src=fs.readFileSync('src/index.js','utf8');
assert.equal(src,fs.readFileSync('dist/index.js','utf8'));
assert(src.includes("const RD_VERSION = '1.1.2'"));
const read=(a,b)=>{const i=src.indexOf(a),j=src.indexOf(b,i+1);assert(i>=0&&j>i,a);return src.slice(i,j);};
const create=(id)=>({ratingKey:String(id),title:'Song '+id,libraryRole:'music',duration:180000,thumb:'/cover/'+id});
let clock=100000,callCount=0,failNext=false,defer=null,artWarm=[];
const state={preferences:{},favorites:[],recentIds:[]};
const engine=(tracks,index)=>({kind:'music',queue:tracks.slice(),unshuffledQueue:tracks.slice(),index, snapshot:{state:'playing'},audio:{paused:false},publish(){this.published=true;}});
const ctx={Math,Number,String,Boolean,Set,Infinity,Promise,console,
  Date:{now:()=>clock},onceToast(){},
  rdArtworkOwnerRatingKeyV83:r=>r.ratingKey,rdArtModeV5:()=> 'square-card',rdArtPathForRoleV83:r=>r.thumb,
  rdArtworkStoreV81:()=>({prefetch:reqs=>{artWarm.push(reqs);return Promise.resolve([]);}}),
  rdMergeUniqueV5:(...blocks)=>{const seen=new Set();return blocks.flat().filter(x=>{const k=String(x.ratingKey);if(seen.has(k))return false;seen.add(k);return true;});},
  RD_DISCOVERY_V11:{state,activeSession:null,remember(rows){state.recentIds.push(...rows.map(x=>x.ratingKey));}},
  call:async(method,...args)=>{callCount++;if(failNext){failNext=false;throw new Error('Temporary Plex error');}if(defer)await defer;
    if(method==='browse_cached')return {success:true,total:100,items:Array.from({length:40},(_,i)=>create(Number(args[2])+i+1))};
    if(method==='get_children')return {tracks:[create(1),create(2),create(3)]};
    throw new Error('Unexpected '+method);
  }
};
vm.createContext(ctx);
vm.runInContext(read('function rdDiscoveryPickV11(','async function rdSurpriseMeV11('),ctx);
vm.runInContext(read('const RD_SURPRISE_LENGTHS_V111=','/* 1.1.1: independently painted glass'),ctx);
(async()=>{
  const twenty=Array.from({length:20},(_,i)=>create(i+1));
  assert.equal(ctx.rdSurpriseTrackSecondsV111(create(1)),180);
  assert.equal(ctx.rdSurpriseLengthLabelV111({sessionLength:'120m'}),'2 hours');
  const timed=engine(twenty,13);
  ctx.rdSurpriseNewSessionV111(timed,twenty,{category:'music',sessionLength:'120m',musicMode:'tracks'});
  assert.equal(ctx.RD_DISCOVERY_V11.activeSession.goalSeconds,7200);
  assert.equal(ctx.RD_DISCOVERY_V11.activeSession.listenedSeconds,0);
  clock+=4000;ctx.rdSurpriseClockTickV112(timed);
  assert(ctx.RD_DISCOVERY_V11.activeSession.listenedSeconds>=3.99,'actual playing time counted');
  timed.audio.paused=true;clock+=3000;ctx.rdSurpriseClockTickV112(timed);
  assert(ctx.RD_DISCOVERY_V11.activeSession.listenedSeconds<5,'paused time excluded');
  timed.audio.paused=false;
  assert.equal(await ctx.rdEnsureSurpriseRunwayV111(timed,false),false,'do not fetch with >5 songs left');
  timed.index=15;
  assert.equal(await ctx.rdEnsureSurpriseRunwayV111(timed,false),true,'refill starts with five songs remaining');
  assert(timed.queue.length>20);
  assert(artWarm.length>=2,'next-track artwork prefetch triggered');
  assert(timed.queue.length<=55);
  const run=ctx.RD_DISCOVERY_V11.activeSession;
  run.listenedSeconds=7200;
  assert(ctx.rdSurpriseDurationCompleteV111(timed));
  const prevCalls=callCount;
  assert.equal(await ctx.rdEnsureSurpriseRunwayV111(timed,true),false,'no more tracks when time elapsed');
  assert.equal(callCount,prevCalls);

  const lone=engine([create(7)],0);
  state.favorites=[create(7)];ctx.rdSurpriseNewSessionV111(lone,lone.queue,{category:'music',sessionLength:'endless',favoritesOnly:true});
  assert.equal(await ctx.rdEnsureSurpriseRunwayV111(lone,true),true,'1-track favorite library must repeat');
  assert(lone.queue.length>=2);

  const flaky=engine(twenty,18);
  ctx.rdSurpriseNewSessionV111(flaky,twenty,{category:'music',sessionLength:'endless'});
  failNext=true;
  assert.equal(await ctx.rdEnsureSurpriseRunwayV111(flaky,true),false,'failed network attempt');
  assert.equal(ctx.RD_DISCOVERY_V11.activeSession.errorCount,1);
  assert.equal(await ctx.rdEnsureSurpriseRunwayV111(flaky,true),true,'urgent boundary must retry');
  assert.equal(ctx.RD_DISCOVERY_V11.activeSession.errorCount,0);

  const stopped=engine(twenty,18);
  ctx.rdSurpriseNewSessionV111(stopped,twenty,{category:'music',sessionLength:'endless'});
  let resolve;defer=new Promise(r=>resolve=r);
  const pending=ctx.rdEnsureSurpriseRunwayV111(stopped,true);
  await Promise.resolve();ctx.RD_DISCOVERY_V11.activeSession=null;resolve();await pending;
  assert.equal(stopped.queue.length,20,'no refill after stop');
  defer=null;

  const album=engine([create(1),create(2),create(3)],2);
  ctx.rdSurpriseNewSessionV111(album,album.queue,{category:'music',musicMode:'albums',sessionLength:'endless'});
  assert.equal(await ctx.rdEnsureSurpriseRunwayV111(album,true),true,'album fallback recycles tracks when fully played');
  assert(album.queue.length>3);

  assert(src.includes('rd-v112-selected-check'));
  assert(src.includes("'✕'"));
  assert(!src.includes("'✕ CLOSE'"));
  assert(src.includes('★ Browse Favorites'));
  assert(src.includes('const pageSize=compact?8:16'));
  assert(src.includes('if(!display)return h(\'img\''),'immediate fallback artwork');
  assert(src.includes('rdWarmUpcomingArtworkV112(this)'),'track switch preloads next covers');
  assert(src.includes("rdSurpriseDurationCompleteV111(this)){await this.stop();return;"),'timed auto-stop on next track boundary');
  assert(src.includes('RD_DISCOVERY_V11.activeSession?.engine!==this'),'Surprise overrides repeat-one for continuous listening');
  console.log('PASS: 1.1.2 clock, pauses, early queue refill, retries, single favorite, albums, stale request, artwork and UI invariants');
})().catch(e=>{console.error(e);process.exitCode=1});
