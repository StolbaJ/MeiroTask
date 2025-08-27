import os
from typing import Optional


class Config:
    """Configuration class for the ShowAds data connector."""

    # ShowAds API Configuration
    SHOWADS_API_URL: str = os.getenv('SHOWADS_API_URL', 'https://golang-assignment-968918017632.europe-west3.run.app')
    PROJECT_KEY: str = os.getenv('PROJECT_KEY', 'meiro-data-connector-project')

    # Age validation limits (configurable at runtime)
    MIN_AGE: int = int(os.getenv('MIN_AGE', '18'))
    MAX_AGE: int = int(os.getenv('MAX_AGE', '120'))

    BATCH_SIZE: int = int(os.getenv('BATCH_SIZE', '1000'))
    MAX_RETRIES: int = int(os.getenv('MAX_RETRIES', '3'))
    RETRY_DELAY: int = int(os.getenv('RETRY_DELAY', '1'))

    # Logging configuration
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')


    @classmethod
    def validate(cls) -> None:
        """Validate configuration values. So there is no non-sense values."""
        if cls.MIN_AGE < 0 or cls.MIN_AGE > 150:
            raise ValueError(f"Invalid MIN_AGE: {cls.MIN_AGE}")

        if cls.MAX_AGE < cls.MIN_AGE or cls.MAX_AGE > 150:
            raise ValueError(f"Invalid MAX_AGE: {cls.MAX_AGE}")

        if cls.BATCH_SIZE <= 0 or cls.BATCH_SIZE > 1000:
            raise ValueError(f"Invalid BATCH_SIZE: {cls.BATCH_SIZE}")

        if not cls.SHOWADS_API_URL:
            raise ValueError("SHOWADS_API_URL is required")

        if not cls.PROJECT_KEY:
            raise ValueError("PROJECT_KEY is required")
