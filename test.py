import unittest
from log_parser import parse_logs


class LogParserTestCase(unittest.TestCase):

    """Test case for log_parser module."""

    def test_empty_dict(self):
        self.assertEqual(parse_logs({}),
                         {},
                         'It should return an empty dict if passed an empty dict.')

    def test_non_debug_level(self):
        self.assertEqual(parse_logs({'firefox': 'ABCDE:check_stability:Hello World'}),
                         {'firefox': 'Hello World'},
                         'It should include non-debug log statements that include ":check_stability:".')

    def test_debug_level(self):
        self.assertEqual(parse_logs({'firefox': 'DEBUG:check_stability:Hello World'}),
                         {'firefox': ''},
                         'It should exclude debug log statements that include ":check_stability:".')

    def test_non_check_stability(self):
        self.assertEqual(parse_logs({'firefox': 'Hello World!'}),
                         {'firefox': ''},
                         'It should exclude lines that do not include ":check_stability:"')

    def test_multi_line(self):
        self.assertEqual(parse_logs({'firefox': 'Hello World!\nERROR:check_stability:Goodbye Cruel World!'}),
                         {'firefox': 'Goodbye Cruel World!'},
                         'It should include and exclude correctly across multiple lines.')

    def test_multi_logs(self):
        self.assertEqual(parse_logs({
                                    'firefox': 'INFO:check_stability:Hello World!\nDEBUG:check_stability:Goodbye Cruel World!',
                                    'chrome': 'DEBUG:check_stability:Hello World!\nWARNING:check_stability:Goodbye Cruel World!'
                                    }),
                         {'firefox': 'Hello World!', 'chrome': 'Goodbye Cruel World!'},
                         'It should include and exclude correctly across multiple logs.')

    def test_new_line(self):
        self.assertEqual(parse_logs({'firefox': 'INFO:check_stability:Hello World!\nWARNING:check_stability:Goodbye Cruel World!',
                                     'chrome': 'INFO:check_stability:Hello World!\nWARNING:check_stability:Goodbye Cruel World!'}),
                         {'firefox': 'Hello World!\nGoodbye Cruel World!',
                          'chrome': 'Hello World!\nGoodbye Cruel World!'},
                         'It should include newline characters as appropriate.')

if __name__ == '__main__':
    unittest.main()
