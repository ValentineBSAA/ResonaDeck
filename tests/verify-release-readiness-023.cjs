const fs=require('fs');
const path=require('path');
const root=path.resolve(__dirname,'..');
const src=fs.readFileSync(path.join(root,'src/index.js'),'utf8');
const dist=fs.readFileSync(path.join(root,'dist/index.js'),'utf8');
const main=fs.readFileSync(path.join(root,'main.py'),'utf8');
const backend=fs.readFileSync(path.join(root,'resonadeck_backend.py'),'utf8');
function ok(v,msg){if(!v){console.error('FAIL:',msg);process.exitCode=1;}else console.log('PASS:',msg);}
ok(src.includes("const RD_VERSION = '1.0.0';"),'frontend version 0.9.49');
ok(src===dist,'src/dist byte-identical');
ok(src.includes('RD_RPC_RETRYABLE_V923'),'bounded read RPC retry present');
ok(src.includes('rdResetManagerWorkspaceV923'),'manager top/focus reset present');
ok(src.includes('pageFocusPending.current=next>page?1:0'),'QAM page focus handoff present');
ok(backend.includes('pms-read-recover'),'Plex stale-endpoint recovery present');
ok(backend.includes('async def recover_connection'),'explicit connection recovery present');
ok((main.match(/async def set_reading_list/g)||[]).length===1,'reading-list forward is not duplicated');
ok(main.includes('async def recover_connection'),'bootstrap exposes connection recovery');
if(process.exitCode)process.exit(process.exitCode);
