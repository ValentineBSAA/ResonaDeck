"""Hardware-independent safety / protocol gate tests for 1.5.8 TEST."""
import asyncio
import sys
import types
import unittest

# aiohttp is available inside Decky; GitHub's python runner may not have it installed.
if "aiohttp" not in sys.modules:
    aiohttp=types.ModuleType("aiohttp")
    class _Timeout:
        def __init__(self, **kwargs): self.settings=kwargs
    aiohttp.ClientTimeout=_Timeout
    aiohttp.ClientError=type("ClientError", (Exception,), {})
    sys.modules["aiohttp"]=aiohttp

from resonadeck_player_connect import _safe_connection, _device_row, install


class GuardTests(unittest.TestCase):
    def test_rfc1918_only(self):
        self.assertEqual(_safe_connection("http://192.168.5.20:32500"),"http://192.168.5.20:32500")
        self.assertEqual(_safe_connection("http://10.15.3.4:32500"),"http://10.15.3.4:32500")
        self.assertEqual(_safe_connection("http://172.19.1.7:32500"),"http://172.19.1.7:32500")
        for uri in ["http://8.8.8.8:32500", "http://127.0.0.1:32500",
                    "http://192.0.0.8:32500", "http://169.254.1.2:32500",
                    "https://10.1.2.3:32500", "http://example.com:32500",
                    "http://user:password@10.1.2.3:32500", "file:///etc/passwd"]:
            with self.subTest(uri=uri):
                self.assertIsNone(_safe_connection(uri))

    def test_accepts_only_local_player_connections(self):
        good={"clientIdentifier":"phone-1","name":"iPhone",
              "product":"Plexamp","provides":"player",
              "connections":[
                {"uri":"http://192.168.1.50:32500", "local":True},
                {"uri":"http://8.8.8.8:32500", "local":False}]}
        result=_device_row(good)
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]["url"],"http://192.168.1.50:32500")
        self.assertNotIn("token",str(result).lower())
        self.assertEqual(_device_row({**good,"provides":"server"}),[])
        self.assertEqual(_device_row({**good,"connections":[{"uri":"http://192.168.1.50:32500","local":False}]}),[])

    def test_invalid_remote_actions_refused(self):
        class Stub:
            _media_provider="plex"
            _session=None
        install(Stub)
        obj=Stub()
        bad=asyncio.run(obj.player_connect_command("test","setWhatever",""))
        self.assertFalse(bad["success"])
        self.assertIn("Unsupported",bad["message"])
        no_device=asyncio.run(obj.player_connect_command("test","play",""))
        self.assertFalse(no_device["success"])

    def test_non_plex_refused_without_network(self):
        class Stub:
            _media_provider="jellyfin"
        install(Stub)
        obj=Stub()
        result=asyncio.run(obj.get_player_connect_devices())
        self.assertFalse(result["success"])
        self.assertEqual(result["devices"],[])


if __name__ == "__main__":
    unittest.main(verbosity=2)
