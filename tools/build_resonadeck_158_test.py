"""Apply ResonaDeck 1.5.8 TEST experimental changes to the *published* 1.5.7 ZIP.
Fail closed when release layout or expected anchors change.
Do not build against repository main: its package metadata still says 1.5.1.
"""
from __future__ import annotations
import json
import shutil
import sys
from pathlib import Path

VERSION = "1.5.8-test.1"

PLAYER_CONNECT_JS = r'''
function PlayerConnectV158(){
  const [expanded,setExpanded]=R.useState(false),[items,setItems]=R.useState([]),
        [selected,setSelected]=R.useState(''),[scanning,setScanning]=R.useState(false),
        [sending,setSending]=R.useState(false),[status,setStatus]=R.useState('');
  const snap=useEngine();
  const refresh=async()=>{
    if(scanning)return;
    setScanning(true);setStatus('Scanning local Plex players…');
    try{
      const answer=await call('get_player_connect_devices',true);
      if(!answer?.success){setItems([]);setStatus(answer?.message||'Discovery is unavailable.');return;}
      const devices=Array.isArray(answer.devices)?answer.devices:[];
      setItems(devices);
      setStatus(devices.length?'Select a player, then test its connection.':'No compatible players found. On your iPhone, open Plexamp and enable Remote Control.');
    }catch(e){setStatus('Player discovery failed. Try again on the same Wi-Fi.');}
    finally{setScanning(false);}
  };
  const send=async(action,id=selected)=>{
    if(!id||sending)return;
    setSending(true);setStatus('Contacting remote player…');
    try{
      const key=String(snap?.current?.ratingKey||snap?.current?.key||'').replace(/^\/library\/metadata\//,'');
      const response=await call('player_connect_command',id,action,action==='sendTrack'?key:'');
      setStatus(response?.success?(
        action==='probe'?'Player responded. Remote controls are ready to test.':
        action==='sendTrack'?'Track sent. Confirm audio on the phone before switching fully.':
        'Command accepted. Check the remote player.'
      ):(response?.message||'The player did not accept that command.'));
      // Do not interrupt local audio without confirmation that a remote receiver started it.
    }catch(e){setStatus('Remote command failed. Check the phone and try again.');}
    finally{setSending(false);}
  };
  const button=(text,action,disabled=false)=>h(ControlV5,{
    className:'rd-v158-remote-button',disabled:disabled||sending,
    onClick:()=>void send(action)
  },text);
  return h(DFL.Focusable,{className:'rd-v158-player-connect','flow-children':'down',
    onCancel:expanded?(e=>{e?.preventDefault?.();e?.stopPropagation?.();setExpanded(false);}):undefined},
    h('style',null,`
      .rd-v158-player-connect{margin:8px 8px 12px;padding:9px;border-radius:17px;
      background:linear-gradient(150deg,rgba(49,92,105,.19),rgba(16,24,43,.36));
      border:1px solid rgba(139,209,225,.22);color:var(--rd-text,#eef5ff)}
      .rd-v158-player-connect .rd-v158-open{width:100%;min-height:46px;border-radius:12px;
      font-weight:700;text-align:left;display:flex;justify-content:space-between;align-items:center}
      .rd-v158-player-connect .rd-v158-row{display:flex;flex-wrap:wrap;gap:8px;margin-top:9px}
      .rd-v158-player-connect .rd-v158-row button{min-height:44px;min-width:70px;flex:1;
      border-radius:12px;white-space:normal;font-weight:600}
      .rd-v158-player-connect .rd-v158-device{width:100%;min-height:58px;text-align:left;
      display:flex;flex-direction:column;justify-content:center;border-radius:13px;padding:9px 12px}
      .rd-v158-player-connect .rd-v158-device.selected{border:2px solid #79e5d6;
      box-shadow:0 0 15px rgba(64,224,200,.2)}
      .rd-v158-player-connect .rd-v158-device small{opacity:.75}
      .rd-v158-player-connect .rd-v158-status{font-size:12px;line-height:1.45;
      margin:9px 3px;color:var(--rd-muted,#c1d5e2)}
      .rd-v158-player-connect .rd-v158-caption{font-size:11px;opacity:.78;line-height:1.45}
    `),
    h(ControlV5,{className:'rd-v158-open',onClick:()=>{if(!expanded){setExpanded(true);void refresh();}else setExpanded(false);},
      'aria-expanded':expanded},'◈  Player Connect',expanded?'▴':'▾'),
    expanded?h(DFL.Focusable,{'flow-children':'down',className:'rd-v158-panel'},
      h('p',{className:'rd-v158-caption'},'1.5.8 TEST · Plex Companion LAN experiment. Touchscreen, D-pad, A and B supported.'),
      h('div',{className:'rd-v158-row'},h(ControlV5,{disabled:scanning,onClick:()=>void refresh()},
        scanning?'Scanning…':'↻ Refresh local players')),
      ...items.map((device)=>h(ControlV5,{key:device.id,
          className:'rd-v158-device '+(selected===device.id?'selected':''),
          onClick:()=>{setSelected(device.id);void send('probe',device.id);}},
        h('strong',null,(selected===device.id?'● ':'○ ')+device.name),
        h('small',null,device.product+' · '+device.source+' · '+(selected===device.id?'Selected':'Tap or press A')))),
      selected?h(DFL.Focusable,{'flow-children':'right',className:'rd-v158-row'},
        button('▶ Play','play'),button('❚❚ Pause','pause'),
        button('‹ Previous','previous'),button('Next ›','next')):null,
      selected?h('div',{className:'rd-v158-row'},button('♫ Send Current Track','sendTrack',!snap?.current),
          button('■ Stop','stop')):null,
      h('div',{className:'rd-v158-status',role:'status'},status||'Steam Deck playback remains local until a remote command is confirmed.'),
      h('p',{className:'rd-v158-caption'},'Experimental: normal ResonaDeck controls and queue still control this Deck. Remote queue handoff and Deck receiver advertising are not yet enabled.')
    ):null);
}
'''

