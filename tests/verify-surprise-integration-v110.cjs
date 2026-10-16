const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const src=fs.readFileSync('src/index.js','utf8');
const from=src.indexOf('function rdDiscoveryPickV11('),to=src.indexOf('function DiscoverySettingsV11(',from);assert(from>=0&&to>from);
const code=src.slice(from,to);
const tracks=Array.from({length:45},(_,i)=>({ratingKey:String(i+1),title:'Track '+(i+1),libraryRole:'music'}));
const events=[],toasts=[];
const db={state:{preferences:{category:'music',musicMode:'tracks',count:20,favoritesOnly:false,crossfade:0},favorites:[],recentIds:[]},async init(){},remember(rows){events.push(['remember',rows.length]);}};
let mode='music';
const engine={async setQueue(rows,index,kind,autoplay){events.push(['play',rows,index,kind,autoplay]);},async setBook(manifest,autoplay){events.push(['book',manifest,autoplay]);}};
const call=async(method,role,view,offset,limit)=>{
  if(method==='browse_cached'){
    if(role==='music'&&view==='albums')return {success:true,items:[{ratingKey:'album-X',title:'Album'}],total:1};
    if(role==='audiobooks')return {success:true,items:[{ratingKey:'book-1',title:'My Book'}],total:1};
    if(role==='podcasts')return {success:true,items:[{ratingKey:'episode-1',title:'My Podcast'}],total:1};
    if(role==='other')return {success:true,items:[{ratingKey:'other-1',title:'My Radio'}],total:1};
    return {success:true,items:tracks.slice(offset,offset+limit),total:45};
  }
  if(method==='get_children')return {success:true,tracks:[{ratingKey:'A',title:'Album Track A'},{ratingKey:'B',title:'Album Track B'}],items:[]};
  if(method==='get_book_manifest')return {success:true,manifest:{ratingKey:'book-1',files:[{ratingKey:'f1'}],title:'My Book'}};
  throw Error('Unexpected backend method '+method);
};
const context={RD_DISCOVERY_V11:db,rdDiscoveryItemV11:x=>x,rdDiscoveryPickV11:undefined,RD_DISCOVERY_ROLES_V11:['music','audiobooks','podcasts','other','all'],RD_DISCOVERY_NAMES_V11:{music:'Music',audiobooks:'Books',podcasts:'Podcasts',other:'More Audio'},audioEngine:engine,call,onceToast:(...x)=>toasts.push(x),Math,Set,Number,String,Boolean,Promise};vm.createContext(context);vm.runInContext(code,context);
(async()=>{
 await context.rdSurpriseMeV11();let e=events.find(x=>x[0]==='play');assert(e);assert.equal(e[1].length,20);assert.equal(new Set(e[1].map(x=>x.ratingKey)).size,20);assert.equal(e[3],'music');events.length=0;
 db.state.favorites=tracks.slice(0,6);db.state.preferences.favoritesOnly=true;await context.rdSurpriseMeV11();e=events.find(x=>x[0]==='play');assert.equal(e[1].length,6,'favorites-only cannot invent 20 favorites');events.length=0;db.state.preferences.favoritesOnly=false;
 db.state.preferences.musicMode='albums';await context.rdSurpriseMeV11();e=events.find(x=>x[0]==='play');assert.equal(e[1].length,2,'random album must play real child tracks, not album directory');events.length=0;
 db.state.preferences.category='audiobooks';await context.rdSurpriseMeV11();assert(events.some(x=>x[0]==='book'),'book must use real manifest and resumable player');events.length=0;
 db.state.preferences.category='podcasts';await context.rdSurpriseMeV11();e=events.find(x=>x[0]==='play');assert.equal(e[1].length,1);assert.equal(e[3],'podcast');events.length=0;
 db.state.preferences.category='other';await context.rdSurpriseMeV11();e=events.find(x=>x[0]==='play');assert.equal(e[1].length,1);assert.equal(e[1][0].libraryRole,'other');
 console.log('PASS: Surprise Me music 20 unique, favorites-only, full albums, real book manifests, podcasts and More Audio');
})().catch(e=>{console.error(e);process.exit(1)});
