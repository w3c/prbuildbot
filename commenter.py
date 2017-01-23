import ConfigParser
import requests

from flask import Flask
app = Flask(__name__)


config = ConfigParser.ConfigParser()
config.readfp(open(r'config.txt'))
TRAVIS_URL = config.get('Travis', 'TRAVIS_URL')


def _get_travis_public_key():
    """ Return the PEM-encoded public key from Travis CI /config endpoint."""
    response = requests.get("%s/config" % TRAVIS_URL, timeout=10.0)
    response.raise_for_status()
    return response.json()['config']['notifications']['webhook']['public_key']


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/stability/travis', methods=['POST'])
def travis():
    """Respond to Travis webhook."""
    return _get_travis_public_key()

if __name__ == '__main__':
    app.run(debug=True)
