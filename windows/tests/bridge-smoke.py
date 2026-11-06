"""Start the real Plex backend without credentials and exercise its local RPC."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

repo = Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory(prefix="resonadeck-win-") as data:
    env = dict(os.environ, RESONADECK_WINDOWS_DATA_DIR=data)
    command = [str(Path(sys.argv[1]).resolve())] if len(sys.argv) > 1 else [
        sys.executable, "-u", str(repo / "windows" / "bridge.py")]
    process = subprocess.Popen(
        command,
        cwd=repo, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, env=env
    )
    requests = [
        {"id": 1, "method": "ping", "args": []},
        {"id": 2, "method": "get_auth_state", "args": []},
        {"id": 3, "method": "__class__", "args": []},
        {"event": "shutdown"}
    ]
    try:
        output, errors = process.communicate(
            "".join(json.dumps(message) + "\n" for message in requests),
            timeout=35
        )
    except subprocess.TimeoutExpired:
        process.kill()
        output, errors = process.communicate()
        raise AssertionError("Backend startup or shutdown timed out") from None
    messages = [json.loads(line) for line in output.splitlines() if line.strip()]
    by_id = {m["id"]: m for m in messages if isinstance(m.get("id"), int)}
    assert by_id[1]["ok"] and by_id[1]["result"]["bootstrapReady"], (messages, errors[-1500:])
    assert by_id[2]["ok"] and isinstance(by_id[2]["result"], dict), (messages, errors[-1500:])
    assert by_id[3]["ok"] is False, (messages, errors[-1500:])
    print("Windows RPC and Plex backend bootstrap passed; no actual Plex login tested.")
