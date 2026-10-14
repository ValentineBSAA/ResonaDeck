const fs=require('node:fs'),assert=require('node:assert/strict'),vm=require('node:vm');
const src=fs.readFileSync('src/index.js','utf8');
const part=(a,b)=>{const i=src.indexOf(a),j=src.indexOf(b,i+a.length);assert(i>=0&&j>i,`missing ${a}`);return src.slice(i,j)};
assert(src.includes('0.9.49'));
const css=part('/* 0.9.34: album-derived dark', '.rd-root.rd-v7-qam .rd-v930-queue-scroll');
assert(css.includes('var(--rd-art-surface'),'Color surface must be art-derived');
assert(css.includes('var(--rd-art-glow'),'Cover glow must be art-derived');
assert(css.includes('z-index:1'),'Keep player controls above backdrop');
assert(!css.includes('91% 35%')&&!css.includes('83%,#0b203e'),'No forced-neon palette');
const library=part('const RD_ART_NEUTRAL_V934=', 'function useArtworkAccentV930(');
const get=vm.runInNewContext(library+';({accent:rdArtworkAccentV930,palette:rdArtworkPaletteV934})');
const makePixels=(r,g,b)=>{const arr=new Uint8ClampedArray(48*48*4);for(let i=0;i<arr.length;i+=4){arr[i]=r;arr[i+1]=g;arr[i+2]=b;arr[i+3]=255;}return {data:arr};};
for(const rgb of [[5,50,180],[180,25,35],[120,30,140],[22,88,54]]){
 const a=get.accent(makePixels(...rgb)),p=get.palette(a);
 assert.match(a,/^rgb\(/);assert.match(p.surface,/^hsl\(/);assert.match(p.glow,/^hsl\(/);
 assert(!p.surface.includes('91% 35%'));
}
assert.notEqual(get.palette('rgb(5,50,180)').surface,get.palette('rgb(180,25,35)').surface);
assert.equal(get.accent(makePixels(5,5,5)),'#38556e');
const browser=part('function QamBrowserV7(){','function StablePreviewArtV81(');
assert(!browser.includes('PREVIEW SELECTED'),'Remove unwanted button');
assert(!browser.includes('rd-v930-browse-hint'),'Remove leftover hint');
assert(browser.includes('onPreview:()=>'),'Hold preview must remain');
assert(src.includes('onSecondaryButton:()=>'),'Secondary preview must remain');
console.log('PASS 0.9.34: source-honoring palettes, red/blue/purple/green identity, UI legibility layering, no stray Preview button, hold/secondary preserved');
