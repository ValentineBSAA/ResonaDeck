const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const root=path.resolve(__dirname,'..');
const src=fs.readFileSync(path.join(root,'src/index.js'),'utf8');
const dist=fs.readFileSync(path.join(root,'dist/index.js'),'utf8');
assert.strictEqual(src,dist,'source and installable frontend must match');
assert(src.includes('function rdWarmSearchTracksV944(payload)'));
assert(src.includes('rdWarmSearchTracksV944(local)')&&src.includes('rdWarmSearchTracksV944(net)'));
assert(src.includes("call('prepare_media',ready)"),'metadata preparation is deliberately asynchronous');
assert(src.includes("className:'rd-v944-now-detail'" )||src.includes("?'rd-v944-now-detail'"),'now-playing detail marker exists');
assert(src.includes('rd-v944-now-detail .rd-v924-shell'),'full detail uses reserved footer space');
assert(src.includes('rd-v924-mini-play'),'mini player transport remains available');
assert(src.includes('rd-v940-shuffle-runner'),'existing shuffle animation remains');
const cut=(a,b)=>{const x=src.indexOf(a),y=src.indexOf(b,x);assert(x>=0&&y>x,`Missing ${a} => ${b}`);return src.slice(x,y)};
const prefetchCode=cut('function rdWarmSearchTracksV944(payload)','function SearchPageV5()');
const warmed=[];
const warmContext={rdMediaTypeV5:item=>item.semanticType||item.type,call:(method,rows)=>{warmed.push({method,rows});return Promise.resolve({success:true})}};
vm.createContext(warmContext);vm.runInContext(prefetchCode+'\nthis.warm=rdWarmSearchTracksV944;',warmContext);
const tracks=[...Array(12)].map((_,i)=>({ratingKey:String(i+1),semanticType:'track'}));
warmContext.warm({tracks:[{ratingKey:'a',type:'album'},...tracks]});
assert.equal(warmed.length,1);assert.equal(warmed[0].method,'prepare_media');assert.equal(warmed[0].rows.length,6);assert.equal(warmed[0].rows[0].ratingKey,'1');
const navCode=cut('function rdManagerDetailScrollV944(', 'function rdManagerOrV910(');
const workspace={scrollHeight:1100,clientHeight:300,scrollTop:0,contains:el=>el?.area==='work'};
const current={area:'work'},footer={area:'footer'};let consumed=0,focused=0;
const navContext={RD_DIR_UP:9,RD_DIR_DOWN:10,RD_DIR_LEFT:11,RD_DIR_RIGHT:12,
  rdDir:event=>event.button,rdManagerRootV910:()=>({querySelector:()=>workspace}),
  rdManagerSpatialTargetV910:()=>footer,rdConsumeDirectionV80:()=>consumed++,rdFocusElementV5:()=>{focused++;return true},rdManagerRevealV910:()=>{}
};
vm.createContext(navContext);vm.runInContext(navCode+'\nthis.navigate=rdManagerDirectionalV910;',navContext);
assert.equal(navContext.navigate({button:10,currentTarget:current}),true);
assert(workspace.scrollTop>0,'Down should scroll detail before focusing the footer');
assert.equal(focused,0,'Footer must not take focus while detail remains');assert.equal(consumed,1);
// When content ends, the mini-player remains reachable; no permanent navigation trap.
workspace.scrollTop=800;
assert.equal(navContext.navigate({button:10,currentTarget:current}),true);
assert.equal(focused,1,'At bottom, footer is reachable');
// Scrolling and media internals for QAM remain separate from native Full Manager search.
const qam=cut('function QamMiniSearchV944()', 'function ReadyQamV7(');
assert(!qam.includes('DFL.TextField'),'QAM must not invoke native Steam keyboard');
assert(src.includes("h(DFL.TextField,{label:'Search all Plex audio'"),'Full Manager keeps native text entry');
console.log('PASS 0.9.45 detail scrolling, footer focus boundary, nonblocking search warmup, separate QAM keyboard');
