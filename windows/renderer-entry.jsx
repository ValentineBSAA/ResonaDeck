import * as React from 'react';
import {createRoot} from 'react-dom/client';

/*
 * Minimal Decky UI adapter. The original ResonaDeck frontend is imported
 * unchanged and still owns player state, crossfade, queues and artwork.
 * This adapter only supplies React, navigation, common UI fields and RPC.
 */
window.SP_REACT = React;

const directions = {ArrowUp: 9, ArrowDown: 10, ArrowLeft: 11, ArrowRight: 12};
const routeFactories = new Map();
const routeListeners = new Set();
let currentRoute = '/';
function publishRoute(route) {
  currentRoute = route;
  for (const listener of routeListeners) listener(route);
}
function navigate(route) {
  const target = routeFactories.has(route) ? route : '/';
  publishRoute(target);
  void window.resonaWindows.command('setMode', target === '/' ? 'mini' : 'full').catch(console.error);
}
function back() { navigate('/'); }
const Navigation = {Navigate: navigate, NavigateBack: back, NavigateTo: element => element?.focus?.()};

function maybeDirection(event, callback) {
  const code = directions[event.key];
  if (code == null) return;
  const directionEvent = {
    detail: {button: code},
    preventDefault: () => event.preventDefault(),
    stopPropagation: () => event.stopPropagation(),
    target: event.target,
    currentTarget: event.currentTarget
  };
  if (typeof callback === 'function') callback(directionEvent);
}
// Decky focus props are meaningful on SteamOS but not valid HTML attributes.
const Focusable = React.forwardRef(function Focusable(props, ref) {
  const {children, className = '', onCancel, onGamepadDirection,
    onKeyDown, focusable, ...rest} = props;
  const attrs = {...rest};
  delete attrs['flow-children'];
  delete attrs['onGamepadButtonDown'];
  return <div {...attrs} ref={ref} tabIndex={attrs.tabIndex ?? -1} className={'rd-win-focusable ' + className}
    onKeyDown={event => {
      onKeyDown?.(event);
      if (!event.defaultPrevented && event.key === 'Escape') onCancel?.(event);
      if (!event.defaultPrevented) maybeDirection(event, onGamepadDirection);
    }}>{children}</div>;
});
const DialogButton = React.forwardRef(function DialogButton(props, ref) {
  const {children, className = '', onGamepadDirection, onCancel, onKeyDown,
    focusable, ...rest} = props;
  const attrs = {...rest};
  delete attrs['flow-children'];
  delete attrs['onGamepadButtonDown'];
  return <button {...attrs} ref={ref} type="button" className={'rd-win-button ' + className}
    onKeyDown={event => {
      onKeyDown?.(event);
      if (!event.defaultPrevented && event.key === 'Escape') onCancel?.(event);
      if (!event.defaultPrevented) maybeDirection(event, onGamepadDirection);
    }}>{children}</button>;
});
function TextField({label, description, value, onChange, onEnterKeyPress, bShowClearAction, ...rest}) {
  return <label className="rd-native-field">
    {label ? <span>{label}</span> : null}
    <input type="text" {...rest} value={value ?? ''} onChange={onChange}
      onKeyDown={event => {if (event.key === 'Enter') onEnterKeyPress?.(event);}} />
    {description ? <small>{description}</small> : null}
  </label>;
}
function SliderField({label, description, min = 0, max = 100, step = 1,
  value = 0, onChange, ...rest}) {
  return <label className="rd-native-slider">
    <span>{label} · {Number(value).toFixed(step < 1 ? 2 : 0)}</span>
    <input type="range" min={min} max={max} step={step} value={value}
      onChange={event => onChange?.(Number(event.target.value))} />
    {description ? <small>{description}</small> : null}
  </label>;
}
window.DFL = {Focusable, DialogButton, TextField, SliderField, Navigation,
  getGamepadNavigationTrees: () => []};

// The existing hooks register for Steam shoulder events. Send equivalent
// standardized Gamepad API events on Windows, without modifying plugin code.
const gamepadListeners = new Set();
window.SteamClient = {
  Input: {
    RegisterForControllerInputMessages(listener) {
      gamepadListeners.add(listener);
      return {unregister: () => gamepadListeners.delete(listener),
        Unregister: () => gamepadListeners.delete(listener)};
    }
  },
  Browser: {HideCursorUntilMouseEvent: () => {}}
};
const lastButtons = new Map();
setInterval(() => {
  for (const pad of navigator.getGamepads?.() || []) {
    if (!pad || !pad.connected) continue;
    const previous = lastButtons.get(pad.index) || {};
    const next = {};
    // Standard Gamepad mapping: LB 4, RB 5, D-pad up/down/left/right 12-15.
    for (const [index, translated] of [[4,30],[5,31],[12,9],[13,10],[14,11],[15,12]]) {
      const pressed = Boolean(pad.buttons?.[index]?.pressed);
      next[index] = pressed;
      if (previous[index] !== pressed) {
        for (const listener of gamepadListeners) {
          try {listener({controller: pad.index, button: translated, pressed});} catch (e) {console.warn(e);}
        }
      }
    }
    lastButtons.set(pad.index, next);
  }
}, 80);

