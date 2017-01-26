#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This module contains all Travis CI interaction logic."""

import ConfigParser
import base64
import json
from urlparse import urljoin

import requests
from OpenSSL.crypto import verify, load_publickey, FILETYPE_PEM, X509
from OpenSSL.crypto import Error as SignatureError

CONFIG = ConfigParser.ConfigParser()
CONFIG.readfp(open(r'config.txt'))
TRAVIS_URL = CONFIG.get('Travis', 'TRAVIS_URL')


def check_authorized(signature, public_key, payload):
    """Reformat PEM-encoded public key for pyOpenSSL, verify signature."""
    pkey_public_key = load_publickey(FILETYPE_PEM, public_key)
    certificate = X509()
    certificate.set_pubkey(pkey_public_key)
    verify(certificate, signature, payload, str('sha1'))


def get_signature(req):
    """Extract raw bytes of the request signature from Travis."""
    signature = req.headers['SIGNATURE']
    return base64.b64decode(signature)


class Travis(object):

    """Interface to GitHub API."""

    def __init__(self, logger):
        """Create Travis instance."""
        self.logger = logger
        self.base_url = TRAVIS_URL

    def get_build_log(self, job_id):
        """Retrieve and return log from Travis CI API."""
        response = requests.get(urljoin(self.base_url,
                                        "/jobs/%s/log" % job_id),
                                timeout=10.0)
        response.raise_for_status()
        return response.text

    def get_public_key(self):
        """Return PEM-encoded public key from Travis CI /config endpoint."""
        response = requests.get(urljoin(self.base_url, '/config'),
                                timeout=10.0)
        response.raise_for_status()
        config = response.json()['config']
        public_key = config['notifications']['webhook']['public_key']
        self.logger.debug("Travis Public Key: %s", public_key)
        return public_key

    def get_verified_payload(self, request):
        """Verify payload with Travis CI signature and public key."""
        payload = request.form['payload']
        self.logger.debug("Payload: %s", payload)
        signature = get_signature(request)
        try:
            public_key = self.get_public_key()
        except requests.Timeout:
            error_message = "Timed out retrieving Travis CI public key."
            self.logger.error({"message": error_message})
            return {"error": {"message": error_message, "code": 500}}
        except requests.RequestException as err:
            error_message = "Failed to retrieve Travis CI public key."
            self.logger.error({
                "message": error_message,
                "error": err.message
            })
            return {"error": {"message": error_message, "code": 500}}
        try:
            check_authorized(signature, public_key, payload)
        except SignatureError as err:
            error_message = "Failed to confirm Travis CI Signature."
            self.logger.error({
                "message": error_message,
                "error": err.message
            })
            return {"error": {"message": error_message, "code": 401}}
        return json.loads(payload)

