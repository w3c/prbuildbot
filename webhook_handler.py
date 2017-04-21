#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This module contains the TravisCI webhook handler."""

import comment
from github import GitHub
from travis import Travis
from log_parser import parse_logs

import logging
import requests

logging.basicConfig(filename='prbuildbot.log', level=logging.DEBUG)


def webhook_handler(payload, signature):
    """Respond to Travis webhook."""
    travis = Travis()
    github = GitHub()

    # The payload comes in the request, but we need to make sure it is
    # really signed by Travis CI. If not, respond to this request with
    # an error.
    verified_payload = travis.get_verified_payload(payload, signature)
    error = verified_payload.get('error')
    if error:
        return error.get('message'), error.get('code')

    issue_number = int(verified_payload.get('pull_request_number'))
    logs = travis.get_logs(verified_payload)

    log_data = parse_logs(logs)

    for log in log_data:
        logs["log_url"] = Travis.job_url(github.org, github.repo,
                                         log['job_id'])

    comment_id, existing = comment.find(github.get_comments_for_user(issue_number))
    body = comment.write(logs, existing)


    try:
        github.post_comment(issue_number, logs)
    except requests.RequestException as err:
        logging.error(err.response.text)
        return err.response.text, 500

    return "OK", 200
