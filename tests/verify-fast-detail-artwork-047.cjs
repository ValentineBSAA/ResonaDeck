const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const src=fs.readFileSync('src/index.js','utf8'),dist=fs.readFileSync('dist/index.js','utf8');
assert.equal(src,dist);
const from=src.indexOf('function rdArtworkFastCoverV947('),to=src.indexOf('function ArtworkV5(',from);
assert(from>0&&to>from);
const records=new Map([
 ['other|song-17|square-card',{state:'ready',url:'http://localhost/cached-song-cover.jpg'}],
 ['music|album-22|square-card',{state:'ready',url:'http://localhost/cached-album-cover.jpg'}],
 ['music|album-33|square-card',{state:'failed',url:'http://localhost/broken-cover.jpg'}],
]);
const ctx={rdArtworkRatingKeyV81:(item)=>item.artOwner||item.ratingKey,rdArtworkStoreV81:()=>({records})};
vm.createContext(ctx);vm.runInContext(src.slice(from,to)+'\nthis.fast=rdArtworkFastCoverV947;',ctx);
assert.equal(ctx.fast({ratingKey:'song-17',title:'Grok Put Her In A Micro...'},'other','/song17/thumb'),'http://localhost/cached-song-cover.jpg');
assert.equal(ctx.fast({ratingKey:'song-18',title:'Another song'},'other','/song18/thumb'),'','cannot leak another track cover');
assert.equal(ctx.fast({ratingKey:'song-17',artRegistryIdentity:'other|song-17|square-card',artRegistryState:'ready',cachedArtUrl:'http://localhost/current-cover.jpg'},'other'), 'http://localhost/current-cover.jpg');
assert.equal(ctx.fast({ratingKey:'album-22',title:'Album',artOwner:'album-22'},'music','/album22/thumb'),'http://localhost/cached-album-cover.jpg');
assert.equal(ctx.fast({ratingKey:'album-33',title:'Failed',artOwner:'album-33'},'music'),'','failed cache entry must never be shown');
const ready=src.slice(src.indexOf('function ReadyQamV7('),src.indexOf('class ManagerRecoveryBoundaryV946'));
assert(!ready.includes('h(QamMiniSearchV944)'), 'do not mount cumbersome Quick Search');
assert(ready.includes('h(QamNowV7)'), 'retain Quick Menu player');
assert(ready.includes('h(QamBrowserV7)'), 'retain library');
assert(src.includes("down:'[data-rd-qam-launch=\"1\"]'"),'pagination focus should lead to Full Manager launch');
assert(src.includes('rd-v940-shuffle-runner'),'keep Shuffle snake');
assert(src.includes('rd-v947')||src.includes('0.9.49'),'version present');
assert(src.includes('0.9.47: Final native-control isolation'),'Full Manager consistency styling included');
console.log('PASS 0.9.47 cached cover reuse, no cross-track image leak, Quick Search removed, glass and Shuffle preserved');
