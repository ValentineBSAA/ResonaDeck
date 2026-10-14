const assert=require('node:assert/strict');
const fs=require('node:fs');
const src=fs.readFileSync('src/index.js','utf8'),dist=fs.readFileSync('dist/index.js','utf8');
assert.equal(src,dist);
const from=src.indexOf('/* 0.9.39: CSS Loader / white Steam theme isolation.');
const to=src.indexOf('.rd-root.rd-v7-qam .rd-v930-queue-scroll',from);
assert(from>0&&to>from,'Theme-isolated glass CSS exists');
const css=src.slice(from,to);
for(const token of ['.rd-v939-glass-skin','position:absolute!important','--rd-v939-top',
  '--rd-v939-bottom','--rd-v939-icon','rd-v938-restart','rd-v938-shuffle','rd-v938-repeat',
  'rd-v938-queue','rd-v938-prev','rd-v938-next','rd-v938-play','rd-v80-volume',
  'outline:3px solid var(--rd-focus)','transition:none!important']){
  assert(css.includes(token),`Missing ${token}`);
}
for(const token of ['function rdV939PaintGlass','RD_GLASS_PAINT_V939',"setProperty('background',RD_GLASS_PAINT_V939,'important')",
   'function rdV939PaintIcon','function rdV939VolumeGlass'])assert(src.includes(token),token);
assert(src.includes("onClick:()=>audioEngine.restartContextual()"));
assert(src.includes('function rdQamDirectionalV7('));
assert(src.includes('function useArtworkPaletteV935('));
console.log('PASS 0.9.39: owned tinted glass surfaces, CSS Loader isolation, gold focus and playback callbacks preserved');
