#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Flask server to listen for Travis webhooks and post GitHub PR comments."""

from github import GitHub
from travis import Travis
from log_parser import parse_logs

import requests

from flask import Flask, request

app = Flask(__name__)


@app.route('/prbuildbot/travis', methods=['POST'])
def bot():
    """Respond to Travis webhook."""
    travis = Travis(app.logger)
    github = GitHub(app.logger)

    # The payload comes in the request, but we need to make sure it is
    # really signed by Travis CI. If not, respond to this request with
    # an error.
    verified_payload = travis.get_verified_payload(request)
    error = verified_payload.get('error')
    if error:
        return error.get('message'), error.get('code')

    issue_number = int(verified_payload.get('pull_request_number'))
    logs = travis.get_logs(verified_payload)

    comments = parse_logs(logs)

    # Create a separate comment for every job
    for title, comment in comments.iteritems():
        try:
            github.post_comment(issue_number,
                                comment,
                                title)
        except requests.RequestException as err:
            app.logger.error(err.response.text)
            return err.response.text, 500

    return "OK"


if __name__ == '__main__':
    app.run(debug=True)
