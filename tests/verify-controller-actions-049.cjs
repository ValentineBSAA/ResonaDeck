const fs=require('fs'), vm=require('vm'), assert=require('node:assert/strict');
const src=fs.readFileSync('src/index.js','utf8');
const dist=fs.readFileSync('dist/index.js','utf8');
assert.equal(src,dist);assert(src.includes("const RD_VERSION = '1.0.0'"));
const block=(a,b)=>{const i=src.indexOf(a),j=src.indexOf(b,i+a.length);assert(i>=0&&j>i,`missing ${a}`);return src.slice(i,j)};
const h=(type,props,...children)=>({type,props:props||{},children:children.flat(Infinity).filter(x=>x!==undefined&&x!==null&&x!==false)});
const walk=n=>!n||typeof n!=='object'?[]:[n,...(n.children||[]).flatMap(walk)];
let directions=[],closeCount=0,menuCount=0,previewCount=0,playCount=0;
const ctx={h,R:{useRef:v=>({current:v}),useEffect:()=>{}},DFL:{Focusable:'focusable',DialogButton:'button'},ControlV5:p=>h('button',p,...p.children),
 rdQamDirectionalV7:(e,t)=>{directions.push(t);return true;},rdQamNativeFocusV934:()=>true,rdQamRootV7:()=>null,
 rdV948PaintQueueGlass:()=>{},rdItemKeyV5:x=>x.ratingKey,rdFmtMsV75:()=>'',rdFocusElementV5:()=>{},
 rdDispatchQamNavigateV912:()=>{},roleInfo:()=>({label:'Music'}),
 audioEngine:{bookContext:null,loadIndex:()=>{},removeAt:()=>{}},setTimeout:()=>1,clearTimeout:()=>{},
 rdMediaTypeV5:x=>x?.type||'album',rdRoleV940:()=> 'music',rdCardGlassStyleV940:()=>({}),rdSkinV940:()=>h('span',{}),
 ArtworkV5:()=>h('img',{}),rdArtPathForRoleV83:()=>'',rdArtModeV5:()=>''};
vm.createContext(ctx);
vm.runInContext(block('// 0.9.48: Own the visible paint','// 0.9.34: canvas palette'),ctx);
const queue=[{ratingKey:'a',title:'Current'},{ratingKey:'b',title:'Upcoming'}];
const tree=ctx.QamMusicQueueDrawerV912({snap:{index:0,queue},cur:{libraryRole:'music',artistRatingKey:'artist1',albumRatingKey:'album1'},onClose:()=>closeCount++});
const nodes=walk(tree);const byAttr=(attr,key)=>nodes.find(n=>n.props?.[attr]===key);
assert.equal(tree.type,'focusable');tree.props.onCancel({preventDefault(){},stopPropagation(){}});assert.equal(closeCount,1);
const artist=byAttr('data-rd-qam-queue-action','artist');const album=byAttr('data-rd-qam-queue-action','album');const close=byAttr('data-rd-qam-queue-action','close');
assert(artist&&album&&close);
artist.props.onGamepadDirection({detail:{button:12}});assert.equal(directions.pop().right,'[data-rd-qam-queue-action="album"]');
close.props.onGamepadDirection({detail:{button:11}});assert.equal(directions.pop().left,'[data-rd-qam-queue-action="album"]');
close.props.onGamepadDirection({detail:{button:10}});assert.equal(directions.pop().down,'[data-rd-qam-queue-row="0"]');
const row=byAttr('data-rd-qam-queue-row','0');row.props.onGamepadDirection({detail:{button:9}});assert.equal(directions.pop().up,'[data-rd-qam-queue-action="close"]');
const remove=byAttr('data-rd-qam-queue-remove','1');remove.props.onGamepadDirection({detail:{button:11}});assert.equal(directions.pop().left,'[data-rd-qam-queue-row="1"]');
close.props.onClick();assert.equal(closeCount,2);
vm.runInContext(block('const RD_PREVIEW_HOLD_MS_V930=','function rdPickContinueIndexV930'),ctx);
const card=ctx.QamHoldCardV930({item:{ratingKey:'1',title:'Example'},role:'music',index:0,onPlay:()=>playCount++,onPreview:()=>previewCount++,onActions:()=>menuCount++});
card.props.onClick();assert.equal(playCount,1);
card.props.onSecondaryButton();assert.equal(menuCount,1);assert.equal(previewCount,0);
card.props.onOptionsButton();assert.equal(menuCount,2);
card.props.onKeyDown({key:'x',repeat:false});assert.equal(menuCount,3);
assert(src.includes("if(!cur)return h('div',{className:'rd-v7-qam-now rd-v80-qam-now rd-v80-now-empty rd-v949-idle'}"));
assert(src.includes("if(!snap?.current)"));
assert(src.includes("await audioEngine.setQueue(tracks,0,'music',next)"));
assert(src.includes("const [actionItem,setActionItem]"));
assert(src.includes("actionItem?h(DFL.Focusable,{'flow-children':'down',className:'rd-v949-action-menu"));
console.log('PASS 0.9.49: queue header reachability and cancel, row focus, X/Options menu dispatch, idle bypass, no-current bulk queue');
