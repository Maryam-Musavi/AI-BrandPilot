def test_placeholder():
    """Placeholder test - should be replaced with actual tests."""
    assert True


def test_app_health(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_app_root(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "AI BrandPilot API"}


def test_chat_endpoint(client):
    """Test the chat endpoint."""
    payload = {"message": "Hello, how can you help me with my brand?"}
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert isinstance(data["response"], str)