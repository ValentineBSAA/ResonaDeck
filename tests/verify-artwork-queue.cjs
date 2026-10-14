const fs=require('fs'),vm=require('vm'),assert=require('assert/strict'),path=require('path');
const source=fs.readFileSync(path.join(__dirname,'../src/index.js'),'utf8');
function fn(name){const start=source.indexOf('function '+name+'(');assert(start>=0,name);const rest=source.slice(start),end=rest.slice(1).search(/\n(?:function |const |class |async function )/);return end<0?rest:rest.slice(0,end+1);}
function harness(){
 let clock=0,tid=0,host={},handler=async()=>null;const timers=new Map(),images=[],calls=[];
 const c={Map,Set,Number,String,Boolean,Array,Object,Math,Promise,Date:{now:()=>clock},runtimeHost:()=>host,RD_ART_STORE_KEY_V81:'store',RD_ART_GOOD_KEY_V81:'decoded',setTimeout:(cb,ms)=>{const id=++tid;timers.set(id,{cb,at:clock+ms});return id},clearTimeout:id=>timers.delete(id),call:(...args)=>{calls.push(args);return handler(...args)},Image:class{constructor(){images.push(this)} set src(v){this.url=v} async decode(){}},h:(type,props,...children)=>({type,props:props||{},children})};vm.createContext(c);
 for(const n of ['rdArtModeV5','rdArtPathV5','rdArtworkOwnerRatingKeyV83','rdArtPathForRoleV83','rdArtworkRatingKeyV81','rdArtIdentityV81','rdArtworkStoreV81','rdArtworkSeedV92','useArtworkRecordV81','rdDecodedArtCacheV81','useDecodedArtV81','rdArtworkCandidateV93','StablePreviewArtV81','ArtworkStatusV80'])vm.runInContext(fn(n),c);
 const flush=()=>new Promise(setImmediate);
 async function advance(ms){const until=clock+ms;for(let steps=0;steps<10000;steps++){const next=[...timers].filter(([,x])=>x.at<=until).sort((a,b)=>a[1].at-b[1].at)[0];if(!next)break;clock=next[1].at;timers.delete(next[0]);next[1].cb();await flush();if(steps===9999)throw Error('Timer loop');}clock=until;await flush();}
 function hooks(){let slots=[],cursor=0,effects=[];c.R={useState(init){const i=cursor++;if(!(i in slots))slots[i]=typeof init==='function'?init():init;return [slots[i],v=>{slots[i]=typeof v==='function'?v(slots[i]):v}]},useRef(init){const i=cursor++;return slots[i]||(slots[i]={current:init})},useEffect(cb,deps){const i=cursor++,old=slots[i];if(!old||deps.some((x,j)=>x!==old.deps[j])){effects.push(()=>{old?.clean?.();slots[i]={deps,clean:cb()}})}}};return {render(cb){cursor=0;effects=[];const out=cb();effects.forEach(f=>f());return out},unmount(){slots.forEach(x=>x?.clean?.())}};}
 return {c,calls,images,flush,advance,hooks,setHandler:fn=>handler=fn};
}
const req=(id,path='/album')=>({path,ratingKey:id,role:'music',mode:'square-card'}),id=n=>`music|${n}|square-card`;
(async()=>{
 // Regression: individual response revision 144 must not skip 143 other covers.
 let t=harness(),store=t.c.rdArtworkStoreV81(),delivered=[];store.subscribe(id('a'),r=>delivered.push(r));
 store.merge({identity:id('other'),state:'downloading',revision:144});assert.equal(store.revision,0);
 t.setHandler(async(name,since)=>{assert.equal(name,'get_artwork_updates');assert.equal(since,0);return {success:true,revision:143,records:[{identity:id('a'),state:'ready',url:'/a',revision:143}]}});
 await store.poll();assert.equal(delivered.at(-1).url,'/a');assert.equal(store.revision,143);
 store.merge({identity:id('a'),state:'downloading',revision:1});assert.equal(store.records.get(id('a')).state,'ready');
 // Metadata hydration plus page-N promise resolving after card identity changes.
 t=harness();store=t.c.rdArtworkStoreV81();let resolveOld;
 t.setHandler((name,p,mode,key)=>name==='get_artwork_record'?key==='old'?new Promise(r=>resolveOld=r):Promise.resolve({identity:id(key),state:'ready',url:p,revision:2}):Promise.resolve({records:[],revision:0}));
 const hook=t.hooks();let item={type:'track',ratingKey:'old'};
 const render=()=>hook.render(()=>t.c.useArtworkRecordV81({item,role:'music',path:t.c.rdArtPathForRoleV83(item,'music')}));
 render();await t.flush();item={type:'track',ratingKey:'track',parentRatingKey:'album',parentThumb:'/album-cover'};assert.equal(render(),null);await t.flush();assert.equal(render().url,'/album-cover');
 resolveOld({identity:id('old'),state:'ready',url:'/wrong-page',revision:1});await t.flush();assert.equal(render().identity,id('album'));assert.equal(render().url,'/album-cover');
 item={...item,parentThumb:'/hydrated-cover'};render();await t.flush();assert.equal(render().url,'/hydrated-cover');hook.unmount();
 // A rejected RPC is retried after a delay; two retries total, shared across renders/remounts.
 t=harness();store=t.c.rdArtworkStoreV81();let attempts=0;store.subscribe(id('retry'),()=>{});
 t.setHandler(async(name,p)=>{if(name==='get_artwork_updates')return {records:[],revision:0};if(++attempts<2)throw Error('network');return {identity:id('retry'),state:'ready',url:p,revision:1}});
 await store.ensure(req('retry'));assert.equal(store.records.get(id('retry')).state,'failed');await t.advance(1500);assert.equal(attempts,2);assert.equal(store.records.get(id('retry')).state,'ready');await store.ensure(req('retry'));assert.equal(attempts,2);
 t=harness();store=t.c.rdArtworkStoreV81();attempts=0;store.subscribe(id('bad'),()=>{});t.setHandler(async name=>{if(name==='get_artwork_updates')return {records:[],revision:0};attempts++;throw Error('network')});await store.ensure(req('bad'));await t.advance(10000);assert.equal(attempts,3);await store.ensure(req('bad'));await t.advance(10000);assert.equal(attempts,3);
 // Legitimately absent metadata is not hammered; a newly supplied path allows recovery.
 t=harness();store=t.c.rdArtworkStoreV81();attempts=0;store.subscribe(id('missing'),()=>{});t.setHandler(async(name,p)=>{if(name==='get_artwork_updates')return {records:[],revision:0};attempts++;return p?{identity:id('missing'),state:'ready',url:p,revision:2}:{identity:id('missing'),state:'failed',errorCode:'NO_CANONICAL_ART',revision:1}});await store.ensure(req('missing',''));await t.advance(10000);assert.equal(attempts,1);await store.ensure(req('missing','/later'));assert.equal(store.records.get(id('missing')).url,'/later');
 // Failed image predecode retries the same canonical cover with a new browser request URL.
 t=harness();store=t.c.rdArtworkStoreV81();store.subscribe(id('image'),()=>{});t.setHandler(async(name,p)=>name==='get_artwork_updates'?{records:[],revision:0}:{identity:id('image'),state:'ready',url:'http://local/cover?v=1',revision:1});await store.ensure(req('image'));
 const decoder=t.hooks();const draw=()=>decoder.render(()=>t.c.useDecodedArtV81(t.c.rdArtworkCandidateV93(store.records.get(id('image'))),id('image'),false,()=>store.retry(id('image'),true)));
 draw();t.images.at(-1).onerror();await t.advance(1500);draw();assert(t.images.at(-1).url.endsWith('&rd_image_retry=1'));await t.images.at(-1).onload();assert(draw().includes('rd_image_retry=1'));decoder.unmount();
 // 144 Music requests drain FIFO with a maximum of four concurrent metadata calls.
 t=harness();store=t.c.rdArtworkStoreV81();let active=0,max=0,order=[];t.setHandler(async(name,p,mode,key)=>{active++;max=Math.max(max,active);order.push(Number(key));await t.flush();active--;return {identity:id(key),state:'ready',url:p,revision:Number(key)+1}});
 await store.prefetch(Array.from({length:144},(_,i)=>req(String(i))));assert.equal(max,4);assert.equal(order.length,144);assert.equal(order.at(-1),143);assert.equal(store.records.get(id('143')).state,'ready');assert.equal(store.ensureJobs.size,0);assert.equal(store.revision,0);
 // A stuck request releases its queue slot and identity promise at the deadline.
 t=harness();store=t.c.rdArtworkStoreV81();t.setHandler(()=>new Promise(()=>{}));const stuck=store.ensure(req('stuck'));await t.flush();await t.advance(45000);await stuck;assert.equal(store.ensureJobs.size,0);assert.equal(store.active,0);
 const album={type:'album',ratingKey:'album',parentRatingKey:'artist',thumb:'/album-cover',parentThumb:'/artist'},track={type:'track',ratingKey:'track',parentRatingKey:'album',parentThumb:'/album-cover',grandparentThumb:'/artist'};
 const full=t.c.rdArtIdentityV81(t.c.rdArtPathV5(album),t.c.rdArtworkOwnerRatingKeyV83(album,'music'),'music','square-card'),qam=t.c.rdArtIdentityV81(t.c.rdArtPathForRoleV83(album,'music'),t.c.rdArtworkOwnerRatingKeyV83(album,'music'),'music',t.c.rdArtModeV5('music',false));assert.equal(full,qam);assert.equal(t.c.rdArtworkOwnerRatingKeyV83(track,'music'),'album');assert.equal(t.c.rdArtPathForRoleV83(track,'music'),'/album-cover');
 for(const key of ['book1','book2']){const book={semanticType:'book',ratingKey:key,parentRatingKey:'author',thumb:`/${key}`,parentThumb:'/author'};assert.equal(t.c.rdArtworkOwnerRatingKeyV83(book,'audiobooks'),key);assert.equal(t.c.rdArtPathForRoleV83(book,'audiobooks'),`/${key}`)}
 // Status still mounts; inactive waiting startup retries without forcing cache rebuild.
 t=harness();let starts=0;t.setHandler(async name=>name==='get_artwork_status'?{state:'waiting',active:false}:{state:++starts<2?'waiting':'downloading',active:starts>=2,queued:2});const status=t.hooks();status.render(()=>t.c.ArtworkStatusV80());await t.flush();assert.equal(starts,1);await t.advance(1500);assert.equal(starts,2);const panel=status.render(()=>t.c.ArtworkStatusV80());assert.equal(panel.props.style.display,'grid');assert(panel.props['aria-label'].includes('2 pending'));status.unmount();
 assert.equal(source,fs.readFileSync(path.join(__dirname,'../dist/index.js'),'utf8'));
 console.log('PASS: cursor loss reproduced/fixed; stale revisions; hydration and old-page identity isolation; delayed bounded RPC/image retries; missing metadata; 144-item FIFO fairness/limit; hung RPC deadline; canonical album identity; sibling Books; status/worker startup recovery; src/dist sync.');
})().catch(e=>{console.error(e);process.exitCode=1});
