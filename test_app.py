import pytest
from app import app

@pytest.fixture
def client():
    app.testing = True
    return app.test_client()

def test_home_status_code(client):
    """Test if the home route returns HTTP 200."""
    response = client.get("/")
    assert response.status_code == 200

def test_home_content(client):
    """Test if the home route returns the correct message."""
    response = client.get("/")
    assert response.data.decode("utf-8") == "****************Hello from Flask CI/CD Pipeline****************"
