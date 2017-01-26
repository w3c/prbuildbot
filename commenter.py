#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Flask server to listen for Travis webhooks and post GitHub PR comments."""

import re
from collections import OrderedDict

from github import GitHub
from travis import Travis

from flask import Flask, request

app = Flask(__name__)

TRAVIS = Travis(app.logger)


def comment_to_github(payload):
    """Comment on the PR with extract from log."""
    github = GitHub(app.logger)
    pull_request = int(payload.get('pull_request_number'))
    jobs = payload.get('matrix')

    for job in jobs:
        config = job.get('config', {})
        env = config.get('env', [])
        for variable in env:
            if 'PRODUCT=' in variable:
                job_id = job.get('id')
                log = TRAVIS.get_build_log(job_id)
                log_lines = list(OrderedDict.fromkeys(log.splitlines()))
                comment_lines = []
                for line in log_lines:
                    if ':check_stability:' in line and 'DEBUG:' not in line:
                        if 'Subtest' in line:
                            comment_lines.append('\n')
                        comment_lines.append(line)
                github.post_comment(pull_request,
                                    re.sub(r'^([A-Z])+:check_stability:',
                                           '',
                                           '\n'.join(comment_lines),
                                           flags=re.MULTILINE),
                                    variable.split('=')[1])
                break
    return "Commented on %s" % pull_request


@app.route('/stability/travis', methods=['POST'])
def bot():
    """Respond to Travis webhook."""
    verified_payload = TRAVIS.get_verified_payload(request)

    error = verified_payload.get('error')
    if error:
        return error['message'], error['code']

    if verified_payload.get('type') == 'pull_request':
        return comment_to_github(verified_payload)

    return 'OK'

if __name__ == '__main__':
    app.run(debug=True)

