const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const src=fs.readFileSync('src/index.js','utf8');
const segment=(start,end)=>{const i=src.indexOf(start),j=src.indexOf(end,i+start.length);assert(i>=0&&j>i,`missing ${start}/${end}`);return src.slice(i,j)};
const source=segment('function rdManagerDetailKindV946(', 'function PlaylistBrowserV5()');
const context={
  R:{useRef:()=>({current:null}),useEffect:()=>{},useState:v=>[v,()=>{}]},
  rdMediaTypeV5:x=>String(x?.type||x?.mediaType||'').toLowerCase(),
  h:(type,props,...children)=>({type,props:props||{},children}),
  DFL:{Focusable:'Focusable'},
  BookDetailV75:'BookDetailV75',AudiobookGroupDetailV75:'AudiobookGroupDetailV75',MediaDetailV5:'MediaDetailV5',TrackDetailV946:'TrackDetailV946',
  ManagerGlassControlV941:'Glass',ArtworkV5:'Artwork',rdArtPathV5:()=>'',rdArtModeV5:()=>'',roleInfo:()=>({label:'Music'}),rdDetailRpcV945:()=>Promise.resolve({}),rdOpenMediaV5:()=>{},
  window:{setTimeout:()=>0,clearTimeout:()=>{}},
};
vm.createContext(context);vm.runInContext(source,context);
const route=(role,view,type,semanticType)=>{const el=context.ManagerDetailRouteV946({item:{ratingKey:'r1',type,semanticType},role,view,onBack:()=>{}});return typeof el.children[0].type==='function'?el.children[0].type.name:el.children[0].type};
assert.equal(route('audiobooks','books','album','book'),'BookDetailV75');
assert.equal(route('audiobooks','authors','artist',null),'AudiobookGroupDetailV75');
assert.equal(route('audiobooks','collections','collection',null),'AudiobookGroupDetailV75');
assert.equal(route('audiobooks','continue','album','book'),'BookDetailV75');
assert.equal(route('audiobooks','tracks','track',null),'TrackDetailV946');
assert.equal(route('music','albums','album',null),'MediaDetailV5');
assert.equal(route('music','tracks','track',null),'TrackDetailV946');
assert.equal(route('music','artists','artist',null),'MediaDetailV5');
assert.equal(route('podcasts','artists','artist',null),'MediaDetailV5');
assert.equal(route('other','tracks','track',null),'TrackDetailV946');
assert(src.includes("h(RoleCatalogPageV5,{key:'music',role:'music'})"),'Music role resets');
for(const role of ['audiobooks','podcasts','other'])assert(src.includes(`h(RoleCatalogPageV5,{key:'${role}',role:'${role}'})`),`Keyed ${role}`);
const now=segment('function NowPlayingV5({onBack})','let rdVolumeSaveTimerV77');
assert(now.indexOf('usePlayerArtworkV6(cur,')<now.indexOf('if(!cur)return'),'Always invoke artwork hook before idle early return');
assert.equal((now.match(/usePlayerArtworkV6\(/g)||[]).length,1,'No conditional second call');
const media=segment('function MediaDetailV5(', '/* 0.9.46: Full Manager must dispatch');
assert(media.includes("void rdDetailRpcV945('get_children',key,8000).then"),'Artist related independently');
assert(!media.includes('Promise.all([primary,related])'),'Never wait for both Plex endpoints');
const home=segment('function HomePageV5(', 'function SearchGridV5(');
assert(home.includes('await Promise.allSettled(jobs.map'),'Home updates each shelf');
assert(!home.includes('const jobs=await Promise.all(['),'Home does not block on all libraries');
const search=segment('function SearchPageV5(', 'function ManagerNowBarV5(');
assert(search.includes("setSource(local?'Living Library':'Checking Plex')"),'Local results first');
assert(search.includes('void Promise.race([call(\'search\''),'Server search nonblocking');
assert.equal(src,fs.readFileSync('dist/index.js','utf8'),'Source and install frontend identical');
console.log('PASS Full Manager integration routing (10 kinds), Now Playing hook order, keyed sections, independent Plex queries, progressive home/search, source/dist sync');
