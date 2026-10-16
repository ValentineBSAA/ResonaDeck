const fs=require('fs'),assert=require('assert/strict'),vm=require('vm'),path=require('path');
const dir=path.resolve(__dirname,'..');
const src=fs.readFileSync(path.join(dir,'src/index.js'),'utf8');
const dist=fs.readFileSync(path.join(dir,'dist/index.js'),'utf8');
const main=fs.readFileSync(path.join(dir,'main.py'),'utf8');
const backend=fs.readFileSync(path.join(dir,'resonadeck_backend.py'),'utf8');
const pack=JSON.parse(fs.readFileSync(path.join(dir,'assets/idle-messages.json'),'utf8'));
assert.equal(src,dist,'frontend source and installation must remain byte identical');
assert.equal(pack.messages.length,2048);
assert.equal(new Set(pack.messages).size,2048,'every quote must be distinct');
assert(pack.messages.every(x=>typeof x==='string'&&x.length>=12&&x.length<=150));
assert(src.includes("const RD_VERSION = '1.0.8'"));
assert(src.includes('const idleQuote=useIdleListeningV101(!cur&&visible)'));
assert(src.includes('setInterval(()=>setIndex(previous=>rdIdlePickV101(list,previous)),23500)'));
assert(src.includes("call('get_idle_messages')"));
assert(src.includes('rd-v101-idle-icon')&&src.includes('rd-v101-idle-quote'));
assert(src.includes('Choose Music, Books, Podcasts or More below'));
assert(src.includes('rd-v101-cursor-idle'));
assert(src.includes('@media(prefers-reduced-motion:reduce)'));
assert(main.includes('async def get_idle_messages(self): return await self._forward("get_idle_messages")'));
assert(backend.includes('async def get_idle_messages(self):'));
const m=src.match(/function rdIdlePickV101\(list,old=-1\)\{[\s\S]*?\n\}/);
assert(m,'pick helper exists');
const context=vm.createContext({Math});
vm.runInContext(m[0],context);
assert.equal(vm.runInContext('rdIdlePickV101(["one"],0)',context),0);
for(const n of [2,3,32,2048]){
  for(let i=0;i<200;i++){
    const arr=Array.from({length:n},(_,k)=>`quote${k}`);
    context.arr=arr;context.prev=i%n;
    const next=vm.runInContext('rdIdlePickV101(arr,prev)',context);
    assert(Number.isInteger(next)&&next>=0&&next<n);
    assert.notEqual(next,context.prev,'rotation must not repeat current line');
  }
}
console.log('PASS: 2048 messages, edit-refresh and backend wiring, idle-only animation, cursor fallback, no repeat picker');
