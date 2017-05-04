#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This module contains the TravisCI webhook handler."""

import ConfigParser
from github import GitHub
from travis import Travis
from log_parser import parse_logs

import logging
import requests

logging.basicConfig(filename='prbuildbot.log', level=logging.DEBUG)

CONFIG = ConfigParser.ConfigParser()
CONFIG.readfp(open(r'config.txt'))
GH_TOKEN = CONFIG.get('GitHub', 'GH_TOKEN')
ORG = CONFIG.get('GitHub', 'ORG')
REPO = CONFIG.get('GitHub', 'REPO')


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

    # Ensure only builds for this repository can comment here.
    repository = verified_payload.get("repository")
    owner_name = repository.get("owner_name")
    repo_name = repository.get("name")
    if owner_name != ORG or repo_name != REPO:
        return "Forbidden: Repository Mismatch. Build for %s/%s attempting to comment on %s/%s" % (owner_name, repo_name, ORG, REPO), 403

    issue_number = int(verified_payload.get('pull_request_number'))
    logs = travis.get_logs(verified_payload)

    comments = parse_logs(logs)

    # Create a separate comment for every job
    for comment in comments:
        try:
            log_url = Travis.job_url(github.org, github.repo,
                                     comment['job_id'])
            github.post_comment(issue_number,
                                comment['text'],
                                comment['title'],
                                log_url)
        except requests.RequestException as err:
            logging.error(err.response.text)
            return err.response.text, 500

    return "OK", 200
