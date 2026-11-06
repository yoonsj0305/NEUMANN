"""Opened software controls only, no external model scoring."""
import unittest

from research.q3.rc41.external_mqtt_first import PublishedMachine


SIMPLE = '''digraph g {
  s0 -> s1 [label="Connect / Ack"];
  s0 -> s0 [label="Ping / Fail"];
  s1 -> s1 [label="Connect / Busy"];
  s1 -> s0 [label="Ping / Pong"];
__start0 -> s0;
}'''


class ExternalModelParser(unittest.TestCase):
    def test_strict_complete_and_reset(self):
        target=PublishedMachine(SIMPLE,2)
        self.assertEqual(target.states,2)
        self.assertEqual(target.edge_count,4)
        self.assertEqual(len(target.alphabet),2)
        self.assertEqual(target.run("ABA"),target.run("ABA"))
        self.assertEqual(len(target.run("ABA")),3)

    def test_non_deterministic_rejected(self):
        with self.assertRaisesRegex(ValueError,"NONDETERMINISTIC"):
            PublishedMachine(SIMPLE.replace('__start0 -> s0;',
                 's0 -> s1 [label="Connect / Ack"];\n__start0 -> s0;'),2)

    def test_incomplete_rejected(self):
        with self.assertRaisesRegex(ValueError,"INCOMPLETE"):
            PublishedMachine(SIMPLE.replace('  s1 -> s0 [label="Ping / Pong"];',''),2)

    def test_wrong_published_state_bound_rejected(self):
        with self.assertRaisesRegex(ValueError,"OUT_OF_FROZEN"):
            PublishedMachine(SIMPLE,1)

    def test_missing_reset_rejected(self):
        with self.assertRaisesRegex(ValueError,"EMPTY_OR_MISSING"):
            PublishedMachine(SIMPLE.replace("__start0 -> s0;",""),2)

    def test_unrecognized_dot_edge_rejected(self):
        with self.assertRaisesRegex(ValueError,"UNRECOGNIZED"):
            PublishedMachine(SIMPLE.replace("s0 -> s1 [label=",
                                               "s0 -> s1 [tooltip="),2)


if __name__=="__main__":
    unittest.main()
