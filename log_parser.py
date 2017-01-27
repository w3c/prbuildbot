#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This module contains Travis CI log-parsing logic.

This should be customized by the developer to pull out the relevant
parts of the log they would like to post as GitHub comments.

The following example parses the logs for w3c/web-platform-tests.
"""

import re
from collections import OrderedDict


def parse_logs(logs):
    """Extract and return relevant info from log."""
    comments = {}
    for title, log in logs.iteritems():

        # The log currently duplicates each line in the log.
        # Split the lines, convert to an OrderedDict to remove
        # duplicates while maintaining order, and turn it back into a
        # list.
        # Note: This may incorrectly assume there are no duplications
        #       that we _do_ want.
        log_lines = list(OrderedDict.fromkeys(log.splitlines()))
        comment_lines = []
        for line in log_lines:
            if ':check_stability:' in line and 'DEBUG:' not in line:

                # Add a newline before the Subtest Results table
                # There's probably a more robust way to do this check.
                if 'Subtest' in line:
                    comment_lines.append('\n')
                comment_lines.append(line)

        # Remove the <LOG_LEVEL>:check_stability: strings at the
        # beginning of every line
        comment_text = re.sub(r'^([A-Z])+:check_stability:',
                              '',
                              '\n'.join(comment_lines),
                              flags=re.MULTILINE)

        comments[title] = comment_text
    return comments
