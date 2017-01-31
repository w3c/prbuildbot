#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Flask server to listen for Travis webhooks and post GitHub PR comments."""

from webhook_handler import webhook_handler

from flask import Flask, request

app = Flask(__name__)


@app.route('/prbuildbot/travis', methods=['POST'])
def bot():
    return webhook_handler(request, app.logger)

if __name__ == '__main__':
    app.run(debug=True)
