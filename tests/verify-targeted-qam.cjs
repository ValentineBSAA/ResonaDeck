const fs=require('fs'),vm=require('vm'),assert=require('assert/strict'),path=require('path');
const source=fs.readFileSync(path.join(__dirname,'../src/index.js'),'utf8');
function fn(name){const start=source.indexOf('function '+name+'(');assert(start>=0,name);const rest=source.slice(start),end=rest.slice(1).search(/\n(?:function |const |class |async function )/);return end<0?rest:rest.slice(0,end+1);}
let calls=[],host={},effects=[],slots=[],cursor=0;
const R={useState(init){const i=cursor++;if(!(i in slots))slots[i]=typeof init==='function'?init():init;return [slots[i],v=>slots[i]=typeof v==='function'?v(slots[i]):v]},useRef(init){const i=cursor++;return slots[i]||(slots[i]={current:init})},useEffect(cb){effects.push(cb)}};
const context={R,Map,Set,Number,String,Boolean,Array,Math,Promise,Image:class{set src(v){this.onerror?.()}},RD_DIR_UP:9,RD_DIR_DOWN:10,RD_DIR_LEFT:11,RD_DIR_RIGHT:12,RD_ART_STORE_KEY_V81:'store',RD_ART_GOOD_KEY_V81:'decoded',runtimeHost:()=>host,setTimeout:()=>0,clearTimeout:()=>{},call:async(...args)=>{calls.push(args);return {identity:`${args[5]}|${args[3]}|${args[2]}`,state:'ready',url:args[1]}},rdFocusIdV90A:el=>el?.id||'',rdFocusEvidenceV90A:()=>{},DFL:{DialogButton:'button',Focusable:'group'},h:(type,props,...children)=>({type,props:props||{},children}),useEngine:()=>({}),usePlayerArtworkV6:()=>'',rdGreetingV5:()=>'',roleInfo:()=>({}),rdMediaTypeV5:x=>x.type,ManagerDetailRouteV946:'ManagerDetailRouteV946'};
vm.createContext(context);
for(const name of ['rdDir','rdNativeTakeFocus','rdArtModeV5','rdArtPathV5','rdArtworkOwnerRatingKeyV83','rdArtPathForRoleV83','rdArtworkRatingKeyV81','rdArtIdentityV81','rdArtworkStoreV81','rdArtworkSeedV92','useArtworkRecordV81','rdDecodedArtCacheV81','useDecodedArtV81','rdQamSpatialTargetV92','rdQamRevealV92','rdQamIsTrueTopBoundaryV94','rdConsumeDirectionV80','rdQamExplicitTargetV933','rdQamDirectionalV7'])vm.runInContext(fn(name),context);
const doc={activeElement:null,defaultView:{innerHeight:500}};
function button(id,x,y,w=60,h=30){return {id,ownerDocument:doc,disabled:false,getAttribute:()=>null,getBoundingClientRect:()=>({left:x,right:x+w,top:y,bottom:y+h,width:w,height:h}),focus(){doc.activeElement=this},scrollIntoView(){this.scrolled=true}}}
const account=button('account',180,0),a=button('a',0,60),b=button('b',80,60),vol=button('volume',0,110,240),tab=button('tab',0,160),card=button('card',0,210),last=button('launch',0,600,240),elements=[account,a,b,vol,tab,card,last],root={querySelectorAll:()=>elements};
let ancestorTakes=0;context.DFL.getGamepadNavigationTrees=()=>[{m_element:{contains:()=>true},BTakeFocus:()=>{ancestorTakes++;return true},children:elements.map(el=>({m_element:el,BTakeFocus:()=>el.focus()}))}];
context.rdQamRootV7=()=>root;context.rdFocusElementV5=context.rdNativeTakeFocus;context.rdQamNativeFocusV934=context.rdNativeTakeFocus;
function move(current,d){let consumed=0;assert(context.rdQamDirectionalV7({currentTarget:current,detail:{button:d},preventDefault:()=>consumed++,stopPropagation:()=>consumed++}));assert.equal(consumed,2);return doc.activeElement;}
assert.equal(move(a,12),b);assert.equal(move(b,11),a);assert.equal(move(b,10),vol);assert.equal(move(a,9),account);let topConsumed=0;doc.activeElement=account;assert.equal(context.rdQamDirectionalV7({currentTarget:account,detail:{button:9},preventDefault:()=>topConsumed++,stopPropagation:()=>topConsumed++}),false);assert.equal(topConsumed,0);assert.equal(doc.activeElement,account);assert.equal(move(vol,10),tab);assert.equal(move(card,9),tab);assert.equal(move(card,10),last);assert(last.scrolled);assert.equal(ancestorTakes,0);assert(!a.scrolled);assert.equal(context.rdQamDirectionalV7({currentTarget:last,detail:{button:10},preventDefault:()=>{},stopPropagation:()=>{}}),false);assert.equal(doc.activeElement,last);
// Wrapped library cards remain spatial instead of flattening into one row.
const c=button('c',0,260),d=button('d',80,260);elements.push(c,d);assert.equal(move(card,10),c);
const track={type:'track',ratingKey:'t1',parentRatingKey:'album1',thumb:'/track',parentThumb:'/album',grandparentThumb:'/artist'};
assert.equal(context.rdArtworkOwnerRatingKeyV83(track,'music'),'album1');assert.equal(context.rdArtPathForRoleV83(track,'music'),'/album');
const book1={type:'album',ratingKey:'book1',parentRatingKey:'author',thumb:'/cover1',parentThumb:'/author'},book2={...book1,ratingKey:'book2',thumb:'/cover2'};
for(const book of [book1,book2]){assert.equal(context.rdArtworkOwnerRatingKeyV83(book,'audiobooks'),book.ratingKey);assert.equal(context.rdArtPathForRoleV83(book,'audiobooks'),book.thumb)}
assert.equal(context.rdArtworkOwnerRatingKeyV83({...book1,semanticType:'book',partKey:'/chapter'},'audiobooks'),'book1');
assert.equal(context.rdArtworkSeedV92({cachedArtUrl:'/wrong',artRegistryState:'ready',artRegistryIdentity:'audiobooks|book1|portrait-book-v85'},'audiobooks|book2|portrait-book-v85'),'');
function renderHook(item){cursor=0;effects=[];const value=context.useArtworkRecordV81({path:context.rdArtPathForRoleV83(item,'music'),item,role:'music'});effects.forEach(f=>f());return value;}
(async()=>{
renderHook({type:'track',ratingKey:'t1'});await new Promise(setImmediate);
renderHook(track);await new Promise(setImmediate);const hydrated=renderHook(track);assert.equal(hydrated.identity,'music|album1|square-card');assert.equal(hydrated.url,'/album');
renderHook({...track,parentThumb:'/new-album'});await new Promise(setImmediate);assert(calls.some(x=>x[0]==='get_artwork_record'&&x[1]==='/new-album'&&x[4]===true));
let failures=0;slots=[];cursor=0;effects=[];context.useDecodedArtV81('/expired','music|album1|square-card',false,()=>failures++);effects.forEach(f=>f());assert.equal(failures,1);
// Render the actual playlist browser, activate All Music, rerender into detail.
for(const n of ['CatalogRowsV5','MediaDetailV5','PlaylistBrowserV5'])vm.runInContext(fn(n),context);
slots=[[{title:'All Music',ratingKey:'all'}]]; // reset below to exact hook order
slots=[null,[{title:'All Music',ratingKey:'all'}],false,''];cursor=0;effects=[];
let view=context.PlaylistBrowserV5();function find(v,type){if(!v||typeof v!=='object')return; if(v.type===type)return v;for(const ch of v.children||[]){const r=Array.isArray(ch)?ch.map(x=>find(x,type)).find(Boolean):find(ch,type);if(r)return r}}
const rows=find(view,context.CatalogRowsV5);assert(rows);const before=calls.length;rows.props.onOpen({title:'All Music',ratingKey:'all'});cursor=0;view=context.PlaylistBrowserV5();assert.equal(view.type,context.ManagerDetailRouteV946 || 'ManagerDetailRouteV946');assert.equal(view.props.item.type,'playlist');assert.equal(calls.length,before);
assert(!source.slice(source.indexOf('function QamBrowserV7'),source.indexOf('function StablePreviewArtV81')).includes('records[i]'));
assert(source.includes("activeItem?.type==='playlist'?'get_playlist_items'"));assert(source.includes('pageFocusPending.current=next>page?1:0'));assert(!source.slice(source.indexOf('function PagedCatalogV5('),source.indexOf('function BookDetailV75(')).includes('scroller.scrollTop=0'));
assert.equal(source,fs.readFileSync(path.join(__dirname,'../dist/index.js'),'utf8'));
console.log('PASS: spatial four-way navigation, top-boundary Decky handoff, account/boundaries/wrapped rows, exact native leaf, conditional scrolling; album ownership, late hydration/path refresh, sibling book covers, seed isolation, decode failure; All Music opens without playback; src/dist match.');
})().catch(e=>{console.error(e);process.exitCode=1});
