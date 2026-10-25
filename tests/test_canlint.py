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
    def test_big_endian_uses_motorola_bit_order(self):
        # A pair of adjacent Motorola signals occupies bytes 0 and 1.  The
        # old linear range check incorrectly rejected the second signal.
        definition={"frames":[{"id":1,"dlc":2,"signals":[
            {"name":"byte0","start_bit":7,"length":8,"byte_order":"big"},
            {"name":"byte1","start_bit":15,"length":8,"byte_order":"big"},
        ]}]}
        self.assertEqual(lint(definition),[])

        # The Motorola signal above occupies bits 0..7, so bit 0 must be
        # reported as overlapping when another signal claims it.
        definition["frames"][0]["signals"].append(
            {"name":"overlap","start_bit":0,"length":1}
        )
        errors=lint(definition)
        self.assertTrue(any("overlaps" in error for error in errors))

    def test_dlc_must_be_a_representable_can_payload_length(self):
        # CAN-FD encodes payload lengths 9..11 and 13..15 using DLC values,
        # but those values represent 12 and 16 bytes on the wire.  Treating
        # them as byte lengths would allow an impossible frame definition.
        invalid = lint({"frames":[{"id":1,"dlc":9,"signals":[]}]})
        self.assertTrue(any("valid CAN payload length" in error for error in invalid))

        for dlc in (8, 12, 16, 20, 24, 32, 48, 64):
            self.assertEqual(lint({"frames":[{"id":1,"dlc":dlc,"signals":[]}]}), [])

    def test_malformed_container_types_are_reported_instead_of_crashing(self):
        self.assertTrue(any("top-level JSON object" in error for error in lint([])))
        self.assertTrue(any("frames: must be a list" in error for error in lint({"frames": None})))
        errors = lint({"frames": [None, {"id": 1, "dlc": 8, "signals": None}]})
        self.assertTrue(any("frame must be an object" in error for error in errors))
        self.assertTrue(any("signals: must be a list" in error for error in errors))
        errors = lint({"frames": [{"id": 1, "dlc": 8, "signals": [None]}]})
        self.assertTrue(any("signal must be an object" in error for error in errors))

    def test_oversized_signal_length_is_rejected_before_bit_expansion(self):
        # A malformed length must not make the linter iterate once per bit
        # before discovering that the signal cannot fit in the frame.
        errors = lint({"frames": [{"id": 1, "dlc": 8, "signals": [
            {"name": "malicious", "start_bit": 0, "length": 10**9}
        ]}]})
        self.assertTrue(any("exceeds 8-byte payload" in error for error in errors))
if __name__=="__main__": unittest.main()
