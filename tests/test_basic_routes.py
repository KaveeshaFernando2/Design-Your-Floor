import pytest
from app import create_app, db

# -------------------------
# Flask App Fixture
# -------------------------
@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    with app.app_context():
        yield app


@pytest.fixture
def client(app):
    return app.test_client()


# -------------------------
# ROUND 1 – BASIC ROUTES
# -------------------------

def test_home_page(client):
    response = client.get('/')
    assert response.status_code == 200


def test_login_page(client):
    response = client.get('/login')
    assert response.status_code == 200


def test_register_page(client):
    response = client.get('/register')
    assert response.status_code == 200
