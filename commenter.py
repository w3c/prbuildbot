#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Flask server to listen for Travis webhooks and post GitHub PR comments."""
import ConfigParser
import base64
import json
import re
from collections import OrderedDict
from urlparse import urljoin

import requests
from OpenSSL.crypto import verify, load_publickey, FILETYPE_PEM, X509
from OpenSSL.crypto import Error as SignatureError

from flask import Flask, request

app = Flask(__name__)

CONFIG = ConfigParser.ConfigParser()
CONFIG.readfp(open(r'config.txt'))
TRAVIS_URL = CONFIG.get('Travis', 'TRAVIS_URL')
GH_TOKEN = CONFIG.get('GitHub', 'GH_TOKEN')
ORG = CONFIG.get('GitHub', 'ORG')
REPO = CONFIG.get('GitHub', 'REPO')


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
        app.logger.debug("POST %s", url)
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
        app.logger.debug("PATCH %s", url)
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
        app.logger.debug("GET %s", url)
        resp = requests.get(
            url,
            headers=self._headers(headers),
            auth=self.auth
        )
        resp.raise_for_status()
        return resp

    def post_comment(self, issue_number, body, product):
        """Create or update comment in pull request comment section."""
        user = self.get(urljoin(self.base_url, "/user")).json()
        issue_comments_url = urljoin(self.base_url,
                                     "issues/%s/comments" % issue_number)
        comments = self.get(issue_comments_url).json()
        title_line = format_comment_title(product)
        data = {"body": body}
        for comment in comments:
            if (comment["user"]["login"] == user["login"] and
                    comment["body"].startswith(title_line)):
                comment_url = urljoin(self.base_url,
                                      "issues/comments/%s" % comment["id"])
                self.patch(comment_url, data)
                break
        else:
            self.post(issue_comments_url, data)


def check_authorized(signature, public_key, payload):
    """Reformat PEM-encoded public key for pyOpenSSL, then verify signature."""
    pkey_public_key = load_publickey(FILETYPE_PEM, public_key)
    certificate = X509()
    certificate.set_pubkey(pkey_public_key)
    verify(certificate, signature, payload, str('sha1'))


def comment_to_github(payload):
    """Comment on the PR with extract from log."""
    github = GitHub()
    pull_request = int(payload.get('pull_request_number'))
    jobs = payload.get('matrix')

    for job in jobs:
        config = job.get('config', {})
        env = config.get('env', [])
        for variable in env:
            if 'PRODUCT=' in variable:
                job_id = job.get('id')
                response = requests.get(urljoin(TRAVIS_URL,
                                                "/jobs/%s/log" % job_id),
                                        timeout=10.0)
                response.raise_for_status()
                log = response.text
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


def get_signature(req):
    """Extract raw bytes of the request signature from Travis."""
    signature = req.headers['SIGNATURE']
    return base64.b64decode(signature)


def get_travis_public_key():
    """Return the PEM-encoded public key from Travis CI /config endpoint."""
    response = requests.get(urljoin(TRAVIS_URL, '/config'), timeout=10.0)
    response.raise_for_status()
    public_key = response.json()['config']['notifications']['webhook']['public_key']
    app.logger.debug("Travis Public Key: %s", public_key)
    return public_key


@app.route('/stability/travis', methods=['POST'])
def travis():
    """Respond to Travis webhook."""
    signature = get_signature(request)
    payload = request.form['payload']
    app.logger.debug("Payload: %s", payload)
    try:
        public_key = get_travis_public_key()
    except requests.Timeout:
        app.logger.error({
            "message":
                "Timed out when attempting to retrieve Travis CI public key"
        })
        return "Failed to retrieve Travis CI public key", 500
    except requests.RequestException as err:
        app.logger.error({
            "message": "Failed to retrieve Travis CI public key",
            "error": err.message
        })
        return "Failed to retrieve Travis CI public key", 500
    try:
        check_authorized(signature, public_key, payload)
    except SignatureError as err:
        app.logger.error({
            "message": "Failed to confirm Travis CI Signature.",
            "error": err.message
        })
        app.logger.error("Payload was: %s", payload)
        return "Bad Travis CI Signature", 401

    json_payload = json.loads(payload)

    if json_payload.get('type') == 'pull_request':
        return comment_to_github(json_payload)
    return 'OK'

if __name__ == '__main__':
    app.run(debug=True)

