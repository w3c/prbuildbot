#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Flask server to listen for Travis webhooks and post GitHub PR comments."""

from webhook_handler import webhook_handler

from flask import Flask, request

app = Flask(__name__)


@app.route('/prbuildbot/travis', methods=['POST'])
def bot():
    """Respond with the output of the webhook handler."""
    payload = request.form['payload']
    signature = request.headers['SIGNATURE']
    return webhook_handler(payload, signature)

if __name__ == '__main__':
    app.run(debug=True)
