import unittest
from log_parser import parse_logs
from comment import CommentParser, Section, update, create_body

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


class CommentParserTestCase(unittest.TestCase):
    def compare(self, comment, expected):
        parser = CommentParser()
        actual = parser.parse(comment)
        self.assertEqual(len(actual), len(expected))
        for a, e in zip(actual, expected):
            self.assertEqual(a.title, e[0])
            self.assertEqual(a.body, e[1])

    def test_0(self):
        comment = """<!--PRBUILDBOT:COMMENT-->
Before first
<!--PRBUILDBOT:START:first\\2dsection-->
In first
In first 2
<!--PRBUILDBOT:END-->
After first
<!--PRBUILDBOT:START:second-->
In second
<!--other comment-->
End not at start of line<!--PRBUILDBOT:END-->
<!--PRBUILDBOT:END-->
After second
"""
        expected = [(None, "Before first"),
                    ("first-section", "In first\nIn first 2"),
                    (None, "After first"),
                    ("second", "In second\n<!--other comment-->\nEnd not at start of line<!--PRBUILDBOT:END-->"),
                    (None, "After second\n")]

        self.compare(comment, expected)


class TestUpdateComment(unittest.TestCase):
    def test_0(self):
        sections_data = [(None, "0"), ("leave1", "1"), ("update1", "2"), ("update2", "3"), ("leave2", "4")]
        logs = [{"title": "update1", "text": "update1", "log_url": "http://example.org"},
                {"title": "update2", "text": "update2"}]
        sections = []


        expected = [(None, "0"),
                    ("leave1", "1"),
                    ("update1", "# Update1 #\n\nupdate1\n\n[Job log](http://example.org)\n"),
                    ("update2", "# Update2 #\n\nupdate2\n"),
                    ("leave2", "4")]

        for title, body in sections_data:
            section = Section()
            section.title = title
            section.body_lines = body.split("\n")
            sections.append(section)

        update(sections, logs)

        self.assertEquals(len(sections), len(expected))

        for a, e in zip(sections, expected):
            self.assertEquals(a.title, e[0])
            self.assertEquals(a.body, e[1])


class TestCommentBody(unittest.TestCase):
    def test_0(self):
        sections_data = [(None, "leading"),
                         ("section-1", "Line1\nLine2"),
                         ("section2", "Line3\nLine4\n"),
                         (None, "trailing")]

        sections = []
        for title, body in sections_data:
            section = Section()
            section.title = title
            section.body_lines = body.split("\n")
            sections.append(section)

        expected = """<!--PRBUILDBOT:COMMENT-->
leading
<!--PRBUILDBOT:START:section\\2d1-->
Line1
Line2
<!--PRBUILDBOT:END-->
<!--PRBUILDBOT:START:section2-->
Line3
Line4

<!--PRBUILDBOT:END-->
trailing"""

        actual = create_body(sections)
        self.assertEquals(actual, expected)


if __name__ == '__main__':
    unittest.main()
