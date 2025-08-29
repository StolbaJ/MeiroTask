"""ShowAds API client with authentication and error handling."""

import logging
from typing import List, Optional
from datetime import datetime, timedelta

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import Config
from models import AuthRequest, AuthResponse, BannerRequest, BulkBannerRequest

logger = logging.getLogger(__name__)


class ShowAdsClient:
    """Client for the ShowAds API with token management and retry logic."""

    def __init__(self, config: Config):
        """Initialize the ShowAds client."""
        self.config = config
        self.base_url = config.SHOWADS_API_URL
        self.project_key = config.PROJECT_KEY
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

        # Set up session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=config.MAX_RETRIES,
            backoff_factor=config.RETRY_DELAY,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _is_token_valid(self) -> bool:
        if not self.access_token or not self.token_expires_at:
            return False

        # Add 1 minute buffer before expiration
        return datetime.now() < (self.token_expires_at - timedelta(minutes=1))

    def _ensure_authenticated(self) -> bool:
        if self._is_token_valid():
            return True

        return self.authenticate()
    def authenticate(self) -> bool:
        """Authenticate with the ShowAds API and obtain access token."""
        try:
            auth_request = AuthRequest(ProjectKey=self.project_key)

            response = self.session.post(
                f"{self.base_url}/auth",
                json=auth_request.dict(),
                timeout=30
            )

            if response.status_code == 200:
                auth_response = AuthResponse(**response.json())
                self.access_token = auth_response.AccessToken
                # Token expires in 24 hours
                self.token_expires_at = datetime.now() + timedelta(hours=24)
                logger.info("Successfully authenticated with ShowAds API")
                return True
            else:
                logger.error(f"Authentication failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return False

    def send_banner_request(self, visitor_cookie: str, banner_id: int) -> bool:
        """Send a single banner request to the ShowAds API."""
        if not self._ensure_authenticated():
            return False

        try:
            banner_request = BannerRequest(
                VisitorCookie=visitor_cookie,
                BannerId=banner_id
            )
            headers = {"Authorization": f"Bearer {self.access_token}"}

            response = self.session.post(
                f"{self.base_url}/banners/show",
                json=banner_request.dict(),
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                logger.debug(f"Successfully sent banner request for cookie {visitor_cookie}")
                return True
            elif response.status_code == 401:
                logger.warning("Token expired, re-authenticating...")
                if self.authenticate():
                    return self.send_banner_request(visitor_cookie, banner_id)
                return False
            else:
                logger.error(f"Banner request failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error sending banner request: {str(e)}")
            return False

    def send_bulk_banner_requests(self, banner_requests: List[BannerRequest]) -> bool:
        """Send bulk banner requests to the ShowAds API."""
        if not banner_requests:
            return True

        if not self._ensure_authenticated():
            return False

        # Ensure we don't exceed the 1000 visitor limit
        if len(banner_requests) > 1000:
            logger.error(f"Too many requests in batch: {len(banner_requests)} (max 1000)")
            return False

        try:
            bulk_request = BulkBannerRequest(Data=banner_requests)
            headers = {"Authorization": f"Bearer {self.access_token}"}

            response = self.session.post(
                f"{self.base_url}/banners/show/bulk",
                json=bulk_request.dict(),
                headers=headers,
                timeout=60
            )

            if response.status_code == 200:
                logger.info(f"Successfully sent bulk banner request for {len(banner_requests)} customers")
                return True
            elif response.status_code == 401:
                logger.warning("Token expired, re-authenticating...")
                if self.authenticate():
                    return self.send_bulk_banner_requests(banner_requests)
                return False
            else:
                logger.error(f"Bulk banner request failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error sending bulk banner request: {str(e)}")
            return False

    def close(self):
        self.session.close()
