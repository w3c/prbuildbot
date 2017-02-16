#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This module contains all Travis CI interaction logic."""

import ConfigParser
import base64
import logging
import json
from urlparse import urljoin

import requests
from OpenSSL.crypto import verify, load_publickey, FILETYPE_PEM, X509
from OpenSSL.crypto import Error as SignatureError

CONFIG = ConfigParser.ConfigParser()
CONFIG.readfp(open(r'config.txt'))
TRAVIS_URL = CONFIG.get('Travis', 'TRAVIS_URL')
COMMENT_ENV_VAR = CONFIG.get('Travis', 'COMMENT_ENV_VAR')


def check_authorized(signature, public_key, payload):
    """Reformat PEM-encoded public key for pyOpenSSL, verify signature."""
    pkey_public_key = load_publickey(FILETYPE_PEM, public_key)
    certificate = X509()
    certificate.set_pubkey(pkey_public_key)
    verify(certificate, signature, payload, str('sha1'))


class Travis(object):

    """Interface to Travis API."""

    def __init__(self):
        """Create Travis instance."""
        self.base_url = TRAVIS_URL

    def get_job_log(self, job_id):
        """Retrieve and return log from Travis CI API."""
        response = requests.get(urljoin(self.base_url,
                                        "/jobs/%s/log" % job_id),
                                timeout=10.0)
        response.raise_for_status()
        return response.text

    def get_logs(self, payload):
        """Get logs for a PR build."""
        if payload.get('type') != 'pull_request':
            return {}

        jobs = payload.get('matrix')
        logs = {}

        for job in jobs:
            config = job.get('config', {})
            env = config.get('env', [])
            for variable in env:
                if COMMENT_ENV_VAR in variable:
                    job_id = job.get('id')
                    log = self.get_job_log(job_id)
                    logs[variable.partition('=')[2]] = log
                    break
        return logs

    def get_public_key(self):
        """Return PEM-encoded public key from Travis CI /config endpoint."""
        response = requests.get(urljoin(self.base_url, '/config'),
                                timeout=10.0)
        response.raise_for_status()
        config = response.json()['config']
        public_key = config['notifications']['webhook']['public_key']
        logging.debug("Travis Public Key: %s", public_key)
        return public_key

    def get_verified_payload(self, payload, signature):
        """Verify payload with Travis CI signature and public key."""
        decoded_signature = base64.b64decode(signature)
        try:
            public_key = self.get_public_key()
        except requests.Timeout:
            error_message = "Timed out retrieving Travis CI public key."
            logging.error({"message": error_message})
            return {"error": {"message": error_message, "code": 500}}
        except requests.RequestException as err:
            error_message = "Failed to retrieve Travis CI public key."
            logging.error({
                "message": error_message,
                "error": err.message
            })
            return {"error": {"message": error_message, "code": 500}}
        try:
            check_authorized(decoded_signature, public_key, payload)
        except SignatureError as err:
            error_message = "Failed to confirm Travis CI Signature."
            logging.error({
                "message": error_message,
                "error": err.message
            })
            return {"error": {"message": error_message, "code": 401}}
        return json.loads(payload)
