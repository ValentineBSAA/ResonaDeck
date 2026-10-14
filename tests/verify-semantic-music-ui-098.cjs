const fs=require('fs'),assert=require('assert');
const src=fs.readFileSync('src/index.js','utf8');
const dist=fs.readFileSync('dist/index.js','utf8');
assert.strictEqual(src,dist,'src/dist differ');
assert(src.includes("const RD_VERSION = '1.0.0'"));
assert(src.includes("['tracks','All Tracks']"),'Music All Tracks tab missing');
assert(src.includes("inspect_library"),'semantic count inspector missing');
assert(src.includes('semanticCounts'),'semantic count UI missing');
console.log('PASS: 0.9.8 frontend exposes All Tracks and Plex semantic counts with src/dist synchronized.');
