const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const src=fs.readFileSync('src/index.js','utf8');
const dist=fs.readFileSync('dist/index.js','utf8');
assert.equal(src,dist,'source and installed frontend must match');
const h=(type,props,...children)=>({type,props:props||{},children:children.flat(Infinity).filter(x=>x!==null&&x!==false&&x!==undefined)});
const walk=(node)=>node&&typeof node==='object'?[node,...(node.children||[]).flatMap(walk)]:[];
const calls=[];
const ctx={h,DFL:{DialogButton:'button',Focusable:'div',TextField:'input'},R:{useState(v){return [v,()=>{}]},useEffect(){}},
 useEngine:()=>({current:{title:'Vera Track',artist:'Vera Static',libraryRole:'music'},state:'paused',artUrl:'cover',kind:'music'}),
 rdGreetingV5:()=> 'LATE NIGHT LISTENING',rdManagerDirectionalV910:()=>true,usePlayerArtworkV6:()=>null,
 rdManagerPaletteV941:()=>({}),PlayerArtworkV6:()=>h('img',{}),
 ManagerGlassControlV941:({children,...props})=>h('button',props,children),
 rdMergeUniqueV5:()=>[],audioEngine:{play:()=>calls.push('play'),pause:()=>calls.push('pause')},
 ShelfV5:()=>null,MediaDetailV5:()=>null,roleInfo:()=>({label:'Music'}),call:()=>Promise.resolve({}),
 rdRoleV940:()=> 'music',rdSavedManagerPageV923:()=> 'home'};
const section=(start,end)=>src.slice(src.indexOf(start),src.indexOf(end,src.indexOf(start)));
vm.createContext(ctx);
vm.runInContext(section('function HomePageV5(', '\nfunction SearchGridV5(')+'\nthis.Home=HomePageV5;',ctx);
const tree=ctx.Home({auth:{activeUser:{title:'Deck'}},onNavigate:()=>{},onNow:()=>calls.push('now')});
const nodes=walk(tree),hero=nodes.find(n=>n.props?.className==='rd-v943-hero-target');
assert(hero,'full manager listening banner must be native-focusable');
assert.equal(hero.props.focusable,true);assert.equal(typeof hero.props.onGamepadDirection,'function');
hero.props.onClick();assert.deepEqual(calls,['play'],'A on banner must play/resume');
const now=nodes.find(n=>String(n.props?.className||'').includes('rd-v943-hero-open'));
assert(now,'now playing control exists');now.props.onClick();assert.deepEqual(calls,['play','now']);
assert(nodes.some(n=>String(n.props?.className||'').includes('rd-v943-hero-play')),'play/pause remains a separate glass control');
const essential=['rd-v943-search-field','rd-v943-search-scopes','rd-v943-search-submit','rd-v943-library-entry-skin','rd-v943-role-option','rd-v943-hero-target-skin'];
for(const c of essential)assert(src.includes(c),'missing '+c);
const bar=section('function NowBarV7(', '\nfunction StatusBarV7(');
assert.equal((bar.match(/rd-v924-mini-progress/g)||[]).length,1,'only one real mini-player timeline');
assert(src.includes('.rd-root.rd-v941-manager .rd-v924-nowbar::before{content:none!important;display:none!important'), 'legacy progress overlay disabled');
assert(src.includes('rdV940ShuffleGlassSnake'),'Quick Menu shuffle orbit preserved');
assert(src.includes('function rdQamNativeFocusV934'), 'QAM focus preserved');
console.log('PASS 0.9.45: Home focus/A and separate controls, Search/Library glass, one timeline, preserved QAM');
