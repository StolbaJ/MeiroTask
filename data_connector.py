"""Main data connector module for processing customer data and sending to ShowAds API."""

import logging
import time
from typing import List

from config import Config
from csv_processing import CSVProcessor
from showads_cli import ShowAdsClient
from models import BannerRequest

logger = logging.getLogger(__name__)


class DataConnector:
    """Main data connector that orchestrates CSV processing and API communication."""

    def __init__(self, config: Config):
        """Initialize the data connector."""
        self.config = config
        self.csv_processor = CSVProcessor(config)
        self.showads_client = ShowAdsClient(config)

    def process_file(self, csv_file_path: str) -> bool:
        """Process a CSV file and send data to ShowAds API."""
        logger.info(f"Starting data connector process for file: {csv_file_path}")

        start_time = time.time()
        total_sent = 0
        total_failed = 0

        try:
            # Process CSV file in chunks
            for valid_customers in self.csv_processor.process_csv_file(csv_file_path):
                if not valid_customers:
                    continue

                # Convert customers to banner requests
                banner_requests = self.csv_processor.customers_to_banner_requests(valid_customers)

                # Send banner requests in batches
                success = self._send_banner_requests_in_batches(banner_requests)

                if success:
                    total_sent += len(banner_requests)
                    logger.info(f"Successfully sent {len(banner_requests)} banner requests")
                else:
                    total_failed += len(banner_requests)
                    logger.error(f"Failed to send {len(banner_requests)} banner requests")

            # Log final statistics
            processing_time = time.time() - start_time
            stats = self.csv_processor.get_statistics()

            logger.info(f"Data connector process completed in {processing_time:.2f} seconds")
            logger.info(f"Processing statistics: {stats}")
            logger.info(f"API submission: Sent: {total_sent}, Failed: {total_failed}")

            return total_failed == 0

        except Exception as e:
            logger.error(f"Error in data connector process: {str(e)}")
            return False

        finally:
            self.showads_client.close()

    def _send_banner_requests_in_batches(self, banner_requests: List[BannerRequest]) -> bool:
        """Send banner requests in batches, respecting API limits."""
        batch_size = min(self.config.BATCH_SIZE, 1000)  # API limit is 1000
        total_requests = len(banner_requests)

        logger.debug(f"Sending {total_requests} banner requests in batches of {batch_size}")

        for i in range(0, total_requests, batch_size):
            batch = banner_requests[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_requests + batch_size - 1) // batch_size

            logger.debug(f"Processing batch {batch_num}/{total_batches} with {len(batch)} requests")

            max_attempts = self.config.MAX_RETRIES + 1

            for attempt in range(max_attempts):
                success = self.showads_client.send_bulk_banner_requests(batch)

                if success:
                    break

                if attempt < max_attempts - 1:
                    wait_time = self.config.RETRY_DELAY * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Batch {batch_num} failed (attempt {attempt + 1}/{max_attempts}), "
                                   f"retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Batch {batch_num} failed after {max_attempts} attempts")
                    return False

        return True

    def validate_configuration(self) -> bool:
        """Validate the configuration before processing."""
        try:
            self.config.validate()
            logger.info("Configuration validation successful")
            return True
        except ValueError as e:
            logger.error(f"Configuration validation failed: {str(e)}")
            return False
