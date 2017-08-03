#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This module contains Travis CI log-parsing logic.

This should be customized by the developer to pull out the relevant
parts of the log they would like to post as GitHub comments.

The following example parses the logs for w3c/web-platform-tests.
"""

import re


def parse_logs(logs):
    """Extract and return relevant info from log."""
    comments = []
    for log in logs:

        log_lines = log['data'].splitlines()
        comment_lines = []
        match_regex = r'^([A-Z])+(:.*check_stability:|:lint:)'
        for line in log_lines:
            if re.search(match_regex, line) and 'DEBUG:' not in line:

                # Add a newline before the Subtest Results table
                # There's probably a more robust way to do this check.
                if 'Subtest' in line:
                    comment_lines.append('\n')
                comment_lines.append(line)

        # Remove the <LOG_LEVEL>:check_stability: strings at the
        # beginning of every line
        comment_text = re.sub(match_regex,
                              '',
                              '\n'.join(comment_lines),
                              flags=re.MULTILINE)

        # Don't comment on passing lint jobs
        if log['title'] == 'lint' and len(comment_text) == 0:
            continue

        comments.append({
            'job_id': log['job_id'],
            'title': log['title'],
            'text': comment_text
        })
    return comments