def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one stable anchor; found {count}")
    return text.replace(old, new, 1)

def work(root: Path, source: Path):
    if not (root / 'plugin.json').is_file():
        children = [p for p in root.iterdir() if p.is_dir() and (p / 'plugin.json').is_file()]
        if len(children)!=1:
            raise RuntimeError('Installer root not recognized; refusing to modify.')
        root=children[0]
    meta=json.loads((root/'plugin.json').read_text(encoding='utf-8'))
    if meta.get('version') != '1.5.7':
        raise RuntimeError(f"Expected published stable package 1.5.7; saw {meta.get('version')!r}.")
    if (root/'resonadeck_player_connect.py').exists():
        raise RuntimeError('Player Connect module already exists; refusing double patch.')
    shutil.copy2(source/'resonadeck_player_connect.py',root/'resonadeck_player_connect.py')

    main=root/'main.py'
    main_text=main.read_text(encoding='utf-8')
    main_text=replace_once(main_text,
        '            impl_cls = getattr(module, "Plugin")',
        '            impl_cls = getattr(module, "Plugin")\n'
        '            from resonadeck_player_connect import install as _rd158_install\n'
        '            _rd158_install(impl_cls)', 'backend install')
    main_text=replace_once(main_text,
        '    async def begin_plex_auth(self):',
        '    async def get_player_connect_devices(self, force: bool = False): return await self._forward("get_player_connect_devices", force)\n'
        '    async def player_connect_command(self, player_id: str, action: str, rating_key: str = ""): return await self._forward("player_connect_command", player_id, action, rating_key)\n'
        '    async def begin_plex_auth(self):', 'backend RPC proxies')
    main.write_text(main_text.replace('ResonaDeck 0.9.30 Decky bootstrap.', 'ResonaDeck 1.5.8 TEST Decky bootstrap.'),encoding='utf-8')

    for path in [root/'dist'/'index.js',root/'src'/'index.js']:
        if not path.is_file():
            raise RuntimeError(f'Missing compiled frontend {path}.')
        code=path.read_text(encoding='utf-8')
        code=replace_once(code, 'function ReadyQamV7({auth,onProfile}){',
                          PLAYER_CONNECT_JS+'\nfunction ReadyQamV7({auth,onProfile}){',str(path)+': component')
        # Only patch the Ready QAM component, not another player's appearance elsewhere.
        start_ready=code.index('function ReadyQamV7({auth,onProfile}){')
        end_ready=code.index('/* 0.9.46:',start_ready)
        if start_ready < 0 or end_ready < 0:
            raise RuntimeError(str(path)+': could not isolate Ready QAM for Player Connect.')
        ready=code[start_ready:end_ready]
        ready=replace_once(ready,'h(QamNowV7),',
            'h(QamNowV7),\n     h(PlayerConnectV158),',str(path)+': Player Connect placement')
        code=code[:start_ready]+ready+code[end_ready:]
        # Make repeated QAM opens instant after a verified first-session ready state.
        # Background refresh remains active; no media or GTM playback code is changed.
        code=replace_once(code,
             "const [stage,setStage]=R.useState('loading'),[auth,setAuth]=R.useState(null),",
             "const [stage,setStage]=R.useState(()=>runtimeHost().__rd158QamReady?'ready':'loading'),[auth,setAuth]=R.useState(()=>runtimeHost().__rd158QamAuth||null),",
             str(path)+': warm state')
        start_qam=code.index('function QAMV7(){')
        end_qam=code.index('function ProfileRoute()',start_qam)
        if start_qam < 0 or end_qam < 0:
            raise RuntimeError(str(path)+': could not isolate QAM startup.')
        qam=code[start_qam:end_qam]
        # Guard any existing Loading transition during background revalidation.
        if "setStage('loading');" in qam:
            qam=qam.replace("setStage('loading');",
                  "if(!runtimeHost().__rd158QamReady)setStage('loading');",1)
        if "setAuth(a);" in qam:
            qam=qam.replace("setAuth(a);",
                  "setAuth(a);runtimeHost().__rd158QamAuth=a;",1)
        if "setStage('ready');" not in qam:
            raise RuntimeError(str(path)+': missing readiness transition; cannot enable warm cache')
        qam=qam.replace("setStage('ready');",
              "runtimeHost().__rd158QamReady=true;setStage('ready');",1)
        if "setStage('server');" in qam:
            qam=qam.replace("setStage('server');",
                  "runtimeHost().__rd158QamReady=false;setStage('server');",1)
        code=code[:start_qam]+qam+code[end_qam:]
        # Do not perform extra remote discovery until user explicitly expands panel.
        code=code.replace("const RD_VERSION = '1.5.7';", "const RD_VERSION = '1.5.8 TEST';", 1)
        path.write_text(code,encoding='utf-8')

    meta['version']=VERSION
    meta['description']='ResonaDeck 1.5.8 TEST: experimental LAN Player Connect and warm Quick Menu.'
    if isinstance(meta.get('publish'),dict):
        meta['publish']['description']=meta['description']
    (root/'plugin.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
    package=root/'package.json'
    if package.is_file():
        p=json.loads(package.read_text(encoding='utf-8'))
        p['version']=VERSION
        p['description']=meta['description']
        package.write_text(json.dumps(p,indent=2)+'\n',encoding='utf-8')
    (root/'TEST_1.5.8_README.md').write_text((source/'docs'/'RESONADECK_158_TEST_PLAN.md').read_text(encoding='utf-8'),encoding='utf-8')
    print('Patched published ResonaDeck 1.5.7 installer -> 1.5.8 TEST (not stable).')

if __name__=='__main__':
    if len(sys.argv)!=3:
        raise SystemExit('usage: build_resonadeck_158_test.py EXTRACTED_ZIP_ROOT PATCH_SOURCE_ROOT')
    work(Path(sys.argv[1]),Path(sys.argv[2]))