let toastListener = () => {};
window.__DECKY_SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED_deckyLoaderAPIInit = {
  connect() {
    return {
      call: (method, ...args) => window.resonaWindows.call(method, args),
      routerHook: {
        addRoute: (path, factory) => routeFactories.set(path, factory),
        removeRoute: path => routeFactories.delete(path)
      },
      toaster: {toast: ({title, body}) => toastListener(String(title || '') + ': ' + String(body || ''))},
      useQuickAccessVisible: () => true
    };
  }
};

function App({plugin}) {
  const [route, setRoute] = React.useState(currentRoute);
  const [native, setNative] = React.useState({mode: 'mini', alwaysOnTop: false, minimizeToTray: true});
  const [toast, setToast] = React.useState('');
  const [showMenu, setShowMenu] = React.useState(false);
  React.useEffect(() => {
    routeListeners.add(setRoute);
    const unsubscribe = window.resonaWindows.onState(state => {
      setNative(state);
      const expected = state.mode === 'mini' ? '/' : '/resonadeck-manager';
      if (currentRoute === '/' && state.mode === 'full') publishRoute(expected);
      if (currentRoute !== '/' && state.mode === 'mini') publishRoute('/');
    });
    window.resonaWindows.state().then(state => {
      setNative(state);
      if (state.mode === 'full') publishRoute('/resonadeck-manager');
    }).catch(console.error);
    return () => {routeListeners.delete(setRoute); unsubscribe();};
  }, []);
  React.useEffect(() => {
    let timer;
    toastListener = message => {setToast(message); clearTimeout(timer); timer = setTimeout(() => setToast(''), 3700);};
    return () => {toastListener = () => {}; clearTimeout(timer);};
  }, []);
  React.useEffect(() => {
    const handle = event => {
      if (event.ctrlKey && event.key.toLowerCase() === 'm') {
        event.preventDefault(); navigate(currentRoute === '/' ? '/resonadeck-manager' : '/');
      }
      if (event.ctrlKey && event.shiftKey && event.key.toLowerCase() === 'p') {
        event.preventDefault(); void window.resonaWindows.command('togglePin');
      }
      if (event.ctrlKey && (event.key === 'PageUp' || event.key === 'PageDown')) {
        event.preventDefault();
        const button = event.key === 'PageUp' ? 30 : 31;
        for (const listener of gamepadListeners) {
          try {listener({controller: 0, button, pressed: true});} catch (_) {}
          setTimeout(() => {try {listener({controller: 0, button, pressed: false});} catch (_) {}}, 25);
        }
      }
      if (event.key === 'Escape' && currentRoute !== '/' && !event.defaultPrevented) back();
    };
    window.addEventListener('keydown', handle);
    return () => window.removeEventListener('keydown', handle);
  }, []);
  const factory = routeFactories.get(route);
  const player = route === '/' ? plugin.content : (factory ? factory() : plugin.content);
  return <div className={'rd-win-app ' + (route === '/' ? 'mini' : 'full')}>
    <header className="rd-win-toolbar">
      <div className="rd-win-drag">
        <span className="rd-win-brand">◉ ResonaDeck</span>
        <span className="rd-win-caption">Windows Preview</span>
      </div>
      <button title={route === '/' ? 'Open Full Library (Ctrl+M)' : 'Mini Player (Ctrl+M)'}
        onClick={() => navigate(route === '/' ? '/resonadeck-manager' : '/')}>
        {route === '/' ? '⛶ Full' : '▣ Mini'}</button>
      <button className={'pin ' + (native.alwaysOnTop ? 'active' : '')}
        title="Toggle Always on Top (Ctrl+Shift+P)"
        aria-pressed={native.alwaysOnTop}
        onClick={() => void window.resonaWindows.command('togglePin')}>📌</button>
      <button title="Windows options" onClick={() => setShowMenu(!showMenu)}>⚙</button>
      <button title="Minimize" onClick={() => void window.resonaWindows.command('minimize')}>−</button>
      <button title="Maximize or restore" onClick={() => void window.resonaWindows.command('toggleMaximize')}>▢</button>
      <button title={native.minimizeToTray ? 'Close to tray' : 'Close'}
        onClick={() => void window.resonaWindows.command('close')}>×</button>
    </header>
    {showMenu && <div className="rd-win-settings">
      <label><input type="checkbox" checked={native.alwaysOnTop}
        onChange={() => void window.resonaWindows.command('togglePin')} /> Always on Top</label>
      <label><input type="checkbox" checked={native.minimizeToTray}
        onChange={() => void window.resonaWindows.command('toggleTray')} /> Close to system tray</label>
      <small>Ctrl+M: mini / full · Ctrl+Shift+P: pin window</small>
    </div>}
    <main className="rd-win-body" id="resonadeck-player">{player}</main>
    {toast && <div className="rd-win-toast" role="status">{toast}</div>}
  </div>;
}
import('../src/index.js').then(module => {
  const plugin = module.default();
  createRoot(document.getElementById('app')).render(<App plugin={plugin}/>);
}).catch(error => {
  console.error(error);
  const target = document.getElementById('app');
  target.textContent = 'ResonaDeck could not start: ' + String(error.message || error);
  target.className = 'rd-win-loading-error';
});
