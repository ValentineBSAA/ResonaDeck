const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const src=fs.readFileSync('src/index.js','utf8');
const dist=fs.readFileSync('dist/index.js','utf8');
const plugin=JSON.parse(fs.readFileSync('plugin.json','utf8'));
const pkg=JSON.parse(fs.readFileSync('package.json','utf8'));
assert.equal(plugin.version,'1.0.0');assert.equal(pkg.version,'1.0.0');assert(src.includes("const RD_VERSION = '1.0.0'"));assert.equal(src,dist);
for(const part of ['RD_RECONNECT_LINES_V930','useArtworkAccentV930','rdArtworkAccentV930','RD_PREVIEW_HOLD_MS_V930','QamHoldCardV930','rdPickContinueIndexV930','rdQuickPlayCollectionV930','rd-v930-queue-scroll','rd-v930-preview-open'])assert(src.includes(part),part);
const start=src.indexOf('const RD_PREVIEW_HOLD_MS_V930='),end=src.indexOf('\nfunction QamBrowserV7(){',start);assert(start>0&&end>start);
const functions=src.slice(start,end);
let calls=[],played=[],previewed=[],opened=[],actioned=[];let nextTimer=0;const timers=new Map();
const h=(type,props,...children)=>({type,props:props||{},children:children.flat()});
const context={
 h,rdRoleV940:role=>role,rdCardGlassStyleV940:()=>({}),rdSkinV940:()=>h('span',{}),R:{useRef:value=>({current:value}),useEffect:()=>{}},DFL:{DialogButton:'dialog-button'},ArtworkV5:'cover',rdArtPathForRoleV83:()=>'',rdArtModeV5:()=>'',rdMediaTypeV5:i=>i.type||'album',roleInfo:role=>({label:role}),
 setTimeout:(cb)=>{const id=++nextTimer;timers.set(id,cb);return id;},clearTimeout:id=>timers.delete(id),
 call:async(...a)=>{calls.push(a);if(a[0]==='get_book_manifest')return {success:true,manifest:{files:[{ratingKey:'part'}],resume:{positionMs:180000}}};if(a[0]==='get_artist_tracks')return {tracks:[{ratingKey:'t1',type:'track'}]};if(a[0]==='get_children')return {tracks:[{ratingKey:'e1',viewOffset:10000,lastViewedAt:2,durationMs:300000},{ratingKey:'e2',viewOffset:45000,lastViewedAt:20,durationMs:300000},{ratingKey:'e3',viewOffset:0,viewCount:0}]};throw Error('unexpected '+a[0]);},
 audioEngine:{setBook:async(...a)=>played.push(['book',...a]),setQueue:async(...a)=>played.push(['queue',...a])},playTrack:async(...a)=>played.push(['track',...a]),
};vm.createContext(context);vm.runInContext(functions,context);
const card=context.QamHoldCardV930({item:{ratingKey:'album',title:'The Black Flame'},role:'music',index:1,onPlay:()=>opened.push('play'),onPreview:()=>previewed.push('preview'),onActions:()=>actioned.push('actions')});
assert.equal(card.props['data-rd-qam-card'],'1');
card.props.onPointerDown();card.props.onPointerUp();card.props.onClick();assert.deepEqual(opened,['play']);assert.equal(previewed.length,0);
card.props.onPointerDown();for(const cb of [...timers.values()])cb();timers.clear();card.props.onPointerUp();card.props.onClick();assert.deepEqual(previewed,['preview']);assert.deepEqual(opened,['play']);
card.props.onSecondaryButton();assert.deepEqual(previewed,['preview']);assert.deepEqual(actioned,['actions']);
assert.equal(context.rdPickContinueIndexV930([{viewOffset:12000,lastViewedAt:20,durationMs:200000},{viewOffset:25000,lastViewedAt:30,durationMs:200000}]),1);
assert.equal(context.rdPickContinueIndexV930([{viewOffset:0,viewCount:1},{viewOffset:0,viewCount:0}]),1);
assert.equal(context.rdPickContinueIndexV930([{viewOffset:50000,durationMs:52000,viewCount:1},{viewOffset:0,viewCount:0}]),1);
(async()=>{
 await context.rdQuickPlayCollectionV930({ratingKey:'album',type:'album'}, {role:'music',kind:'music',view:'albums'});
 assert.equal(played.at(-1)[0],'queue');assert.equal(played.at(-1)[2],0);
 await context.rdQuickPlayCollectionV930({ratingKey:'show',type:'artist'}, {role:'podcasts',kind:'podcast',view:'artists'});
 assert.equal(played.at(-1)[0],'queue');assert.equal(played.at(-1)[2],1);
 await context.rdQuickPlayCollectionV930({ratingKey:'book',type:'album'}, {role:'audiobooks',kind:'audiobook',view:'books'});
 assert.equal(played.at(-1)[0],'book');assert.equal(played.at(-1)[3],180000);
 await context.rdQuickPlayCollectionV930({ratingKey:'asmr',type:'track'}, {role:'other',kind:'music',view:'tracks'});
 assert.equal(played.at(-1)[0],'track');assert.equal(played.at(-1)[3],'other');
 console.log('PASS 0.9.30: version sync, press A play, long hold preview without click-through, explicit preview fallback, podcast episode resume, book bookmark, ASMR direct play, artist/album routing');
})().catch(e=>{console.error(e);process.exit(1)});
