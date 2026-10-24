import json
import unittest
from canlint import lint

class CanLintTests(unittest.TestCase):
    def test_valid_definition(self):
        with open("examples/network.json",encoding="utf-8") as handle: definition=json.load(handle)
        self.assertEqual(lint(definition),[])
    def test_duplicate_and_overlap(self):
        errors=lint({"frames":[{"id":1,"dlc":1,"signals":[{"name":"a","start_bit":0,"length":4},{"name":"b","start_bit":3,"length":2}]},{"id":1,"dlc":1,"signals":[]}]})
        self.assertTrue(any("duplicate CAN id" in e for e in errors)); self.assertTrue(any("overlaps" in e for e in errors))
if __name__=="__main__": unittest.main()
