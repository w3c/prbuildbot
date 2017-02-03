import unittest
from log_parser import parse_logs


class LogParserTestCase(unittest.TestCase):

    """Test case for log_parser module."""

    def test_empty_dict(self):
        self.assertEqual(parse_logs([]),
                         [],
                         'It should return an empty dict if passed an empty list.')

    def test_non_debug_level(self):
        self.assertEqual(parse_logs([{'job_id': 3, 'title': 'firefox', 'data': 'ABCDE:check_stability:Hello World'}]),
                         [{'job_id': 3, 'title': 'firefox', 'text': 'Hello World'}],
                         'It should include non-debug log statements that include ":check_stability:".')

    def test_debug_level(self):
        self.assertEqual(parse_logs([{'job_id': 5, 'title': 'firefox', 'data': 'DEBUG:check_stability:Hello World'}]),
                         [{'job_id': 5, 'title': 'firefox', 'text': ''}],
                         'It should exclude debug log statements that include ":check_stability:".')

    def test_non_check_stability(self):
        self.assertEqual(parse_logs([{'job_id': 8, 'title': 'firefox', 'data': 'Hello World!'}]),
                         [{'job_id': 8, 'title': 'firefox', 'text': ''}],
                         'It should exclude lines that do not include ":check_stability:"')

    def test_multi_line(self):
        self.assertEqual(parse_logs([{'job_id': 9, 'title': 'firefox', 'data': 'Hello World!\nERROR:check_stability:Goodbye Cruel World!'}]),
                         [{'job_id': 9, 'title': 'firefox', 'text': 'Goodbye Cruel World!'}],
                         'It should include and exclude correctly across multiple lines.')

    def test_multi_logs(self):
        self.assertEqual(parse_logs([
                                    {'job_id': 94, 'title': 'firefox', 'data': 'INFO:check_stability:Hello World!\nDEBUG:check_stability:Goodbye Cruel World!'},
                                    {'job_id': 32, 'title': 'chrome', 'data': 'DEBUG:check_stability:Hello World!\nWARNING:check_stability:Goodbye Cruel World!'}
                                    ]),
                         [
                             {'job_id': 94, 'title': 'firefox', 'text': 'Hello World!'},
                             {'job_id': 32, 'title': 'chrome', 'text': 'Goodbye Cruel World!'}
                         ],
                         'It should include and exclude correctly across multiple logs.')

    def test_new_line(self):
        self.assertEqual(parse_logs([
                                    {'job_id': 83, 'title': 'firefox', 'data': 'INFO:check_stability:Hello World!\nWARNING:check_stability:Goodbye Cruel World!'},
                                    {'job_id': 88, 'title': 'chrome', 'data': 'INFO:check_stability:Hello World!\nWARNING:check_stability:Goodbye Cruel World!'}
                                    ]),
                         [
                             {'job_id': 83, 'title': 'firefox', 'text': 'Hello World!\nGoodbye Cruel World!'},
                             {'job_id': 88, 'title': 'chrome', 'text': 'Hello World!\nGoodbye Cruel World!'}
                         ],
                         'It should include newline characters as appropriate.')

if __name__ == '__main__':
    unittest.main()
