"""Parser gates, synthetic only; external source results are not inspected."""
import unittest
from research.q3.rc42.external_tls_first import strict_tls_adapter
from research.q3.rc41.external_mqtt_first import PublishedMachine

TINY='''digraph {
1
0
1 -> 0 [label="Ping/Pong"]
1 -> 1 [label="Stop/Ok"]
0 -> 0 [label="Ping/Pong"]
0 -> 1 [label="Stop/Ok"]
}'''

class TlsAdapter(unittest.TestCase):
    def test_numeric_initial_state_and_io_semantics(self):
        model=PublishedMachine(strict_tls_adapter(TINY,2,2,2),2)
        self.assertEqual(model.states,2)
        self.assertEqual(model.edge_count,4)
        self.assertEqual(model.initial,1)
        self.assertEqual(len(model.run("ABBA")),4)

    def test_frozen_bound_rejects(self):
        with self.assertRaises(ValueError):
            strict_tls_adapter(TINY,3,2,2)

    def test_missing_transition_rejected(self):
        with self.assertRaises(ValueError):
            strict_tls_adapter(TINY.replace('0 -> 1 [label="Stop/Ok"]',''),2,2,2)

    def test_duplicate_edge_rejected(self):
        duplicate=TINY.replace('0 -> 1 [label="Stop/Ok"]',
             '0 -> 1 [label="Stop/Ok"]\n0 -> 0 [label="Stop/Ok"]')
        with self.assertRaises(ValueError):
            PublishedMachine(strict_tls_adapter(duplicate,2,2,2),2)

    def test_source_change_to_unrecognized_line_rejected(self):
        with self.assertRaises(ValueError):
            strict_tls_adapter(TINY.replace("digraph {","graph {"),2,2,2)

    def test_bad_label_rejected(self):
        with self.assertRaises(ValueError):
            strict_tls_adapter(TINY.replace("Ping/Pong","PingPong"),2,2,2)

if __name__=='__main__':
    unittest.main()
