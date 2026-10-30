import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from library_setup import suggested_assignment

class LibrarySetupTests(unittest.TestCase):
    def test_explicit_role(self):
        self.assertEqual(suggested_assignment({"role":"audiobooks"}),"audiobooks")
    def test_ambiguous_not_silently_music(self):
        self.assertEqual(suggested_assignment({"role":"unassigned","title":"Vera Static"}),"other")
    def test_single_unknown_defaults_music(self):
        self.assertEqual(suggested_assignment({"role":"unassigned"},True),"music")
    def test_plex_suggestion(self):
        self.assertEqual(suggested_assignment({"role":"unassigned","suggestedRole":"music"}),"music")

if __name__=="__main__":unittest.main()
