const fs=require('node:fs'),assert=require('node:assert/strict');
const src=fs.readFileSync('src/index.js','utf8'),dist=fs.readFileSync('dist/index.js','utf8');
const plugin=JSON.parse(fs.readFileSync('plugin.json','utf8'));
const pkg=JSON.parse(fs.readFileSync('package.json','utf8'));
assert.equal(src,dist,'Decky frontend must be the same as tested source');
assert.equal(plugin.version,'1.0.8');assert.equal(pkg.version,'1.0.8');
assert(src.includes("const RD_VERSION = '1.0.8'"));
for(const role of ['music','audiobooks','podcasts','other']) {
 assert(src.includes(`.rd-root .rd-v940-role-${role}`),`${role} must have an independent color identity`);
 assert(src.includes(`rd-v940-role-`),'role-specific card/tab decoration missing');
}
assert(src.includes('function rdCardGlassStyleV940('),'per-cover card color sampling must be present');
assert(src.includes('function rdSkinV940('),'native Steam controls must own internal glass');
assert(src.includes("className:'rd-v939-glass-skin',ref:rdV939PaintGlass"),'0.9.39 playback glass must be preserved');
assert(src.includes("extraClass==='rd-v940-shuffle-face'?h('span',{className:'rd-v940-shuffle-orbit'"),'Shuffle snake must be separate from native CSS pseudo-elements');
const snake=src.slice(src.indexOf('/* 0.9.40: restore the perimeter snake'),src.indexOf('.rd-root.rd-v7-qam .rd-v930-queue-scroll{'));
for(const requirement of ['rdV940ShuffleGlassSnake','offset-path:inset(0 round 8px)','1.85s linear infinite','var(--rd-v939-icon','prefers-reduced-motion:reduce','active .rd-v940-shuffle-runner','pointer-events:none']){
 assert(snake.includes(requirement),`missing snake requirement ${requirement}`);
}
assert(src.includes("rdControlFaceV938('⤮',s.shuffle?'SHUFFLE · ON':'SHUFFLE · OFF','rd-v940-shuffle-face')"),'ON/OFF still controlled by engine');
assert(src.includes('onClick:()=>audioEngine.toggleShuffle()'),'native shuffle callback untouched');
console.log('PASS 0.9.40: 4 category palettes, artwork cards, CSS Loader-resistant glass, independent active Shuffle snake, reduced motion, native input preserved');
