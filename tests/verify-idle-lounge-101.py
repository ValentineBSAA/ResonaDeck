"""Offline regression for Decky idle quote packs without launching the Plex backend."""
from pathlib import Path
import ast
import asyncio
import json
import tempfile
import types
import unittest

ROOT=Path(__file__).resolve().parents[1]

class IdleLoungeTest(unittest.TestCase):
    def setUp(self):
        source=(ROOT/'resonadeck_backend.py').read_text()
        parsed=ast.parse(source)
        cls=next(x for x in parsed.body if isinstance(x,ast.ClassDef) and x.name=='Plugin')
        meth=next(x for x in cls.body if isinstance(x,ast.AsyncFunctionDef) and x.name=='get_idle_messages')
        context={'json':json}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[meth],type_ignores=[])), '<idle>', 'exec'), context)
        self.method=context['get_idle_messages']
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.fake=types.SimpleNamespace(idle_messages_path=Path(self.tmp.name)/'idle-messages.json',_idle_messages_cached=None,_idle_messages_stat=None)
        self.src=json.loads((ROOT/'assets/idle-messages.json').read_text())

    def run_fetch(self):
        return asyncio.run(self.method(self.fake))

    def test_large_editable_pack(self):
        self.fake.idle_messages_path.write_text(json.dumps(self.src),encoding='utf-8')
        r=self.run_fetch()
        self.assertTrue(r['ok'])
        self.assertEqual(r['count'],2048)
        self.assertEqual(len(set(r['messages'])),2048)
        self.assertEqual(self.run_fetch()['count'],2048)

    def test_edits_and_malformed_pack(self):
        self.fake.idle_messages_path.write_text(json.dumps({'messages':['This is the initial line.']}),encoding='utf-8')
        self.assertEqual(self.run_fetch()['messages'],['This is the initial line.'])
        self.fake.idle_messages_path.write_text(json.dumps({'messages':['Another line after update.','Another line after update.','<b>Never interpret HTML as markup!</b>']}),encoding='utf-8')
        r=self.run_fetch()
        self.assertEqual(r['count'],2)
        self.assertTrue(r['ok'])
        self.fake.idle_messages_path.write_text('bad json',encoding='utf-8')
        self.assertFalse(self.run_fetch()['ok'])
        self.assertEqual(self.run_fetch()['count'],3)

if __name__=='__main__':
    unittest.main()
