'use strict';
const {app, BrowserWindow, ipcMain, Tray, Menu, shell, nativeImage, screen} = require('electron');
const path = require('node:path');
const fs = require('node:fs');
const {spawn} = require('node:child_process');

const SMALL = {width: 430, height: 720};
const LARGE = {width: 1160, height: 780};
let mainWindow = null, tray = null, backend = null, backendBuffer = '';
let exiting = false, currentId = 0;
const pending = new Map();
let options = {mode: 'mini', alwaysOnTop: false, minimizeToTray: true, bounds: {}};
let optionsFile = '';
const validMethod = /^[a-z][a-z0-9_]{1,65}$/;
const validModes = new Set(['mini', 'full']);

function loadOptions() {
  optionsFile = path.join(app.getPath('userData'), 'window.json');
  try {
    const data = JSON.parse(fs.readFileSync(optionsFile, 'utf8'));
    options = {
      mode: validModes.has(data.mode) ? data.mode : 'mini',
      alwaysOnTop: data.alwaysOnTop === true,
      minimizeToTray: data.minimizeToTray !== false,
      bounds: typeof data.bounds === 'object' && data.bounds ? data.bounds : {}
    };
  } catch (_) { /* first run */ }
}
function saveOptions() {
  try {
    fs.mkdirSync(path.dirname(optionsFile), {recursive: true});
    const tmp = optionsFile + '.tmp';
    fs.writeFileSync(tmp, JSON.stringify(options, null, 2), {mode: 0o600});
    fs.renameSync(tmp, optionsFile);
  } catch (error) { console.error('Could not save window preferences:', error.message); }
}
function safeBounds(value, fallback) {
  if (!value || !['width', 'height', 'x', 'y'].every(k => Number.isFinite(value[k]))) return fallback;
  const displays = screen.getAllDisplays().map(d => d.workArea);
  const width = Math.max(350, Math.min(2400, Math.round(value.width)));
  const height = Math.max(380, Math.min(1800, Math.round(value.height)));
  const x = Math.round(value.x), y = Math.round(value.y);
  if (!displays.some(d => x + width > d.x + 80 && x < d.x + d.width - 80 &&
                          y + height > d.y + 50 && y < d.y + d.height - 50)) return fallback;
  return {x, y, width, height};
}
function windowState() {
  return {
    mode: options.mode,
    alwaysOnTop: options.alwaysOnTop,
    minimizeToTray: options.minimizeToTray,
    maximized: Boolean(mainWindow && mainWindow.isMaximized())
  };
}
function broadcast() {
  if (mainWindow && !mainWindow.isDestroyed()) mainWindow.webContents.send('rd:state-change', windowState());
  if (tray) tray.setContextMenu(createTrayMenu());
}
function setMode(mode) {
  if (!validModes.has(mode) || !mainWindow) return;
  if (options.mode === mode) return broadcast();
  if (!mainWindow.isMaximized()) options.bounds[options.mode] = mainWindow.getBounds();
  options.mode = mode;
  if (mainWindow.isMaximized()) mainWindow.unmaximize();
  const size = mode === 'full' ? LARGE : SMALL;
  const stored = safeBounds(options.bounds[mode], null);
  const bounds = stored || {...size, ...mainWindow.getBounds(), width: size.width, height: size.height};
  mainWindow.setMinimumSize(mode === 'full' ? 650 : 350, mode === 'full' ? 500 : 380);
  mainWindow.setBounds(bounds, true);
  saveOptions(); broadcast();
}
function togglePin() {
  options.alwaysOnTop = !options.alwaysOnTop;
  mainWindow.setAlwaysOnTop(options.alwaysOnTop, 'floating');
  saveOptions(); broadcast();
}
function iconPath() {
  return path.join(__dirname, 'icon.ico');
}
function createTrayMenu() {
  return Menu.buildFromTemplate([
    {label: 'Show ResonaDeck', click: () => {mainWindow.show(); mainWindow.focus();}},
    {label: 'Mini player', click: () => {setMode('mini'); mainWindow.show();}},
    {label: 'Full library', click: () => {setMode('full'); mainWindow.show();}},
    {type: 'separator'},
    {label: 'Always on Top', type: 'checkbox', checked: options.alwaysOnTop, click: togglePin},
    {label: 'Minimize to tray on close', type: 'checkbox', checked: options.minimizeToTray, click: () => {
      options.minimizeToTray = !options.minimizeToTray; saveOptions(); broadcast();
    }},
    {type: 'separator'},
    {label: 'Quit ResonaDeck', click: () => {exiting = true; app.quit();}}
  ]);
}
function createWindow() {
  const defaults = options.mode === 'full' ? LARGE : SMALL;
  const bounds = safeBounds(options.bounds[options.mode], defaults);
  mainWindow = new BrowserWindow({
    ...bounds, frame: false, backgroundColor: '#101825',
    minWidth: 350, minHeight: 380, show: false,
    autoHideMenuBar: true,
    icon: iconPath(),
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
      backgroundThrottling: false,
      webSecurity: true
    }
  });
  mainWindow.setAlwaysOnTop(options.alwaysOnTop, 'floating');
  mainWindow.on('ready-to-show', () => mainWindow.show());
  mainWindow.on('close', event => {
    if (!exiting && options.minimizeToTray && tray) {
      event.preventDefault(); mainWindow.hide();
    }
  });
  const remember = () => {
    if (!mainWindow.isMaximized() && !mainWindow.isMinimized()) {
      options.bounds[options.mode] = mainWindow.getBounds();
      saveOptions();
    }
    broadcast();
  };
  mainWindow.on('resize', remember);
  mainWindow.on('move', remember);
  mainWindow.on('maximize', broadcast);
  mainWindow.on('unmaximize', broadcast);
  mainWindow.webContents.setWindowOpenHandler(({url}) => {
    if (/^https:\/\//i.test(url)) void shell.openExternal(url);
    return {action: 'deny'};
  });
  mainWindow.webContents.on('will-navigate', (event, url) => {
    if (url !== mainWindow.webContents.getURL()) {
      event.preventDefault();
      if (/^https:\/\//i.test(url)) void shell.openExternal(url);
    }
  });
  mainWindow.loadFile(path.join(__dirname, 'index.html'));
}
function createTray() {
  let icon = nativeImage.createFromPath(iconPath());
  if (icon.isEmpty()) {
    const fallback = path.join(__dirname, '..', 'assets', 'resonadeck-icon.webp');
    icon = nativeImage.createFromPath(fallback);
  }
  if (icon.isEmpty()) return;
  tray = new Tray(icon);
  tray.setToolTip('ResonaDeck for Windows');
  tray.setContextMenu(createTrayMenu());
  tray.on('double-click', () => {mainWindow.show(); mainWindow.focus();});
}
function backendExecutable() {
  if (app.isPackaged) return {
    cmd: path.join(process.resourcesPath, 'backend', 'ResonaDeckBackend', 'ResonaDeckBackend.exe'),
    args: [],
    cwd: path.join(process.resourcesPath, 'backend', 'ResonaDeckBackend')
  };
  return {
    cmd: process.env.RESONADECK_PYTHON || 'python',
    args: ['-u', path.join(__dirname, 'bridge.py')],
    cwd: path.resolve(__dirname, '..')
  };
}
function rejectAll(reason) {
  for (const [id, item] of pending) {
    clearTimeout(item.timer); item.reject(new Error(reason)); pending.delete(id);
  }
}
function startBackend() {
  const config = backendExecutable();
  backend = spawn(config.cmd, config.args, {
    cwd: config.cwd, windowsHide: true, stdio: ['pipe', 'pipe', 'pipe'],
    env: {...process.env, RESONADECK_WINDOWS_DATA_DIR: app.getPath('userData')}
  });
  backend.on('error', error => {console.error('Backend startup failed:', error.message); rejectAll('Could not start Plex backend. See windows/README.md.');});
  backend.on('exit', (code) => {backend = null; rejectAll('Plex backend stopped (exit ' + code + ')');});
  backend.stdout.setEncoding('utf8');
  backend.stdout.on('data', chunk => {
    backendBuffer += chunk;
    if (backendBuffer.length > 32 * 1024 * 1024) {backendBuffer = ''; rejectAll('Backend response exceeded limit');}
    let end;
    while ((end = backendBuffer.indexOf('\n')) >= 0) {
      const line = backendBuffer.slice(0, end); backendBuffer = backendBuffer.slice(end + 1);
      let result;
      try {result = JSON.parse(line);} catch (_) {continue;}
      if (!Number.isInteger(result.id)) continue;
      const item = pending.get(result.id);
      if (!item) continue;
      pending.delete(result.id); clearTimeout(item.timer);
      if (result.ok) item.resolve(result.result); else item.reject(new Error(String(result.error || 'Backend error')));
    }
  });
  backend.stderr.setEncoding('utf8');
  backend.stderr.on('data', data => console.error('[Plex backend]', data.toString().slice(0, 1000)));
}
function rpc(method, args) {
  if (typeof method !== 'string' || !validMethod.test(method) ||
      !Array.isArray(args) || args.length > 20) return Promise.reject(new Error('Invalid Plex request'));
  if (!backend || !backend.stdin.writable) return Promise.reject(new Error('Plex backend unavailable'));
  const id = ++currentId;
  const line = JSON.stringify({id, method, args}) + '\n';
  if (line.length > 2 * 1024 * 1024) return Promise.reject(new Error('Request too large'));
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      pending.delete(id); reject(new Error('Backend request timed out'));
    }, 25000);
    pending.set(id, {resolve, reject, timer});
    backend.stdin.write(line, error => {
      if (error && pending.has(id)) {
        clearTimeout(timer); pending.delete(id); reject(error);
      }
    });
  });
}
const gotLock = app.requestSingleInstanceLock();
if (!gotLock) app.quit();
else {
  app.on('second-instance', () => {if (mainWindow) {mainWindow.show(); mainWindow.focus();}});
  app.whenReady().then(() => {
    loadOptions(); createWindow(); createTray(); startBackend();
    ipcMain.handle('rd:rpc', (event, method, args) => {
      if (event.sender !== mainWindow.webContents) throw new Error('Invalid sender');
      return rpc(method, args);
    });
    ipcMain.handle('rd:state', event => {
      if (event.sender !== mainWindow.webContents) throw new Error('Invalid sender');
      return windowState();
    });
    ipcMain.handle('rd:command', (event, name, arg) => {
      if (event.sender !== mainWindow.webContents) throw new Error('Invalid sender');
      if (name === 'minimize') mainWindow.minimize();
      else if (name === 'close') {
        if (options.minimizeToTray && tray) mainWindow.hide();
        else {exiting = true; app.quit();}
      }
      else if (name === 'togglePin') togglePin();
      else if (name === 'setMode') setMode(arg);
      else if (name === 'toggleMaximize') {
        if (mainWindow.isMaximized()) mainWindow.unmaximize(); else mainWindow.maximize();
      }
      else if (name === 'toggleTray') {
        options.minimizeToTray = !options.minimizeToTray; saveOptions(); broadcast();
      } else throw new Error('Unknown window command');
      return windowState();
    });
  });
  app.on('before-quit', () => {
    exiting = true;
    if (backend && backend.stdin.writable) {
      try {backend.stdin.write(JSON.stringify({event: 'shutdown'}) + '\n');} catch (_) {}
    }
  });
  app.on('window-all-closed', () => {if (!options.minimizeToTray || !tray) app.quit();});
}
