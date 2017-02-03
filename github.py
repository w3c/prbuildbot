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


class GitHub(object):

    """Interface to GitHub API."""

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

    def post_comment(self, issue_number, body, title, full_log_url):
        """Create or update comment in pull request comment section."""
        user = self.get(urljoin(self.base_url, "/user")).json()
        issue_comments_url = urljoin(self.base_url,
                                     "issues/%s/comments" % issue_number)
        comments = self.get(issue_comments_url).json()
        title_line = format_comment_title(title)
        link = ' [View the complete job log.](%s)' % full_log_url
        data = {"body": "%s\n\n%s" % (link, body)}
        for comment in comments:
            if (comment["user"]["login"] == user["login"] and
                    title_line in comment["body"]):
                comment_url = urljoin(self.base_url,
                                      "issues/comments/%s" % comment["id"])
                return self.patch(comment_url, data)
        return self.post(issue_comments_url, data)
