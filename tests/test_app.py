#testapp.py
import pytest, flask
from flask_wtf.csrf import generate_csrf
from flask.testing import FlaskClient as BaseFlaskClient
from app import create_app
# configure test_client to handle CSRF tokens properly
# according to https://gist.github.com/singingwolfboy/2fca1de64950d5dfed72

# Flask's assumptions about an incoming request don't quite match up with
# what the test client provides in terms of manipulating cookies, and the
# CSRF system depends on cookies working correctly. This little class is a
# fake request that forwards along requests to the test client for setting
# cookies.
class RequestShim(object):
    """
    A fake request that proxies cookie-related methods to a Flask test client.
    """
    def __init__(self, client):
        self.client = client
        self.vary = set({})

    def set_cookie(self, key, value='', *args, **kwargs):
        """Set the cookie on the Flask test client."""
        server_name = flask.current_app.config['SERVER_NAME'] or 'localhost'
        return self.client.set_cookie(
            server_name, key=key, value=value, *args, **kwargs
        )

    def delete_cookie(self, key, *args, **kwargs):
        """Delete the cookie on the Flask test client."""
        server_name = flask.current_app.config['SERVER_NAME'] or 'localhost'
        return self.client.delete_cookie(
            server_name, key=key, *args, **kwargs
        )


# We're going to extend Flask's built-in test client class, so that it knows
# how to look up CSRF tokens for you!
class FlaskClient(BaseFlaskClient):
    @property
    def csrf_token(self):
        # First, we'll wrap our request shim around the test client, so that
        # it will work correctly when Flask asks it to set a cookie.
        request = RequestShim(self)
        # Next, we need to look up any cookies that might already exist on
        # this test client, such as the secure cookie that powers `flask.session`,
        # and make a test request context that has those cookies in it.
        environ_overrides = {}
        self.cookie_jar.inject_wsgi(environ_overrides)
        with flask.current_app.test_request_context(
                '/auth/login', environ_overrides=environ_overrides,
            ):
            # Now, we call Flask-WTF's method of generating a CSRF token...
            csrf_token = generate_csrf()
            # ...which also sets a value in `flask.session`, so we need to
            # ask Flask to save that value to the cookie jar in the test
            # client. This is where we actually use that request shim we made!
            flask.current_app.session_interface.save_session(flask.current_app, flask.session, request)
            # And finally, return that CSRF token we got from Flask-WTF.
            return csrf_token

    def login(self, username='test', password='test'):
        return self.post_csrf('/auth/login', username=username, password=password, remember_me=False)

    def logout(self):
        return self.get('/auth/logout', follow_redirects=True)


def post_csrf(self, url, **kwargs):
    """Generic post with csrf_token to test all form submissions of my flask app"""
    data = kwargs.pop("data", {})
    data["csrf_token"] = self.csrf_token
    follow_redirects = kwargs.pop("follow_redirects", True)

    return self.post(url, data=data, follow_redirects=follow_redirects, **kwargs)

@pytest.fixture()
def app():
    app = create_app()
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()

def test_get_play(client):
    response = client.get("/")
    assert b"<h1>PyQuest Game</h1>" in response.data

def test_post_play(client):
    post_data = {'form':{'username':'test@test.com'}}
    response = client.post("/", data=post_data)
    assert b"<h2>Character setup</h2>" in response.data

@pytest.fixture()
def runner(app):
    return app.test_cli_runner()
