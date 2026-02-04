"""
Unit tests for API client functionality.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import httpx


class TestAPIClient:
    """Test suite for API client."""
    
    @pytest.fixture
    def api_client(self, mock_api_key):
        """Create API client instance."""
        from src.api_client import APIClient
        return APIClient(api_key=mock_api_key, base_url="https://api.test.com")
    
    @pytest.mark.asyncio
    async def test_get_request_success(self, api_client, sample_api_response):
        """Test successful GET request."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = sample_api_response
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            result = await api_client.get("/items")
            
            assert result == sample_api_response
            mock_get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_post_request_with_data(self, api_client):
        """Test POST request with JSON data."""
        test_data = {"name": "New Item", "value": 500}
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {"id": 4, **test_data}
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response
            
            result = await api_client.post("/items", json=test_data)
            
            assert result["name"] == test_data["name"]
            assert "id" in result
            mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_request_with_retry_on_failure(self, api_client):
        """Test request retry mechanism on failure."""
        with patch('httpx.AsyncClient.get') as mock_get:
            # First call fails, second succeeds
            mock_get.side_effect = [
                httpx.HTTPError("Connection error"),
                Mock(status_code=200, json=Mock(return_value={"status": "ok"}))
            ]
            
            result = await api_client.get("/items", retry=True, max_retries=2)
            
            assert result["status"] == "ok"
            assert mock_get.call_count == 2
    
    @pytest.mark.asyncio
    async def test_request_timeout_handling(self, api_client):
        """Test timeout handling in requests."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = httpx.TimeoutException("Request timeout")
            
            with pytest.raises(httpx.TimeoutException):
                await api_client.get("/items", timeout=5.0)
    
    @pytest.mark.asyncio
    async def test_authentication_header_included(self, api_client, mock_api_key):
        """Test that authentication headers are included."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {}
            mock_get.return_value = mock_response
            
            await api_client.get("/items")
            
            call_kwargs = mock_get.call_args.kwargs
            assert "headers" in call_kwargs
            assert call_kwargs["headers"]["Authorization"] == f"Bearer {mock_api_key}"
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, api_client):
        """Test rate limiting functionality."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 429  # Too Many Requests
            mock_response.headers = {"Retry-After": "2"}
            mock_get.return_value = mock_response
            
            with pytest.raises(Exception) as exc_info:
                await api_client.get("/items")
            
            assert "rate limit" in str(exc_info.value).lower()
    
    def test_url_construction(self, api_client):
        """Test correct URL construction."""
        url = api_client._build_url("/items", {"page": 1, "limit": 10})
        
        assert "items" in url
        assert "page=1" in url
        assert "limit=10" in url
    
    @pytest.mark.asyncio
    async def test_error_response_handling(self, api_client):
        """Test handling of error responses."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.json.return_value = {"error": "Not found"}
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Not found", request=Mock(), response=mock_response
            )
            mock_get.return_value = mock_response
            
            with pytest.raises(httpx.HTTPStatusError):
                await api_client.get("/items/999")