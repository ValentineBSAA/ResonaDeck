const fs=require('fs'),assert=require('node:assert/strict'),vm=require('vm');
const src=fs.readFileSync('src/index.js','utf8'),dist=fs.readFileSync('dist/index.js','utf8');
assert.equal(src,dist);assert(src.includes("const RD_VERSION = '1.0.8';"));
const part=(begin,end)=>{const i=src.indexOf(begin),j=src.indexOf(end,i+begin.length);assert(i>=0&&j>i,`missing ${begin}`);return src.slice(i,j);};
const pick=vm.runInNewContext(part('function rdPickContinueIndexV930(', 'async function rdQuickPlayCollectionV930(')+';rdPickContinueIndexV930');
assert.equal(pick([{viewCount:1},{viewOffset:72000,durationMs:150000,lastViewedAt:123},{viewOffset:42000,durationMs:150000,lastViewedAt:200}]),2);
assert.equal(pick([{viewCount:1},{viewCount:0},{viewCount:0}]),1);
assert.equal(pick([{viewOffset:149000,durationMs:150000,viewCount:1},{viewCount:0}]),1);
assert.equal(pick([]),0);
const accent=vm.runInNewContext(part('const RD_ART_NEUTRAL_V934=', 'function useArtworkAccentV930(')+';rdArtworkAccentV930');
const pixels=new Uint8ClampedArray(48*48*4);for(let i=0;i<pixels.length;i+=4){pixels[i]=200;pixels[i+1]=40;pixels[i+2]=57;pixels[i+3]=255;}
assert(/^rgb\(\d+,\d+,\d+\)$/.test(accent({data:pixels})),'red album art must produce RGB accent');
assert.equal(accent({data:new Uint8ClampedArray([8,8,8,255])}),'#38556e');
let now=[];
const h=(component,props,...children)=>({component,props:props||{},children:children.flat(Infinity).filter(x=>x!=null)});
const context={R:{useRef:initial=>({current:initial}),useEffect:()=>{}},h,DFL:{DialogButton:'button',Focusable:'group'},setTimeout,clearTimeout,
 rdRoleV940:role=>role,rdCardGlassStyleV940:()=>({}),rdSkinV940:()=>h('span',{}),ArtworkV5:()=>h('img',{}),rdArtPathForRoleV83:()=>'',rdArtModeV5:()=>'',rdMediaTypeV5:item=>item.type||'',roleInfo:()=>({label:'Audio'})};
vm.createContext(context);
vm.runInContext(part('const RD_PREVIEW_HOLD_MS_V930', 'function rdPickContinueIndexV930('),context);
const card=context.QamHoldCardV930({item:{ratingKey:'1',title:'Album'},role:'music',index:0,onPlay:()=>now.push('play'),onPreview:()=>now.push('preview'),onActions:()=>now.push('actions'),onSelect:()=>{},onGamepadDirection:()=>{}});
card.props.onClick();assert.deepEqual(now,['play']);
card.props.onSecondaryButton();assert.deepEqual(now,['play','actions']);
// Separate simulated long press, which must swallow the synthetic release click.
const clock=async()=>{card.props.onPointerDown();await new Promise(resolve=>setTimeout(resolve,570));card.props.onPointerUp();card.props.onClick();assert.deepEqual(now,['play','actions','preview']);};
let playlist=[];
const context2={rdMediaTypeV5:item=>item.type||'',rdPickContinueIndexV930:pick,
 playTrack:async(item,kind,role)=>playlist.push(['track',kind,role,item.ratingKey]),
 audioEngine:{setBook:async(m,auto,offset)=>playlist.push(['book',offset]),setQueue:async(q,i,k)=>playlist.push(['queue',i,k,q.map(x=>x.ratingKey)])},
 call:async(method,key)=>{
   if(method==='get_book_manifest')return {success:true,manifest:{resume:{positionMs:18000},files:[{ratingKey:'b1'}]}};
   if(method==='get_artist_tracks')return {tracks:[{ratingKey:'a1'}]};
   if(method==='get_children')return key==='podcast'?{items:[{ratingKey:'season'}],tracks:[]}:{tracks:key==='season'?[{ratingKey:'p1',durationMs:900000,viewOffset:45000,lastViewedAt:222},{ratingKey:'p2',viewOffset:0}]:[{ratingKey:'m1'},{ratingKey:'m2'}]};
 }};
