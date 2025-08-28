"main function file"

import logging
import sys
import os
import argparse
from dotenv import load_dotenv

from config import Config
from data_connector import DataConnector


def setup_logging(log_level: str = 'INFO') -> None:
    """Set up logging configuration."""
    level = getattr(logging, log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Reduce noise from requests library
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)


def main():
    """Main function to run the data connector."""
    # Load environment variables from .env file if it exists
    load_dotenv()

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='ShowAds Data Connector')
    parser.add_argument('csv_file', help='Path to the CSV file containing customer data')
    parser.add_argument('--log-level', default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='Set the logging level (default: INFO)')
    parser.add_argument('--min-age', type=int,
                        help='Minimum age for customer validation (overrides config)')
    parser.add_argument('--max-age', type=int,
                        help='Maximum age for customer validation (overrides config)')
    parser.add_argument('--batch-size', type=int,
                        help='Batch size for API requests (max 1000)')

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    # Check if CSV file exists
    if not os.path.exists(args.csv_file):
        logger.error(f"CSV file not found: {args.csv_file}")
        sys.exit(1)

    # Override configuration with command line arguments if provided
    if args.min_age is not None:
        os.environ['MIN_AGE'] = str(args.min_age)
    if args.max_age is not None:
        os.environ['MAX_AGE'] = str(args.max_age)
    if args.batch_size is not None:
        os.environ['BATCH_SIZE'] = str(args.batch_size)

    # Initialize configuration
    config = Config()

    logger.info("ShowAds Data Connector Starting")
    logger.info(f"CSV file: {args.csv_file}")
    logger.info(f"API URL: {config.SHOWADS_API_URL}")
    logger.info(f"Age range: {config.MIN_AGE}-{config.MAX_AGE}")
    logger.info(f"Batch size: {config.BATCH_SIZE}")

    # Initialize and run data connector
    data_connector = DataConnector(config)

    # Validate configuration
    if not data_connector.validate_configuration():
        logger.error("Configuration validation failed")
        sys.exit(1)

    # Process the CSV file
    success = data_connector.process_file(args.csv_file)

    if success:
        logger.info("Data connector completed successfully")
        sys.exit(0)
    else:
        logger.error("Data connector completed with errors")
        sys.exit(1)


if __name__ == "__main__":
    main()