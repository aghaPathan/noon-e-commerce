"""
Pytest configuration and shared fixtures for all tests.
"""
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
import json
import os

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "test_data"
TEST_DATA_DIR.mkdir(exist_ok=True)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_api_key():
    """Provide mock API key for testing."""
    return "test-api-key-12345"


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "id": "user123",
        "email": "test@example.com",
        "name": "Test User",
        "role": "user",
        "created_at": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_api_response():
    """Sample API response data."""
    return {
        "status": "success",
        "data": {
            "items": [
                {"id": 1, "name": "Item 1", "value": 100},
                {"id": 2, "name": "Item 2", "value": 200},
                {"id": 3, "name": "Item 3", "value": 300}
            ],
            "total": 3,
            "page": 1,
            "per_page": 10
        },
        "timestamp": "2024-01-01T12:00:00Z"
    }


@pytest.fixture
def mock_http_client():
    """Mock HTTP client for API calls."""
    mock = AsyncMock()
    mock.get.return_value = Mock(
        status_code=200,
        json=Mock(return_value={"status": "success"})
    )
    mock.post.return_value = Mock(
        status_code=201,
        json=Mock(return_value={"status": "created"})
    )
    return mock


@pytest.fixture
def mock_database():
    """Mock database connection."""
    db = Mock()
    db.execute = AsyncMock(return_value=[])
    db.fetch_one = AsyncMock(return_value=None)
    db.fetch_all = AsyncMock(return_value=[])
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture
def temp_upload_file(tmp_path):
    """Create temporary upload file for testing."""
    file_path = tmp_path / "test_upload.txt"
    file_path.write_text("Test file content")
    return file_path


@pytest.fixture
def mock_env_vars():
    """Mock environment variables."""
    env_vars = {
        "API_KEY": "test-key",
        "API_URL": "https://api.test.com",
        "DATABASE_URL": "postgresql://test:test@localhost/testdb",
        "REDIS_URL": "redis://localhost:6379",
        "ENV": "test",
        "DEBUG": "true"
    }
    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture
def mock_cache():
    """Mock cache implementation."""
    cache = {}
    
    class MockCache:
        async def get(self, key: str):
            return cache.get(key)
        
        async def set(self, key: str, value, ttl: int = 300):
            cache[key] = value
        
        async def delete(self, key: str):
            cache.pop(key, None)
        
        async def clear(self):
            cache.clear()
    
    return MockCache()


@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset all mocks after each test."""
    yield
    # Cleanup happens here


@pytest.fixture
def sample_security_report():
    """Sample security report data."""
    return {
        "vulnerabilities": [],
        "security_headers": {
            "Content-Security-Policy": "present",
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff"
        },
        "authentication": {
            "method": "JWT",
            "secure": True
        },
        "encryption": {
            "in_transit": True,
            "at_rest": True
        }
    }


@pytest.fixture
def sample_coverage_report():
    """Sample test coverage report."""
    return {
        "total_coverage": 85.5,
        "files": {
            "src/api.py": 92.0,
            "src/models.py": 88.0,
            "src/utils.py": 78.0
        },
        "uncovered_lines": [
            {"file": "src/utils.py", "lines": [45, 46, 78]}
        ]
    }