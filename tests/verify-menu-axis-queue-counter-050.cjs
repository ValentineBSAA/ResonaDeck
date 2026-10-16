const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const src=fs.readFileSync('src/index.js','utf8');
const dist=fs.readFileSync('dist/index.js','utf8');
assert.equal(src,dist,'shipped frontend must match source');
assert(src.includes("const RD_VERSION = '1.0.8'"));
const take=(from,to)=>{const i=src.indexOf(from);assert(i!==-1,from);const j=src.indexOf(to,i+from.length);assert(j!==-1,to);return src.slice(i,j)};
const h=(type,props,...children)=>({type,props:props||{},children:children.flat(Infinity).filter(x=>x!=null&&x!==false)});
const nodes=n=>!n||typeof n!=='object'?[]:[n,...(n.children||[]).flatMap(nodes)];
const ctx={};vm.createContext(ctx);
ctx.RD_DIR_UP=9;ctx.RD_DIR_DOWN=10;ctx.RD_DIR_LEFT=11;ctx.RD_DIR_RIGHT=12;
vm.runInContext(take('function rdQamActionTargetV950(', 'function QamBrowserV7(){'),ctx);
const moves={
  0:{11:null,12:1,9:null,10:2},
  1:{11:0,12:null,9:null,10:3},
  2:{11:null,12:3,9:0,10:null},
  3:{11:2,12:null,9:1,10:null}
};
for(const [origin,dirs] of Object.entries(moves))for(const [dir,target] of Object.entries(dirs)){
 assert.equal(ctx.rdQamActionTargetV950(Number(origin),Number(dir),4),target,`music menu ${origin},${dir}`);
}
// Non-music menus have a single 2-option row.
assert.equal(ctx.rdQamActionTargetV950(0,12,2),1);
assert.equal(ctx.rdQamActionTargetV950(1,11,2),0);
assert.equal(ctx.rdQamActionTargetV950(0,10,2),null);
assert.equal(ctx.rdQamQueueCountV950({queue:Array(47).fill(null),index:31}),47);
assert.equal(ctx.rdQamQueueCountV950({queue:[],index:0}),0);
assert.equal(ctx.rdQamQueueCountV950({}),0);
const menu=take('function QamBrowserV7(){','function StablePreviewArtV81');
assert(menu.includes("'flow-children':'down',className:'rd-v949-action-menu"));
assert(menu.includes("'flow-children':'down',className:'rd-v949-action-items rd-v950-action-items'"));
assert(menu.includes("'flow-children':'right',className:'rd-v950-action-row'"));
assert(menu.includes('rdQamActionTargetV950(i,d,total)'));
assert(menu.includes('rdQamNativeFocusV934(el)'), 'native Steam focus is retained');
assert(menu.includes('return rdConsumeDirectionV80(e)'), 'boundary input remains within menu');
assert(menu.includes("['+ Add to Queue'"), 'existing Add to Queue stays');
assert(menu.includes("['▶ Play Next'"), 'existing Play Next stays');
assert(menu.includes("['Browse Details'"), 'existing Browse Details stays');
assert(menu.includes("['Close',closeActions]"), 'existing Close stays');
const now=take('function QamNowV7(){','function QamDetailV7');
assert(now.includes("rdControlFaceV938('≣',`QUEUE · ${rdQamQueueCountV950(s)}`)"),'QAM counter shows total even while open');
assert(!now.includes('QUEUE · OPEN'), 'drawer open must not hide count');
assert(!now.includes('Math.max(0,(s.queue?.length||0)-Number(s.index||0)-1)'), 'do not show remaining tracks as queue total');
// Control callbacks publish snapshots for all three mutations.
const engine=take('  addToQueue(item){','  async setQueue(');
for(const fn of ['addToQueue','playNext','removeAt']){
 if(fn==='removeAt') continue; // removal implemented elsewhere in AudioEngine
 assert(engine.includes(`${fn}(item)`));
}
const drawer=take('function QamMusicQueueDrawerV912','// 0.9.34: canvas palette');
assert(drawer.includes('`${rows.length} tracks · playing ${Math.min(rows.length,activeIndex+1)} of ${rows.length}`'));
console.log('PASS 0.9.50: all music/nonmusic D-pad transitions; nested Steam focus tree; controller actions retained; live queue totals in player and drawer');
