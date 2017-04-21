import re

comment_marker = "<!--PRBUILDBOT:COMMENT-->"
section_start = "<!--PRBUILDBOT:START:%s-->"
section_start_re = re.compile("^%s$" % (section_start % "([^\-]*)"))
section_end = "<!--PRBUILDBOT:END-->"

def unescape_comment(comment):
    return comment.replace("\\2d", "-")


def escape_comment(comment):
    return comment.replace("-", "\\2d")


class Section(object):
    def __init__(self):
        self.title = None
        self.body_lines = []

    @property
    def body(self):
        return "\n".join(self.body_lines)

    @property
    def empty(self):
        return self.title is None and not self.body_lines

    def append(self, line):
        self.body_lines.append(line)


class CommentParser(object):
    def __init__(self):
        self.state = None
        self.current = None
        self.rv = None

    def parse(self, body):
        self.current = Section()
        self.state = self.outside_section
        self.rv = []

        lines = body.split("\n")
        if lines[0] != comment_marker:
            raise ValueError("Comment did not start with expected marker")

        for line in lines[1:]:
            self.state(line)

        self.finish_section()

        return self.rv

    def finish_section(self):
        if not self.current.empty:
            self.rv.append(self.current)
            self.current = Section()

    def outside_section(self, line):
        m = section_start_re.match(line)
        
        if m:
            title = unescape_comment(m.group(1))
            self.finish_section()
            self.current.title = title
            self.state = self.in_section
        else:
            self.current.append(line)

    def in_section(self, line):
        if line == section_end:
            self.finish_section()
            self.state = self.outside_section
        else:
            self.current.append(line)


def find(comments):
    """Find an existing comment posted by the bot.

    :param: comments"""
    for comment in comments:
        body = comment["body"].strip()

        if body.split("\n")[0] == self.comment_marker:
            return comment
    return None


def write(logs, existing):
    if existing:
        sections = parse(existing["body"])
    else:
        sections = []
    update(sections, logs)
    return create_body(sections)


def parse(body):
    """Parse a comment that was made by this bot.

    :param body: String containing the comment text
    :retval: List of Section objects  corresponding to the comment
    """

    parser = CommentParser()
    return parser.parse(body)


def update(sections, logs):
    """Perform an in-place update of a list of sections from an existing
    comment.

    :param sections: A list of Section objects
    :param logs: A list of dictionaries from parsing logs
    """
    sections_by_title = {item.title: item for item in sections}
    for item in logs:
        target = sections_by_title.get(item["title"])
        if target is None:
            target = Section()
            target.title = item["title"]
            sections.append(target)
        target.body_lines = format_body(item)


def format_body(log):
    rv = [format_comment_title(log["title"]), ""]
    rv.extend(log["text"].split("\n"))
    rv.append("")
    if log.get("log_url"):
        rv.append("[Job log](%s)" % log["log_url"])
        rv.append("")
    return rv


def create_body(sections):
    body = [comment_marker]

    for section in sections:
        if section.title is not None:
            body.append(section_start % escape_comment(section.title))
            body.extend(section.body_lines)
            body.append(section_end)
        else:
            body.extend(section.body_lines)

    return "\n".join(body)


# TODO: Find a way around this w3c/web-platform-tests -specific way of
# handling title/finding the previous comments.
# This currently _must_ match the function of the same name in
# w3c/web-platform-tests/check_stability.py
def format_comment_title(product):
    """
    Produce a Markdown-formatted string based on a given product.

    Returns a string containing a browser identifier optionally followed
    by a colon and a release channel. (For example: "firefox" or
    "chrome:dev".) The generated title string is used both to create new
    comments and to locate (and subsequently update) previously-submitted
    comments.
    """
    parts = product.split(":")
    title = parts[0].title()

    if len(parts) > 1:
        title += " (%s channel)" % parts[1]

    return "# %s #" % title
