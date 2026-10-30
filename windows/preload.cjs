'use strict';
const {contextBridge, ipcRenderer} = require('electron');

contextBridge.exposeInMainWorld('resonaWindows', Object.freeze({
  call: (method, args) => ipcRenderer.invoke('rd:rpc', method, args),
  state: () => ipcRenderer.invoke('rd:state'),
  command: (name, arg) => ipcRenderer.invoke('rd:command', name, arg),
  onState: (listener) => {
    if (typeof listener !== 'function') return () => {};
    const wrapped = (_event, state) => listener(state);
    ipcRenderer.on('rd:state-change', wrapped);
    return () => ipcRenderer.removeListener('rd:state-change', wrapped);
  }
}));
