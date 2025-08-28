"""Tests for ShowAds API client."""

import pytest
from datetime import datetime, timedelta

from config import Config
from showads_cli import ShowAdsClient
from models import BannerRequest


class TestShowAdsClient:
    """Tests for ShowAdsClient class."""

    @pytest.fixture
    def config(self, mocker):
        """Create a test configuration."""
        config = mocker.Mock(spec=Config)
        config.SHOWADS_API_URL = 'https://test-api.example.com'
        config.PROJECT_KEY = 'test-project'
        config.MAX_RETRIES = 3
        config.RETRY_DELAY = 1
        return config

    @pytest.fixture
    def client(self, config):
        """Create a ShowAdsClient instance."""
        return ShowAdsClient(config)

    def test_init(self, client, config):
        """Test client initialization."""
        assert client.base_url == config.SHOWADS_API_URL
        assert client.project_key == config.PROJECT_KEY
        assert client.access_token is None
        assert client.token_expires_at is None

    def test_is_token_valid_no_token(self, client):
        """Test token validation when no token exists."""
        assert not client._is_token_valid()

    def test_is_token_valid_expired_token(self, client):
        """Test token validation when token is expired."""
        client.access_token = 'test-token'
        client.token_expires_at = datetime.now() - timedelta(hours=1)
        assert not client._is_token_valid()

    def test_is_token_valid_valid_token(self, client):
        """Test token validation when token is valid."""
        client.access_token = 'test-token'
        client.token_expires_at = datetime.now() + timedelta(hours=1)
        assert client._is_token_valid()

    def test_authenticate_success(self, mocker, client):
        """Test successful authentication."""
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'AccessToken': 'test-token'}
        mock_post = mocker.patch('requests.Session.post', return_value=mock_response)

        result = client.authenticate()

        assert result is True
        assert client.access_token == 'test-token'
        assert client.token_expires_at is not None
        mock_post.assert_called_once()

    def test_authenticate_failure(self, mocker, client):
        """Test failed authentication."""
        mock_response = mocker.Mock()
        mock_response.status_code = 400
        mock_response.text = 'Bad Request'
        mock_post = mocker.patch('requests.Session.post', return_value=mock_response)

        result = client.authenticate()

        assert result is False
        assert client.access_token is None
        assert client.token_expires_at is None

    def test_authenticate_exception(self, mocker, client):
        """Test authentication with exception."""
        mock_post = mocker.patch('requests.Session.post', side_effect=Exception('Network error'))

        result = client.authenticate()

        assert result is False
        assert client.access_token is None

    def test_send_banner_request_success(self, mocker, client):
        """Test successful banner request."""
        mock_auth = mocker.patch.object(client, '_ensure_authenticated', return_value=True)
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_post = mocker.patch('requests.Session.post', return_value=mock_response)
        client.access_token = 'test-token'

        result = client.send_banner_request('test-cookie', 42)

        assert result is True
        mock_post.assert_called_once()

    def test_send_banner_request_auth_failure(self, mocker, client):
        """Test banner request with authentication failure."""
        mock_auth = mocker.patch.object(client, '_ensure_authenticated', return_value=False)

        result = client.send_banner_request('test-cookie', 42)

        assert result is False

    def test_send_banner_request_api_error(self, mocker, client):
        """Test banner request with API error."""
        mock_auth = mocker.patch.object(client, '_ensure_authenticated', return_value=True)
        mock_response = mocker.Mock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_post = mocker.patch('requests.Session.post', return_value=mock_response)
        client.access_token = 'test-token'

        result = client.send_banner_request('test-cookie', 42)

        assert result is False

    def test_send_banner_request_token_expired(self, mocker, client):
        """Test banner request with token expiration and re-authentication."""
        mock_auth = mocker.patch.object(client, '_ensure_authenticated', return_value=True)
        mock_reauth = mocker.patch.object(client, 'authenticate', return_value=True)

        # First call returns 401 (token expired), second call succeeds
        mock_response_401 = mocker.Mock()
        mock_response_401.status_code = 401
        mock_response_200 = mocker.Mock()
        mock_response_200.status_code = 200
        mock_post = mocker.patch('requests.Session.post', side_effect=[mock_response_401, mock_response_200])

        client.access_token = 'test-token'

        result = client.send_banner_request('test-cookie', 42)

        assert result is True
        assert mock_post.call_count == 2
        mock_reauth.assert_called_once()

    def test_send_bulk_banner_requests_success(self, mocker, client):
        """Test successful bulk banner requests."""
        mock_auth = mocker.patch.object(client, '_ensure_authenticated', return_value=True)
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_post = mocker.patch('requests.Session.post', return_value=mock_response)
        client.access_token = 'test-token'

        banner_requests = [
            BannerRequest(VisitorCookie='cookie1', BannerId=1),
            BannerRequest(VisitorCookie='cookie2', BannerId=2)
        ]

        result = client.send_bulk_banner_requests(banner_requests)

        assert result is True
        mock_post.assert_called_once()

    def test_send_bulk_banner_requests_empty_list(self, mocker, client):
        """Test bulk banner requests with empty list."""
        mock_auth = mocker.patch.object(client, '_ensure_authenticated', return_value=True)

        result = client.send_bulk_banner_requests([])

        assert result is True

    def test_send_bulk_banner_requests_too_many(self, mocker, client):
        """Test bulk banner requests with too many requests."""
        mock_auth = mocker.patch.object(client, '_ensure_authenticated', return_value=True)

        # Create 1001 requests (exceeding limit of 1000)
        banner_requests = [
            BannerRequest(VisitorCookie=f'cookie{i}', BannerId=i % 100)
            for i in range(1001)
        ]

        result = client.send_bulk_banner_requests(banner_requests)

        assert result is False

    def test_send_bulk_banner_requests_auth_failure(self, mocker, client):
        """Test bulk banner requests with authentication failure."""
        mock_auth = mocker.patch.object(client, '_ensure_authenticated', return_value=False)

        banner_requests = [
            BannerRequest(VisitorCookie='cookie1', BannerId=1)
        ]

        result = client.send_bulk_banner_requests(banner_requests)

        assert result is False
