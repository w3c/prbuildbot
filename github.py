#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This module contains all GitHub interaction logic."""

import ConfigParser
import json
import logging
from urlparse import urljoin

import requests

CONFIG = ConfigParser.ConfigParser()
CONFIG.readfp(open(r'config.txt'))
GH_TOKEN = CONFIG.get('GitHub', 'GH_TOKEN')
ORG = CONFIG.get('GitHub', 'ORG')
REPO = CONFIG.get('GitHub', 'REPO')


class GitHub(object):

    """Interface to GitHub API."""

    max_comment_length = 65536

    def __init__(self):
        """Create GitHub instance."""
        self.headers = {"Accept": "application/vnd.github.v3+json"}
        self.auth = (GH_TOKEN, "x-oauth-basic")
        self.org = ORG
        self.repo = REPO
        self.base_url = "https://api.github.com/repos/%s/%s/" % (ORG, REPO)

    def _headers(self, headers):
        """Extend existing HTTP headers and return new value."""
        if headers is None:
            headers = {}
        return_value = self.headers.copy()
        return_value.update(headers)
        return return_value

    def post(self, url, data, headers=None):
        """Serialize and POST data to given URL."""
        logging.debug("POST %s", url)
        if data is not None:
            data = json.dumps(data)
        resp = requests.post(
            url,
            data=data,
            headers=self._headers(headers),
            auth=self.auth
        )
        resp.raise_for_status()
        return resp

    def patch(self, url, data, headers=None):
        """Serialize and PATCH data to given URL."""
        logging.debug("PATCH %s", url)
        if data is not None:
            data = json.dumps(data)
        resp = requests.patch(
            url,
            data=data,
            headers=self._headers(headers),
            auth=self.auth
        )
        resp.raise_for_status()
        return resp

    def get(self, url, headers=None):
        """Execute GET request for given URL."""
        logging.debug("GET %s", url)
        resp = requests.get(
            url,
            headers=self._headers(headers),
            auth=self.auth
        )
        resp.raise_for_status()
        return resp

    def get_comments_for_user(self, issue_number):
        user = self.get(urljoin(self.base_url, "/user")).json()
        issue_comments_url = urljoin(self.base_url,
                                     "issues/%s/comments" % issue_number)
        return [item for item in self.get(issue_comments_url).json() if
                comment["user"]["login"] == user["login"]]


    def post_comment(self, issue_number, comment_id, body):
        """Create or update comment in pull request comment section."""
        issue_comments_url = urljoin(self.base_url,
                                     "issues/%s/comments" % issue_number)

        if len(body) > self.max_comment_length:
            truncation_msg = ('*This report has been truncated because the ' +
                'total content is %s characters in length, which is in ' +
                'excess of GitHub.com\'s limit for comments (%s ' +
                'characters).\n\n') % (len(body), self.max_comment_length)

            body = truncation_msg + \
                body[0:self.max_comment_length - len(truncation_msg)]

        data = {"body": body}

        if comment_id is not None:
            comment_url = urljoin(self.base_url,
                                  "issues/comments/%s" % comment["id"])
            return self.patch(comment_url, data)

        return self.post(issue_comments_url, data)
