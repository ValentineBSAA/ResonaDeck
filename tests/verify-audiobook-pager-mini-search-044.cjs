const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const src=fs.readFileSync('src/index.js','utf8'),dist=fs.readFileSync('dist/index.js','utf8');
assert.equal(src,dist,'Source and Decky-installed runtime must match');
assert.match(src,/function ManagerBookPagerControlV944/);
for(const id of ['data-rd-v929-catalog-pager','data-rd-v929-chapter-pager','data-rd-v929-saved-pager']) {
  assert.match(src,new RegExp('ManagerBookPagerControlV944.*'+id));
}
assert.match(src,/\.rd-v75-full-pager \.rd-v944-book-pager>\.rd-v941-control-skin/);
assert.doesNotMatch(src.slice(src.indexOf('function ReadyQamV7('),src.indexOf('function ManagerV7()')),/h\(QamMiniSearchV944\)/,'Quick Menu search must no longer be mounted');
assert.match(src,/data-rd-qam-search-field/);
assert.match(src,/function QamKeyboardV944/);
assert.doesNotMatch(src.slice(src.indexOf('function QamMiniSearchV944'),src.indexOf('function ReadyQamV7')),/DFL\.TextField|<input|createElement\(['"]input/,'Quick search must not invoke native Steam text entry');
const h=(type,props,...children)=>({type,props:props||{},children:children.flat(Infinity).filter(x=>x!==null&&x!==false&&x!==undefined)});
const walk=x=>x&&typeof x==='object'?(typeof x.type==='function'?walk(x.type(x.props)):[x,...(x.children||[]).flatMap(walk)]):[];
const states=[],refs=[];let stateIndex=0,refIndex=0;
const R={useState(initial){const id=stateIndex++;if(!(id in states))states[id]=initial;return [states[id],v=>{states[id]=typeof v==='function'?v(states[id]):v;}];},useRef(initial){const id=refIndex++;if(!(id in refs))refs[id]={current:initial};return refs[id];},useEffect(){} };
const requests=[];let chosen=0;
const cached={albums:[{ratingKey:'111',title:'Music One',artist:'Artist',libraryRole:'music'},{ratingKey:'222',title:'Book Two',artist:'Narrator',libraryRole:'audiobooks'}],tracks:[{ratingKey:'333',title:'Song Three',libraryRole:'music'}],artists:[]};
const ctx={h,R,DFL:{Focusable:'div'},ControlV5:'control',
 rdSkinV940:()=>h('skin',{}),rdLabelV940:x=>h('label',{},x),rdRoleV940:x=>x,rdKindForRoleV5:r=>r,
 rdItemKeyV5:x=>x.ratingKey,roleInfo:r=>({label:r}),rdQamDirectionalV7:()=>true,
 rdQamNativeFocusV934:()=>false,rdFocusElementV5:()=>false,rdQamRevealV92:()=>{},rdDir:()=>10,
 rdConsumeDirectionV80:()=>true,RD_DIR_LEFT:11,RD_DIR_RIGHT:12,RD_DIR_UP:9,RD_DIR_DOWN:10,
 rdQamFocusV7:()=>true,onceToast:()=>{},setTimeout:()=>{},document:{querySelector:()=>null},
 async call(...args){requests.push(args);if(args[0]==='search_cached')return cached;return {artists:[],albums:[],tracks:[],success:true};},
 async rdQuickPlayCollectionV930(){chosen++;return true;},async rdOpenMediaV5(){chosen++;}
};
const start=src.indexOf('function rdMiniSearchResultsV944('),stop=src.indexOf('function ReadyQamV7(',start);
assert(start>=0&&stop>start);
vm.createContext(ctx);vm.runInContext(src.slice(start,stop)+'\nthis.search=QamMiniSearchV944;this.keyboard=QamKeyboardV944;this.pick=rdMiniSearchResultsV944;',ctx);
function render(){stateIndex=0;refIndex=0;return walk(ctx.search());}
function keyboardNodes(){return render().filter(x=>typeof x.props['data-rd-qam-key']==='string');}
function key(label){return keyboardNodes().find(x=>x.props['aria-label']===label);}
let nodes=render();
const toggle=nodes.find(x=>x.props['data-rd-qam-search-toggle']==='1');assert(toggle);toggle.props.onClick();
nodes=render();assert(nodes.some(x=>x.props['data-rd-qam-search-field']==='1'));
assert(key('Type q'),'built-in keyboard renders letter keys');
key('Type t').props.onClick();key('Type h').props.onClick();key('Type e').props.onClick();
let field=render().find(x=>x.props['data-rd-qam-search-field']==='1');
assert.match(field.props['aria-label'],/the/,'search text accumulated without native keyboard');
key('Backspace').props.onClick();field=render().find(x=>x.props['data-rd-qam-search-field']==='1');
assert.match(field.props['aria-label'],/th\. Open keyboard/,'Backspace removes last character');
key('Type e').props.onClick();
key('Space').props.onClick();key('Type a').props.onClick();
field=render().find(x=>x.props['data-rd-qam-search-field']==='1');assert.match(field.props['aria-label'],/the a\. Open keyboard/);
key('CLEAR').props.onClick();field=render().find(x=>x.props['data-rd-qam-search-field']==='1');assert.match(field.props['aria-label'],/Search text/);
key('Type t').props.onClick();key('Type h').props.onClick();key('Type e').props.onClick();
// Nested keyboard keys, not native TextField. Search then render results.
(async()=>{
  key('Search Plex').props.onClick();
  await new Promise(resolve=>setImmediate(resolve));
  nodes=render();
  const results=nodes.filter(x=>typeof x.props['data-rd-qam-search-result']==='string');
  assert.equal(results.length,2);
  assert.equal(requests[0][0],'search_cached');assert.equal(requests[0][1],'the');assert.equal(requests[0][2],'everything');
  assert(!requests.some(x=>x[0]==='search'),'two cached matches avoid unnecessary network search');
  await results[0].props.onClick();assert.equal(chosen,1);
  assert.equal(ctx.pick({albums:Array.from({length:10},(_,i)=>({ratingKey:String(i),title:String(i)}))}).length,2);
  assert.equal(keyboardNodes().length,0,'keyboard closes after Search, leaving results usable');
  nodes.find(x=>x.props['data-rd-qam-search-toggle']==='1').props.onClick();
  assert.equal(render().some(x=>x.props['data-rd-qam-search-field']==='1'),false);
  console.log('PASS 0.9.45 audiobook pager + controller-native-free QAM keyboard and Plex search');
})().catch(e=>{console.error(e);process.exitCode=1});
