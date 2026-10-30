import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core import Pager, Queue, pick_surprise, clean_discovery, media_kind

def items(n):
    return [{"ratingKey": str(i), "title": f"Track {i}", "libraryRole": "music"} for i in range(n)]

class PagingTests(unittest.TestCase):
    def test_156_albums_are_reachable(self):
        pager = Pager(page_size=48)
        all_rows = items(156)
        for start in (0,48,96,144):
            request = pager.start()
            self.assertEqual(request, (0,start))
            segment = all_rows[start:start+48]
            self.assertTrue(pager.receive(request[0],{"success":True,"items":segment,
                "offset":start,"total":156,"hasMore":start+len(segment)<156}))
        self.assertEqual(len(pager.rows),156)
        self.assertEqual(pager.total,156)
        self.assertFalse(pager.has_more)
        self.assertIsNone(pager.start())

    def test_old_response_does_not_break_new_view(self):
        p=Pager()
        old=p.start()
        p.reset("music","artists")
        self.assertFalse(p.receive(old[0],{"success":True,"items":items(6),"total":6}))
        self.assertEqual(p.offset,0)
        self.assertEqual(p.rows,[])

class QueueTests(unittest.TestCase):
    def test_no_duplicate_queue_advance_at_end(self):
        q=Queue()
        q.replace(items(3))
        self.assertEqual(q.advance()["ratingKey"],"1")
        self.assertEqual(q.advance()["ratingKey"],"2")
        self.assertIsNone(q.advance())
        q.repeat="all"
        self.assertEqual(q.advance()["ratingKey"],"0")

    def test_play_next_and_previous(self):
        q=Queue()
        q.replace(items(4))
        q.enqueue(items(2),next_up=True)
        self.assertEqual(len(q.tracks),6)
        q.advance()
        self.assertEqual(q.current["ratingKey"],"0")
        q.previous()
        self.assertEqual(q.index,0)

    def test_repeat_one_only_automatic(self):
        q=Queue()
        q.replace(items(3))
        q.repeat="one"
        self.assertEqual(q.candidate(),0)
        self.assertEqual(q.candidate(manual=True),1)

class DiscoveryTests(unittest.TestCase):
    def test_surprise_limits_and_recent(self):
        chosen=pick_surprise(items(30),10,["1","2"])
        self.assertEqual(len(chosen),10)
        self.assertNotIn("1",[x["ratingKey"] for x in chosen])
    def test_defaults(self):
        self.assertEqual(clean_discovery()["crossfade"],8)
        self.assertEqual(clean_discovery({"crossfade":200})["crossfade"],8)
        self.assertEqual(media_kind({"libraryRole":"audiobooks"}),"audiobook")

if __name__=="__main__":
    unittest.main()
