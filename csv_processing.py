"""CSV processor for customer data validation and processing."""

import logging
from typing import Generator, List, Tuple
import pandas as pd
from pydantic import ValidationError

from config import Config
from models import Customer, BannerRequest

logger = logging.getLogger(__name__)


class CSVProcessor:
    """Processes CSV files and validates customer data."""

    def __init__(self, config: Config):
        """Initialize the CSV processor."""
        self.config = config
        self.valid_customers: List[Customer] = []
        self.invalid_count = 0
        self.total_count = 0

    def read_csv_in_chunks(self, file_path: str, chunk_size: int = 10000) -> Generator[pd.DataFrame, None, None]:
        """Read CSV file in chunks to handle large files efficiently."""
        try:
            logger.info(f"Starting to read CSV file: {file_path}")

            # Read the CSV in chunks to handle large files
            chunk_reader = pd.read_csv(file_path, chunksize=chunk_size)

            for chunk_num, chunk in enumerate(chunk_reader):
                logger.debug(f"Processing chunk {chunk_num + 1} with {len(chunk)} rows")
                yield chunk

        except FileNotFoundError:
            logger.error(f"CSV file not found: {file_path}")
            raise
        except pd.errors.EmptyDataError:
            logger.error(f"CSV file is empty: {file_path}")
            raise
        except Exception as e:
            logger.error(f"Error reading CSV file {file_path}: {str(e)}")
            raise

    def validate_customer_row(self, row: pd.Series) -> Tuple[Customer, bool]:
        """Validate a single customer row and return the customer object and validity status."""
        try:
            # Convert row to dict and create Customer object
            customer_data = {
                'Name': str(row.get('Name', '')),
                'Age': int(row.get('Age', 0)),
                'Cookie': str(row.get('Cookie', '')),
                'Banner_id': int(row.get('Banner_id', -1))
            }

            # Create customer object (this validates Name, Cookie, and Banner_id)
            customer = Customer(**customer_data)

            # Validate age against configurable limits
            customer.validate_age(self.config.MIN_AGE, self.config.MAX_AGE)

            return customer, True

        except (ValidationError, ValueError, TypeError) as e:
            # Log the specific validation error with row data
            row_info = f"Name: {row.get('Name', 'N/A')}, Age: {row.get('Age', 'N/A')}, " \
                       f"Cookie: {row.get('Cookie', 'N/A')}, Banner_id: {row.get('Banner_id', 'N/A')}"
            logger.warning(f"Invalid customer data - {row_info} - Error: {str(e)}")
            return None, False

    def process_csv_chunk(self, chunk: pd.DataFrame) -> List[Customer]:
        """Process a chunk of CSV data and return valid customers."""
        valid_customers = []

        for index, row in chunk.iterrows():
            self.total_count += 1

            customer, is_valid = self.validate_customer_row(row)

            if is_valid and customer:
                valid_customers.append(customer)
            else:
                self.invalid_count += 1

        return valid_customers

    def process_csv_file(self, file_path: str) -> Generator[List[Customer], None, None]:
        """Process entire CSV file and yield batches of valid customers."""
        logger.info(f"Starting CSV processing for file: {file_path}")

        self.total_count = 0
        self.invalid_count = 0

        try:
            for chunk in self.read_csv_in_chunks(file_path):
                valid_customers = self.process_csv_chunk(chunk)

                if valid_customers:
                    logger.debug(f"Processed chunk: {len(valid_customers)} valid customers")
                    yield valid_customers

            # Log final statistics
            valid_count = self.total_count - self.invalid_count
            logger.info(f"CSV processing completed. Total: {self.total_count}, "
                        f"Valid: {valid_count}, Invalid: {self.invalid_count}")

            if self.invalid_count > 0:
                logger.warning(f"Skipped {self.invalid_count} invalid records. "
                               f"Check logs for validation errors.")

        except Exception as e:
            logger.error(f"Error processing CSV file: {str(e)}")
            raise

    def customers_to_banner_requests(self, customers: List[Customer]) -> List[BannerRequest]:
        """Convert list of customers to banner requests."""
        banner_requests = []

        for customer in customers:
            banner_request = BannerRequest(
                VisitorCookie=customer.Cookie,
                BannerId=customer.Banner_id
            )
            banner_requests.append(banner_request)

        return banner_requests

    def get_statistics(self) -> dict:
        """Get processing statistics."""
        return {
            'total_records': self.total_count,
            'valid_records': self.total_count - self.invalid_count,
            'invalid_records': self.invalid_count,
            'validation_success_rate': (
                                                   self.total_count - self.invalid_count) / self.total_count * 100 if self.total_count > 0 else 0
        }
