#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Flask server to listen for Travis webhooks and post GitHub PR comments."""

import urllib

from webhook_handler import webhook_handler
from wptserve import server
from wptserve.handlers import handler


@handler
def travis_handler(request, response):
    """Respond with the output of the webhook handler."""
    payload = urllib.unquote_plus(request.body).split('payload=')[1]
    signature = request.headers.get('signature')
    message, code = webhook_handler(payload, signature)
    return code, [("Content-Type", "text/plain")], message


httpd = server.WebTestHttpd(host='45.55.224.178',
                            doc_root='.',
                            port=80,
                            routes=[
                                ("POST", "/prbuildbot/travis/", travis_handler)
                            ])

if __name__ == '__main__':
    httpd.start(block=True)
