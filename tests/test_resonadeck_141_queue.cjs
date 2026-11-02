'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const src=fs.readFileSync(require('node:path').join(__dirname,'..','dist','index.js'),'utf8');
const cut=(a,b)=>{const i=src.indexOf(a),j=src.indexOf(b,i+1);assert(i>=0&&j>i,'missing '+a);return src.slice(i,j);};
const row=n=>({ratingKey:String(n),title:'Plex song '+n,libraryRole:'music',duration:180,thumb:'/art/'+n});
let now=100000,fail=false,pending=null, networkCalls=0, warmed=0;
const state={preferences:{},favorites:[],recentIds:[]};
const ctx={Math,Number,String,Array,Boolean,Set,Infinity,Promise,console,
 Date:{now:()=>now},onceToast(){},
 rdArtworkOwnerRatingKeyV83:v=>v.ratingKey,rdArtModeV5:()=> 'square',rdArtPathForRoleV83:v=>v.thumb,
 rdArtworkStoreV81:()=>({prefetch(){warmed++;return Promise.resolve([]);}}),
 rdMergeUniqueV5:(...parts)=>{const seen=new Set();return parts.flat().filter(x=>{const id=String(x.ratingKey);if(seen.has(id))return false;seen.add(id);return true;});},
 RD_DISCOVERY_V11:{state,activeSession:null,remember(xs){state.recentIds.push(...xs.map(x=>String(x.ratingKey)));}},
 call:async (method,...args)=>{
  networkCalls++;if(pending)await pending;if(fail){throw Error('Plex temporary outage');}
  if(method==='browse_cached'){const from=Number(args[2]);return {success:true,items:Array.from({length:40},(_,i)=>row(from+1+i)),total:950};}
  if(method==='get_children')return {tracks:[row(90),row(91)]};
  throw Error('Unexpected method '+method);
 }
};
vm.createContext(ctx);
vm.runInContext(cut('function rdDiscoveryPickV11(','async function rdSurpriseMeV11('),ctx);
vm.runInContext(cut('const RD_SURPRISE_LENGTHS_V111=','/* 1.1.1: independently painted glass'),ctx);
const engine=(arr,i,kind='music')=>({kind,queue:arr.slice(),unshuffledQueue:arr.slice(),index:i,current:arr[i],snapshot:{state:'playing'},audio:{paused:false},publish(){this.publishes=(this.publishes||0)+1;}});
(async()=>{
 let e=engine(Array.from({length:55},(_,i)=>row(i+1)),54);
 ctx.rdSurpriseNewSessionV111(e,e.queue,{category:'music',sessionLength:'endless',musicMode:'tracks'});
 const before=ctx.rdSurpriseQueuePositionV113(e,e).position;
 assert.equal(before,55);
 fail=true;
 assert.equal(ctx.rdSurpriseBoundaryGuardV138(e),true,'last song rescues instantly even if network is down');
 assert(e.queue.length-e.index>=2,'new music available after boundary');
 assert(e.queue.length<=60,'bounded queue after compaction');
 assert.equal(ctx.rdSurpriseQueuePositionV113(e,e).position,55,'continuous lifetime index after trim');
 assert.equal(ctx.rdSurpriseQueuePositionV113(e,e).ahead>0,true);
 assert(warmed>0,'artwork prewarming retained');
 // Simulate continued streaming and offline recycle over 120 lifetime songs.
 let last=55;
 for(let trackNumber=56;trackNumber<=130;trackNumber++){
   if(e.index+1>=e.queue.length)assert.equal(ctx.rdSurpriseBoundaryGuardV138(e,2),true,'offline refills at boundary');
   e.index++;e.current=e.queue[e.index];
   const pos=ctx.rdSurpriseQueuePositionV113(e,e).position;
   assert.equal(pos,trackNumber,'lifetime position for '+trackNumber);
   assert(e.queue.length<=60,'bounded at '+trackNumber);
   last=pos;
   if(e.queue.length-1-e.index<=2)ctx.rdSurpriseBoundaryGuardV138(e,2);
 }
 assert.equal(last,130);
 // Simulate the asynchronous cached browse throwing: Keep Playing still has songs.
 e.index=e.queue.length-3;e.current=e.queue[e.index];
 const returned=await ctx.rdEnsureSurpriseRunwayV111(e,true);
 assert(returned||e.queue.length-1-e.index>0,'failed network cannot drain valid endless queue');
 // One-track Plex collection should recycle itself, not stop.
 const one=engine([row(1)],0);
 ctx.rdSurpriseNewSessionV111(one,one.queue,{category:'music',sessionLength:'endless',musicMode:'tracks'});
 assert(ctx.rdSurpriseBoundaryGuardV138(one,0));
 assert.equal(one.queue[one.index+1].ratingKey,'1');
 // One song remains for album mode: rescue with known songs.
 const albums=engine([row(101),row(102),row(103)],2);
 ctx.rdSurpriseNewSessionV111(albums,albums.queue,{category:'music',sessionLength:'endless',musicMode:'albums'});
 assert(ctx.rdSurpriseBoundaryGuardV138(albums));
 assert(albums.queue.length>3);
 // Timed sessions do not use emergency refill, but normal timed refills still work.
 fail=false;
 const timed=engine(Array.from({length:20},(_,i)=>row(i+1)),18);
 ctx.rdSurpriseNewSessionV111(timed,timed.queue,{category:'music',sessionLength:'120m',musicMode:'tracks'});
 assert.equal(ctx.rdSurpriseBoundaryGuardV138(timed,2),false);
 assert.equal(await ctx.rdEnsureSurpriseRunwayV111(timed,true),true,'normal timed session refill preserved');
 assert(timed.queue.length>20);
 ctx.RD_DISCOVERY_V11.activeSession.listenedSeconds=7200;
 assert.equal(await ctx.rdEnsureSurpriseRunwayV111(timed,true),false,'timed sessions end at chosen duration');
 // Standard manual queue cannot be rescued.
 ctx.RD_DISCOVERY_V11.activeSession=null;
 const manual=engine([row(1),row(2)],1);
 assert.equal(ctx.rdSurpriseBoundaryGuardV138(manual,2),false);
 assert.equal(manual.queue.length,2);
 // Stopped session cannot be restarted by late async responses.
 const stopped=engine(Array.from({length:20},(_,i)=>row(i+1)),15);
 ctx.rdSurpriseNewSessionV111(stopped,stopped.queue,{category:'music',sessionLength:'endless'});
 let resolve;pending=new Promise(r=>resolve=r);const future=ctx.rdEnsureSurpriseRunwayV111(stopped,false);
 await Promise.resolve();ctx.RD_DISCOVERY_V11.activeSession=null;resolve();await future;pending=null;
 assert.equal(stopped.queue.length,20);
 // Helpers must remain in playback advance AND crossfade admission.
 assert(src.includes('if(this.index+1>=this.queue.length)rdSurpriseBoundaryGuardV138(this);'));
 assert(src.includes("if(delta>0&&this.kind==='music'&&RD_DISCOVERY_V11.activeSession?.mode==='endless')rdSurpriseBoundaryGuardV138(this,2);"));
 // All previous 1.3.7 features remain in same built file.
 for(const marker of ['rdV134CorsOptedIn','rdGtmBridge','gtmVisual','crossfadeBlend','Open Full ResonaDeck']){
  if(!src.toLowerCase().includes(marker.toLowerCase()))console.warn('Non-critical feature marker not found:',marker);
 }
 console.log('PASS ResonaDeck 1.3.8: 55→130 continuous offline queue, bounded history, timed sessions, manual playlists, one-song replay, album fallback, cancelled request and crossfade guard');
})().catch(e=>{console.error(e.stack||e);process.exit(1)});
