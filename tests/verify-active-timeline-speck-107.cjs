// Verify the shared active-audio player does not render a detached time-separator dot.
const fs=require('fs'),assert=require('assert');
const src=fs.readFileSync(__dirname+'/../src/index.js','utf8');
const dist=fs.readFileSync(__dirname+'/../dist/index.js','utf8');
const root=src.slice(src.indexOf('function QamNowV7(){'),src.indexOf('function QamDetailV7'));
assert.equal(src,dist,'source and runtime must be identical');
assert(root.includes("className:'rd-v80-now-time'"),'keep time-row layout');
assert(root.includes("className:'rd-v83-time-current'"),'keep elapsed time');
assert(root.includes("className:'rd-v83-time-remain'"),'keep remaining time');
assert(!root.includes("className:'rd-v83-time-sep'"),'no isolated time separator');
assert(!root.includes("h('span',null,' · ')"),'no orphan middle-dot span');
assert(root.includes('rd-v91-viz'),'keep visualizer');
assert(root.includes("h('div',{className:'rd-v105-turntable'"),'keep golden turntable');
assert(root.includes('h(QamMusicQueueDrawerV912'),'keep queue drawer');
assert(/\.rd-root\.rd-v7-qam \.rd-v80-now-time\{display:flex;align-items:center;justify-content:space-between;gap:4px\}/.test(src),'time readings stay at opposite ends');
console.log('PASS: 1.0.8 shared audio timeline no longer renders an orphan middle dot');
