"""Test source and frozen Plex backend without a Plex account."""
import json, os, subprocess, sys, tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[2]
exe=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else None
with tempfile.TemporaryDirectory(prefix="resonadeck-native-") as path:
    env={**os.environ,"RESONADECK_WINDOWS_DATA_DIR":path}
    args=[str(exe)] if exe else [sys.executable,"-u",str(root/"native"/"bridge.py")]
    p=subprocess.Popen(args,cwd=root,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE,text=True,env=env)
    packets=[{"id":1,"method":"ping","args":[]},
             {"id":2,"method":"get_auth_state","args":[]},
             {"id":3,"method":"__class__","args":[]},
             {"event":"shutdown"}]
    try:
        output,errors=p.communicate("".join(json.dumps(x)+"\n" for x in packets),timeout=40)
    except subprocess.TimeoutExpired:
        p.kill();p.communicate()
        raise AssertionError("Native backend deadlocked") from None
    messages=[json.loads(line) for line in output.splitlines() if line.strip()]
    data={m["id"]:m for m in messages if isinstance(m.get("id"),int)}
    assert data[1]["ok"] and data[1]["result"]["bootstrapReady"], (messages,errors[-1200:])
    assert data[2]["ok"] and isinstance(data[2]["result"],dict)
    assert data[3]["ok"] is False
    assert p.returncode == 0, (p.returncode,errors[-1200:])
    print("Native backend IPC, security rejection and graceful shutdown PASS")
