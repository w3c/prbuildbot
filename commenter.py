#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Flask server to listen for Travis webhooks and post GitHub PR comments."""
import ConfigParser
import base64

import requests
from OpenSSL.crypto import verify, load_publickey, FILETYPE_PEM, X509
from OpenSSL.crypto import Error as SignatureError

from flask import Flask, request

app = Flask(__name__)

config = ConfigParser.ConfigParser()
config.readfp(open(r'config.txt'))
TRAVIS_URL = config.get('Travis', 'TRAVIS_URL')


def _check_authorized(signature, public_key, payload):
    """Reformat PEM-encoded public key for pyOpenSSL, then verify signature."""
    pkey_public_key = load_publickey(FILETYPE_PEM, public_key)
    certificate = X509()
    certificate.set_pubkey(pkey_public_key)
    verify(certificate, signature, payload, str('sha1'))


def _get_signature(req):
    """Extract raw bytes of the request signature from Travis."""
    signature = req.headers['SIGNATURE']
    return base64.b64decode(signature)


def _get_travis_public_key():
    """Return the PEM-encoded public key from Travis CI /config endpoint."""
    response = requests.get("%s/config" % TRAVIS_URL, timeout=10.0)
    response.raise_for_status()
    return response.json()['config']['notifications']['webhook']['public_key']


@app.route('/stability/travis', methods=['POST'])
def travis():
    """Respond to Travis webhook."""
    # TEST SIGNATURE
    # signature = 'vnOOLXsHXZh75AYErDoE30fNSfBDHaolIBwkNiH7EASJiyBpZ0b2jVWyiEDlqK2SP9RCUAHpGNdN4wO8BZhFs/WSgAUStM4DX2+baUIghHXDaQBNABHjI53nWo8xtloG1deuUHs1ZiPezQiRTpCz5LM+tBTvQcuNyQlE8X7XDuE8CNWVq5FD+ZdW1Q+jmhRmNJyFqUFKKux1X9lYEvxKCwfbXQz08Tb6JYyuC/q/zIwc7zaz3s3I9W5VIQd2DvYT7VMLM0aSV8fppLno7DoVLUabdnAnjQeMTlMLIqUCsS85p9TVbzomL7FpxTqIkuOSJteV9tb6pvGGPuKcW2lBlw=='
    signature = _get_signature(request)
    # TEST PAYLOAD
    # payload = '{"a":"Hello","b":"World"}'
    payload = request.form['payload']
    try:
        # TEST PUBLIC KEY
        # public_key = '-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA1mTMThevVTEmDKwaKcDB\ndsa9LSqowZ8aR+6M7l/GTGw/Q6faASDHYiV6bR7y20KbgeSiBE3HJGBeXtKPnjrG\nSiEoPXCSPIwRK2ZrOlsSwiEqRVRM1nuDw97gk0KxC9rvHyFizUGBhuiGAiKi/JHi\niEPWMflG9YQzsLDciiXm0SXazktktW5O9MMBmwdLsljGqeiwnlfRbmG5mi95sbSi\nZForhrsuATOA2paMmr15Ch29MWnm1U/1rsqF7sDvE/JTo2ZSFxUY7959KH+zXdGk\n5b631Jgdx/QEedP/JydeyJw5mLvY1UfZ2vzCkgEoQytI43Uoz9NQvzkqFcVRzZ9j\nAwIDAQAB\n-----END PUBLIC KEY-----\n'
        public_key = _get_travis_public_key()
    except (requests.Timeout, requests.RequestException):
        return "Failed to retrieve Travis CI public key", 500

    try:
        _check_authorized(signature, public_key, payload)
    except SignatureError:
        return "Bad Travis CI Signature", 401

#    json_payload = json.loads(payload)
    return public_key

if __name__ == '__main__':
    app.run(debug=True)
