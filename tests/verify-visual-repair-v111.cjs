const fs = require('fs');
const assert = require('node:assert/strict');
const path = require('path');
const root = path.resolve(__dirname, '..');
const src = fs.readFileSync(path.join(root,'src/index.js'), 'utf8');
const dist = fs.readFileSync(path.join(root,'dist/index.js'), 'utf8');
const base = fs.readFileSync('/mnt/data/rd_110_work/ResonaDeck/src/index.js', 'utf8');
assert.equal(src,dist,'distribution must match sources exactly');
assert(src.includes("const RD_VERSION = '1.1.1'"));
assert.equal(JSON.parse(fs.readFileSync(path.join(root,'plugin.json'),'utf8')).version,'1.1.1');
assert.equal(JSON.parse(fs.readFileSync(path.join(root,'package.json'),'utf8')).version,'1.1.1');
const slice = (code,a,b) => {
 const start=code.indexOf(a);const end=code.indexOf(b,start+a.length);
 assert(start>=0&&end>start,`Missing code boundary ${a}`);
 return code.slice(start,end);
};
// New duration refill is isolated to the queue-boundary path. Loaded-media layout is unchanged.
assert.equal(slice(src,'function QamNowV7(){','function QamDetailV7'),
             slice(base,'function QamNowV7(){','function QamDetailV7'),
             'active player markup and controller navigation unchanged');
assert.equal(slice(src,'  cancelCrossfadeV11(){','  applyBoost(){'),
             slice(base,'  cancelCrossfadeV11(){','  applyBoost(){'),
             'crossfade engine must remain unchanged');
assert(!src.includes("className:'rd-v83-time-sep'"),'the repaired white dot must stay gone');
const idle = slice(src,'function QamSurpriseIdleV11({','function QamNowV7(){');
assert(idle.includes("h(R.Fragment,null"),'settings outside banner row');
assert(idle.includes("className:'rd-v105-turntable rd-v11-surprise-record'"),'record itself is the focusable button');
assert(!idle.includes("className:'rd-v11-surprise-record',disabled"),'old oversized record button removed');
assert(idle.includes('onSecondaryButton:()=>setOpen(x=>!x)'),'X settings preserved');
assert(idle.includes('onClick:()=>void run()'),'A starts Surprise Me');
assert(idle.includes('rd-v105-vinyl-label'),'original golden center logo retained');
assert(src.includes('rdV105Spin 3.3s linear infinite'),'gold vinyl animation preserved');
const settings = slice(src,'function DiscoverySettingsV11({','function DiscoveryLibraryV11(){');
assert(!settings.includes('h(ControlV5,'),'all settings buttons must use protected glass');
assert(settings.includes("selected:String(cfg[key])===String(v)"),'selected option visible');
assert(settings.includes('h(DiscoveryGlassButtonV111,'));
for (const marker of ['function DiscoveryLibraryV11(){','function ManagerDiscoveryV11(){']) {
 const begin=src.indexOf(marker);const end=src.indexOf('\n}',begin)+2;const piece=src.slice(begin,end);
 assert(!piece.includes('h(ControlV5,'),`${marker} still has unthemed buttons`);
}
assert(src.includes("className:'rd-v111-glass-skin'"),'protected CSS Loader inner surface');
assert(src.includes('rd-v111-glass-label'),'high contrast readable labels');
assert(src.includes('max-height:min(50vh,420px)'),'settings must be scrollable in short QAM');
console.log('PASS: 1.1.1 theme/record isolation, protected discovery buttons, functional A/X, immutable white-dot/playback/crossfade engine.');