vm.createContext(context2);
vm.runInContext(part('async function rdQuickPlayCollectionV930(', 'function QamBrowserV7('),context2);
const verify=async()=>{
 await clock();
 await context2.rdQuickPlayCollectionV930({ratingKey:'book',type:'album'},{role:'audiobooks',view:'books',kind:'audiobook'});
 await context2.rdQuickPlayCollectionV930({ratingKey:'podcast',type:'artist'},{role:'podcasts',view:'artists',kind:'podcast'});
 await context2.rdQuickPlayCollectionV930({ratingKey:'music',type:'album'},{role:'music',view:'albums',kind:'music'});
 await context2.rdQuickPlayCollectionV930({ratingKey:'asmr',type:'track'},{role:'other',view:'tracks',kind:'music'});
 playlist=JSON.parse(JSON.stringify(playlist));
 assert.deepEqual(playlist[0],['book',18000]);
 assert.deepEqual(playlist[1],['queue',0,'podcast',['p1','p2']]);
 assert.deepEqual(playlist[2],['queue',0,'music',['m1','m2']]);
 assert.deepEqual(playlist[3],['track','music','other','asmr']);
 // A 47-track queue must render every row instead of only the next six.
 const ctx={R:{useRef:x=>({current:x}),useEffect:()=>{}},h,DFL:{Focusable:'group',DialogButton:'button'},ControlV5:(p)=>h('button',p),rdV948QueueSkin:()=>h('span',{className:'rd-v948-queue-skin'}),rdV948QueueAction:(label,props)=>h('button',{...props,className:`${props.className||''} rd-v948-queue-button rd-v948-queue-action`},h('span',{className:'rd-v948-queue-face'},label)),
   audioEngine:{loadIndex:()=>{},removeAt:()=>{}},rdItemKeyV5:x=>x.ratingKey,rdQamDirectionalV7:()=>{},rdFmtMsV75:()=>'',rdFocusElementV5:()=>{},roleInfo:()=>({label:'Audio'}),rdDispatchQamNavigateV912:()=>false};
 vm.createContext(ctx);vm.runInContext(part('function QamMusicQueueDrawerV912(', 'function rdArtworkAccentV930('),ctx);
 const queue=Array.from({length:47},(_,i)=>({ratingKey:`track${i}`,title:`Song ${i}`}));const tree=ctx.QamMusicQueueDrawerV912({snap:{index:26,queue},cur:{libraryRole:'music'},onClose:()=>{}});
 const nodes=[];const walk=x=>{if(x&&typeof x==='object'){nodes.push(x);for(const y of x.children||[])walk(y);}};walk(tree);
 const jumps=nodes.filter(n=>n.props?.['data-rd-qam-queue-row']!==undefined);
 assert.equal(jumps.length,47);assert(jumps.some(n=>n.props['data-rd-qam-queue-row']==='26'));
 assert(src.includes('rd-v930-queue-scroll'));assert(src.includes('rd-v930-preview-open'));
 assert(src.includes('onCancel:e=>{e?.preventDefault?.();e?.stopPropagation?.();back();}'));
 assert(!src.includes("'data-rd-v930-preview-selected':'1'"),'Preview must be gesture-based without a stray button');
 console.log('PASS 0.9.30 focus checks: album tint, press/hold guard, music/podcast/book/ASMR dispatch, Plex offset choice, 47-row queue, preview fallback and B navigation.');
};
verify().catch(err=>{console.error(err);process.exitCode=1;});
