const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const src=fs.readFileSync('src/index.js','utf8');
const start=src.indexOf('// 0.9.35: separate artwork-derived roles');
const end=src.indexOf('function QamNowV7(){',start);
assert(start>0&&end>start,'New palette logic exists');
const originalStart=src.indexOf('const RD_ART_NEUTRAL_V934=');
const code=src.slice(originalStart,end);
const context={R:{useState:()=>{},useEffect:()=>{}},Image:function(){}};
vm.createContext(context);
vm.runInContext(code,context);
const samples=(colors)=>{
 const data=new Uint8ClampedArray(colors.length*4);
 colors.forEach(([r,g,b],i)=>{data[i*4]=r;data[i*4+1]=g;data[i*4+2]=b;data[i*4+3]=255;});
 return {data};
};
const solid=(r,g,b)=>samples(Array.from({length:512},()=>[r,g,b]));
const blue=context.rdArtworkPaletteFromPixelsV935(solid(16,91,219));
const red=context.rdArtworkPaletteFromPixelsV935(solid(200,38,57));
const purple=context.rdArtworkPaletteFromPixelsV935(solid(103,40,175));
const forest=context.rdArtworkPaletteFromPixelsV935(solid(31,135,68));
for(const palette of [blue,red,purple,forest]){
 for(const field of ['deep','surface','secondary','glow','accent','highlight','controlTop','controlBottom','controlAlt','border']){
  assert.match(palette[field],/^hsl\(\d+ \d+% \d+%\)$/,`missing ${field}`);
 }
 assert.notEqual(palette.deep,palette.surface);
 assert.notEqual(palette.surface,palette.controlTop);
 assert.notEqual(palette.controlTop,palette.controlBottom);
 assert.notEqual(palette.accent,palette.highlight);
}
assert.notEqual(blue.surface,red.surface);
assert.notEqual(purple.surface,red.surface);
assert.notEqual(forest.surface,blue.surface);
const mixed=context.rdArtworkPaletteFromPixelsV935(samples([
 ...Array.from({length:500},()=>[12,99,207]),
 ...Array.from({length:220},()=>[220,128,23])
]));
assert.notEqual(mixed.secondary,mixed.surface,'mixed artwork must have a separate secondary hue');
assert.notEqual(mixed.secondary,blue.secondary,'secondary hue uses actual second-color pixels');
const neutral=context.rdArtworkPaletteFromPixelsV935(solid(30,30,30));
assert.match(neutral.surface,/^hsl\(/,'grayscale still has fallback');
const css=src.slice(src.indexOf('/* 0.9.38 DEV:'),src.indexOf('.rd-root.rd-v7-qam .rd-v930-queue-scroll',src.indexOf('/* 0.9.38 DEV:')));
for(const rule of ['--rd-art-deep','--rd-art-secondary','--rd-art-highlight','--rd-art-control-top','--rd-art-control-bottom','rd-v912-secondary-controls','rd-v912-primary-controls','rd-v80-volume-track','rd-v80-now-progress','rd-v91-viz','rd-v80-qam-controls','rd-v912-queue-drawer','var(--rd-focus)'])assert(css.includes(rule),`Missing ${rule} in visual layer`);
assert(src.includes('artPalette=useArtworkPaletteV935(String(s.artUrl||\'\'))'));
assert(src.includes("'--rd-art-control-alt':artPalette.controlAlt"));
assert(src.includes('function rdQamDirectionalV7('),'controller navigation maintained');
assert(!css.includes('background:#ffffff')&&!css.includes('background:white'));
console.log('PASS 0.9.37: distinct and mixed palettes, scoped control tokens, progress/volume/viz colors, Steam focus retained');
