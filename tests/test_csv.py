"""Tests 4 CSV processor."""

import pandas as pd
import pytest
from unittest.mock import Mock

from config import Config
from csv_processing import CSVProcessor
from models import Customer


class TestCSVProcessor:
    """Tests for CSVProcessor class."""

    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        config = Mock(spec=Config)
        config.MIN_AGE = 18
        config.MAX_AGE = 65
        return config

    @pytest.fixture
    def processor(self, config):
        """Create a CSVProcessor instance."""
        return CSVProcessor(config)

    def test_validate_customer_row_valid(self, processor):
        """Test validation of a valid customer row."""
        row = pd.Series({
            'Name': 'John Doe',
            'Age': 35,
            'Cookie': '26555324-53df-4eb1-8835-e6c0078bb2c0',
            'Banner_id': 42
        })

        customer, is_valid = processor.validate_customer_row(row)

        assert is_valid
        assert customer.Name == 'John Doe'
        assert customer.Age == 35
        assert customer.Cookie == '26555324-53df-4eb1-8835-e6c0078bb2c0'
        assert customer.Banner_id == 42

    def test_validate_customer_row_invalid_name(self, processor):
        """Test validation of invalid name."""
        row = pd.Series({
            'Name': 'John123',
            'Age': 35,
            'Cookie': '26555324-53df-4eb1-8835-e6c0078bb2c0',
            'Banner_id': 42
        })

        customer, is_valid = processor.validate_customer_row(row)

        assert not is_valid
        assert customer is None

    def test_validate_customer_row_invalid_age_below_minimum(self, processor):
        """Test validation of age below minimum."""
        row = pd.Series({
            'Name': 'John Doe',
            'Age': 16,
            'Cookie': '26555324-53df-4eb1-8835-e6c0078bb2c0',
            'Banner_id': 42
        })

        customer, is_valid = processor.validate_customer_row(row)

        assert not is_valid
        assert customer is None

    def test_validate_customer_row_invalid_age_above_maximum(self, processor):
        """Test validation of age above maximum."""
        row = pd.Series({
            'Name': 'John Doe',
            'Age': 70,
            'Cookie': '26555324-53df-4eb1-8835-e6c0078bb2c0',
            'Banner_id': 42
        })

        customer, is_valid = processor.validate_customer_row(row)

        assert not is_valid
        assert customer is None

    def test_validate_customer_row_invalid_cookie(self, processor):
        """Test validation of invalid cookie format."""
        row = pd.Series({
            'Name': 'John Doe',
            'Age': 35,
            'Cookie': 'invalid-uuid',
            'Banner_id': 42
        })

        customer, is_valid = processor.validate_customer_row(row)

        assert not is_valid
        assert customer is None

    def test_validate_customer_row_invalid_banner_id(self, processor):
        """Test validation of invalid banner ID."""
        row = pd.Series({
            'Name': 'John Doe',
            'Age': 35,
            'Cookie': '26555324-53df-4eb1-8835-e6c0078bb2c0',
            'Banner_id': 100
        })

        customer, is_valid = processor.validate_customer_row(row)

        assert not is_valid
        assert customer is None

    def test_process_csv_chunk(self, processor):
        """Test processing a CSV chunk."""
        # Create test data
        data = {
            'Name': ['John Doe', 'Jane Smith', 'Invalid123'],
            'Age': [35, 28, 25],
            'Cookie': [
                '26555324-53df-4eb1-8835-e6c0078bb2c0',
                '12345678-1234-5678-9abc-123456789012',
                '33333333-4444-5555-6666-777777777777'
            ],
            'Banner_id': [42, 25, 75]
        }
        chunk = pd.DataFrame(data)

        valid_customers = processor.process_csv_chunk(chunk)

        assert len(valid_customers) == 2
        assert processor.total_count == 3
        assert processor.invalid_count == 1

        # Check valid customers
        assert valid_customers[0].Name == 'John Doe'
        assert valid_customers[1].Name == 'Jane Smith'

    def test_customers_to_banner_requests(self, processor):
        """Test conversion of customers to banner requests."""
        customers = [
            Customer(
                Name='John Doe',
                Age=35,
                Cookie='26555324-53df-4eb1-8835-e6c0078bb2c0',
                Banner_id=42
            ),
            Customer(
                Name='Jane Smith',
                Age=28,
                Cookie='12345678-1234-5678-9abc-123456789012',
                Banner_id=25
            )
        ]

        banner_requests = processor.customers_to_banner_requests(customers)

        assert len(banner_requests) == 2
        assert banner_requests[0].VisitorCookie == '26555324-53df-4eb1-8835-e6c0078bb2c0'
        assert banner_requests[0].BannerId == 42
        assert banner_requests[1].VisitorCookie == '12345678-1234-5678-9abc-123456789012'
        assert banner_requests[1].BannerId == 25

    def test_get_statistics(self, processor):
        """Test getting processing statistics."""
        processor.total_count = 100
        processor.invalid_count = 10

        stats = processor.get_statistics()

        assert stats['total_records'] == 100
        assert stats['valid_records'] == 90
        assert stats['invalid_records'] == 10
        assert stats['validation_success_rate'] == 90.0

    def test_get_statistics_no_records(self, processor):
        """Test getting statistics when no records processed."""
        stats = processor.get_statistics()

        assert stats['total_records'] == 0
        assert stats['valid_records'] == 0
        assert stats['invalid_records'] == 0
        assert stats['validation_success_rate'] == 0
