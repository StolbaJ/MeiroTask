"""Configuration module for the ShowAds data connector."""

import os
from typing import Optional


class Config:
    """Configuration class for the ShowAds data connector."""

    @staticmethod
    def get_showads_api_url() -> str:
        return os.getenv('SHOWADS_API_URL', 'https://golang-assignment-968918017632.europe-west3.run.app')

    @staticmethod
    def get_project_key() -> str:
        return os.getenv('PROJECT_KEY', 'meiro-data-connector-project')

    @staticmethod
    def get_min_age() -> int:
        return int(os.getenv('MIN_AGE', '18'))

    @staticmethod
    def get_max_age() -> int:
        return int(os.getenv('MAX_AGE', '120'))

    @staticmethod
    def get_batch_size() -> int:
        return int(os.getenv('BATCH_SIZE', '1000'))

    @staticmethod
    def get_max_retries() -> int:
        return int(os.getenv('MAX_RETRIES', '3'))

    @staticmethod
    def get_retry_delay() -> int:
        return int(os.getenv('RETRY_DELAY', '1'))

    @staticmethod
    def get_log_level() -> str:
        return os.getenv('LOG_LEVEL', 'INFO')

    # Properties for backward compatibility
    @property
    def SHOWADS_API_URL(self) -> str:
        return self.get_showads_api_url()

    @property
    def PROJECT_KEY(self) -> str:
        return self.get_project_key()

    @property
    def MIN_AGE(self) -> int:
        return self.get_min_age()

    @property
    def MAX_AGE(self) -> int:
        return self.get_max_age()

    @property
    def BATCH_SIZE(self) -> int:
        return self.get_batch_size()

    @property
    def MAX_RETRIES(self) -> int:
        return self.get_max_retries()

    @property
    def RETRY_DELAY(self) -> int:
        return self.get_retry_delay()

    @property
    def LOG_LEVEL(self) -> str:
        return self.get_log_level()

    def validate(self) -> None:
        """Validate configuration values. So there is no non-sense values."""
        if self.MIN_AGE < 0 or self.MIN_AGE > 150:
            raise ValueError(f"Invalid MIN_AGE: {self.MIN_AGE}")

        if self.MAX_AGE < self.MIN_AGE or self.MAX_AGE > 150:
            raise ValueError(f"Invalid MAX_AGE: {self.MAX_AGE}")

        if self.BATCH_SIZE <= 0 or self.BATCH_SIZE > 1000:
            raise ValueError(f"Invalid BATCH_SIZE: {self.BATCH_SIZE}")

        if not self.SHOWADS_API_URL:
            raise ValueError("SHOWADS_API_URL is required")

        if not self.PROJECT_KEY:
            raise ValueError("PROJECT_KEY is required")
