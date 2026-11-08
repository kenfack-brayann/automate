import pytest

from app import create_app


@pytest.fixture
def app():
    return create_app({"TESTING": True, "RATE_LIMIT_REQUESTS": 10_000})


@pytest.fixture
def client(app):
    return app.test_client()
