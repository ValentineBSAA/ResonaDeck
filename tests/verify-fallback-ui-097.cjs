const fs=require('fs'),vm=require('vm'),assert=require('assert/strict'),path=require('path');
const src=fs.readFileSync(path.join(__dirname,'../src/index.js'),'utf8');
const dist=fs.readFileSync(path.join(__dirname,'../dist/index.js'),'utf8');
assert(src.includes("const RD_VERSION = '1.0.8'"));
for(const [name,file] of [['RD_FALLBACK_MUSIC_V97','fallback-music.webp'],['RD_FALLBACK_AUDIOBOOKS_V97','fallback-audiobooks.webp'],['RD_FALLBACK_PODCASTS_V97','fallback-podcasts.webp']]){
  const m=src.match(new RegExp(`const ${name} = '(data:image\/webp;base64,[A-Za-z0-9+/=]+)'`));
  assert(m && m[1].length>20000,`${name} missing/too small`);
  const embedded=Buffer.from(m[1].split(',')[1],'base64'),asset=fs.readFileSync(path.join(__dirname,'../assets',file));
  assert(embedded.equals(asset),`${name} does not exactly embed ${file}`);
}
assert(src.includes("store={version:97"),'artwork store generation was not bumped');
assert(src.includes('rdArtworkStoreV81().kick?.(Number(r.registryRevision||0))'),'status does not kick ordered artwork polling');
assert(src.includes("terminalState=rec?.state==='failed'||rec?.state==='fallback'"),'fallback state is not rendered');
assert(src.includes("rdFallbackArtworkV97(role)"),'bundled fallback is not wired into ArtworkV5');

// Execute candidate selection to make sure image retries cannot corrupt data: URLs.
const start=src.indexOf("function rdArtworkCandidateV93("); assert(start>=0);
const rest=src.slice(start); const end=rest.slice(1).search(/\nfunction /); const block=end<0?rest:rest.slice(0,end+1);
const ctx={}; vm.createContext(ctx); vm.runInContext(block,ctx);
const data='data:image/webp;base64,AAAA';
assert.equal(ctx.rdArtworkCandidateV93({state:'fallback',imageAttempt:2},data),data);
assert.equal(ctx.rdArtworkCandidateV93({state:'failed',imageAttempt:2},data),data);
assert.equal(ctx.rdArtworkCandidateV93({state:'ready',url:'http://127.0.0.1/a',imageAttempt:2},''),'http://127.0.0.1/a?rd_image_retry=2');
assert.equal(src,dist,'src/dist mismatch');
console.log('PASS: locked fallback artwork is embedded, fallback state renders, live-update kick/store generation are present, data URLs survive retry attempts, and src/dist match.');
