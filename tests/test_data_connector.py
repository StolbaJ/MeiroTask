"""Tests for DataConnector."""

import pytest
import time

from config import Config
from data_connector import DataConnector
from models import Customer, BannerRequest


class TestDataConnector:
    """Tests for DataConnector class."""

    @pytest.fixture
    def config(self):
        """Create a test configuration."""

        class MockConfig:
            BATCH_SIZE = 100
            MAX_RETRIES = 2
            RETRY_DELAY = 1

            def validate(self):
                pass

        return MockConfig()

    @pytest.fixture
    def mock_csv_processor(self):
        """Create mock CSV processor."""

        class MockCSVProcessor:
            def __init__(self, config):
                pass

            def process_csv_file(self, file_path):
                return []

            def customers_to_banner_requests(self, customers):
                return []

            def get_statistics(self):
                return {'total_records': 0, 'valid_records': 0}

        return MockCSVProcessor

    @pytest.fixture
    def mock_showads_client(self):
        """Create mock ShowAds client."""

        class MockShowAdsClient:
            def __init__(self, config):
                pass

            def send_bulk_banner_requests(self, requests):
                return True

            def close(self):
                pass

        return MockShowAdsClient

    @pytest.fixture
    def connector(self, config, mock_csv_processor, mock_showads_client, monkeypatch):
        """Create a DataConnector instance with mocked dependencies."""
        monkeypatch.setattr('data_connector.CSVProcessor', mock_csv_processor)
        monkeypatch.setattr('data_connector.ShowAdsClient', mock_showads_client)

        return DataConnector(config)

    def test_init(self, config, mock_csv_processor, mock_showads_client, monkeypatch):
        """Test DataConnector initialization."""
        monkeypatch.setattr('data_connector.CSVProcessor', mock_csv_processor)
        monkeypatch.setattr('data_connector.ShowAdsClient', mock_showads_client)

        connector = DataConnector(config)

        assert connector.config == config
        assert isinstance(connector.csv_processor, mock_csv_processor)
        assert isinstance(connector.showads_client, mock_showads_client)

    def test_validate_configuration_success(self, connector):
        """Test successful configuration validation."""
        # config.validate() doesn't raise exception (defined in fixture)
        result = connector.validate_configuration()
        assert result is True

    def test_validate_configuration_failure(self, connector, monkeypatch):
        """Test failed configuration validation."""

        def failing_validate():
            raise ValueError("Invalid config")

        monkeypatch.setattr(connector.config, 'validate', failing_validate)

        result = connector.validate_configuration()
        assert result is False

    def test_process_file_success(self, connector, monkeypatch):
        """Test successful file processing."""
        test_customers = [
            Customer(Name="John Doe", Age=35, Cookie="12345678-1234-5678-9abc-123456789012", Banner_id=42)
        ]
        banner_requests = [
            BannerRequest(VisitorCookie="12345678-1234-5678-9abc-123456789012", BannerId=42)
        ]

        # Track calls
        calls = {'process_csv_file': [], 'customers_to_banner_requests': [], 'batch_send': [], 'close': []}

        def mock_process_csv_file(file_path):
            calls['process_csv_file'].append(file_path)
            return [test_customers]

        def mock_customers_to_banner_requests(customers):
            calls['customers_to_banner_requests'].append(customers)
            return banner_requests

        def mock_batch_send(requests):
            calls['batch_send'].append(requests)
            return True

        def mock_close():
            calls['close'].append(True)

        monkeypatch.setattr(connector.csv_processor, 'process_csv_file', mock_process_csv_file)
        monkeypatch.setattr(connector.csv_processor, 'customers_to_banner_requests', mock_customers_to_banner_requests)
        monkeypatch.setattr(connector.csv_processor, 'get_statistics', lambda: {'total_records': 1, 'valid_records': 1})
        monkeypatch.setattr(connector, '_send_banner_requests_in_batches', mock_batch_send)
        monkeypatch.setattr(connector.showads_client, 'close', mock_close)

        result = connector.process_file('test.csv')

        assert result is True
        assert calls['process_csv_file'] == ['test.csv']
        assert calls['customers_to_banner_requests'] == [test_customers]
        assert calls['batch_send'] == [banner_requests]
        assert calls['close'] == [True]

    def test_process_file_batch_failure(self, connector, monkeypatch):
        """Test file processing with batch failure."""
        test_customers = [
            Customer(Name="John Doe", Age=35, Cookie="12345678-1234-5678-9abc-123456789012", Banner_id=42)
        ]
        banner_requests = [
            BannerRequest(VisitorCookie="12345678-1234-5678-9abc-123456789012", BannerId=42)
        ]

        close_called = []

        monkeypatch.setattr(connector.csv_processor, 'process_csv_file', lambda x: [test_customers])
        monkeypatch.setattr(connector.csv_processor, 'customers_to_banner_requests', lambda x: banner_requests)
        monkeypatch.setattr(connector.csv_processor, 'get_statistics', lambda: {'total_records': 1, 'valid_records': 1})
        monkeypatch.setattr(connector, '_send_banner_requests_in_batches', lambda x: False)
        monkeypatch.setattr(connector.showads_client, 'close', lambda: close_called.append(True))

        result = connector.process_file('test.csv')

        assert result is False
        assert len(close_called) == 1

    def test_process_file_exception(self, connector, monkeypatch):
        """Test file processing with exception."""
        close_called = []

        def failing_process(file_path):
            raise Exception("Test error")

        monkeypatch.setattr(connector.csv_processor, 'process_csv_file', failing_process)
        monkeypatch.setattr(connector.showads_client, 'close', lambda: close_called.append(True))

        result = connector.process_file('test.csv')

        assert result is False
        assert len(close_called) == 1

    def test_process_file_empty_customers(self, connector, monkeypatch):
        """Test file processing with empty customer chunks."""
        banner_requests_called = []
        close_called = []

        def track_banner_requests(customers):
            banner_requests_called.append(customers)
            return []

        monkeypatch.setattr(connector.csv_processor, 'process_csv_file', lambda x: [[], []])
        monkeypatch.setattr(connector.csv_processor, 'get_statistics', lambda: {'total_records': 0, 'valid_records': 0})
        monkeypatch.setattr(connector.csv_processor, 'customers_to_banner_requests', track_banner_requests)
        monkeypatch.setattr(connector.showads_client, 'close', lambda: close_called.append(True))

        result = connector.process_file('test.csv')

        assert result is True
        # Should not call banner request methods for empty chunks
        assert len(banner_requests_called) == 0
        assert len(close_called) == 1

    def test_send_banner_requests_in_batches_success(self, connector, monkeypatch):
        """Test successful batch sending."""
        banner_requests = [
            BannerRequest(VisitorCookie=f"cookie{i}", BannerId=i % 100)
            for i in range(250)  # Create 250 requests (will be split into 3 batches of 100, 100, 50)
        ]

        call_count = []

        def mock_send_bulk(requests):
            call_count.append(len(requests))
            return True

        monkeypatch.setattr(connector.showads_client, 'send_bulk_banner_requests', mock_send_bulk)

        result = connector._send_banner_requests_in_batches(banner_requests)

        assert result is True
        assert len(call_count) == 3
        assert call_count == [100, 100, 50]

    def test_send_banner_requests_in_batches_retry_success(self, connector, monkeypatch):
        """Test batch sending with retry that eventually succeeds."""
        banner_requests = [
            BannerRequest(VisitorCookie="cookie1", BannerId=1)
        ]

        call_count = []
        sleep_calls = []

        def mock_send_bulk(requests):
            call_count.append(True)
            # First call fails, second succeeds
            return len(call_count) > 1

        def mock_sleep(seconds):
            sleep_calls.append(seconds)

        monkeypatch.setattr(connector.showads_client, 'send_bulk_banner_requests', mock_send_bulk)
        monkeypatch.setattr('time.sleep', mock_sleep)

        result = connector._send_banner_requests_in_batches(banner_requests)

        assert result is True
        assert len(call_count) == 2
        assert sleep_calls == [1]  # RETRY_DELAY * (2^0)

    def test_send_banner_requests_in_batches_retry_failure(self, connector, monkeypatch):
        """Test batch sending with retry that ultimately fails."""
        banner_requests = [
            BannerRequest(VisitorCookie="cookie1", BannerId=1)
        ]

        call_count = []
        sleep_calls = []

        def mock_send_bulk(requests):
            call_count.append(True)
            return False  # All attempts fail

        def mock_sleep(seconds):
            sleep_calls.append(seconds)

        monkeypatch.setattr(connector.showads_client, 'send_bulk_banner_requests', mock_send_bulk)
        monkeypatch.setattr('time.sleep', mock_sleep)

        result = connector._send_banner_requests_in_batches(banner_requests)

        assert result is False
        # MAX_RETRIES = 2, so total attempts = 3
        assert len(call_count) == 3
        # Should sleep twice (after attempt 1 and 2)
        assert len(sleep_calls) == 2
        # Exponential backoff: 1 * (2^0) = 1, then 1 * (2^1) = 2
        assert sleep_calls == [1, 2]

    def test_send_banner_requests_in_batches_empty_list(self, connector, monkeypatch):
        """Test batch sending with empty list."""
        call_count = []

        def mock_send_bulk(requests):
            call_count.append(True)
            return True

        monkeypatch.setattr(connector.showads_client, 'send_bulk_banner_requests', mock_send_bulk)

        result = connector._send_banner_requests_in_batches([])

        assert result is True
        assert len(call_count) == 0  # Should not be called

    def test_send_banner_requests_batch_size_limit(self, connector, monkeypatch):
        """Test that batch size respects API limit of 1000."""
        # Set config batch size higher than API limit
        connector.config.BATCH_SIZE = 1500

        banner_requests = [
            BannerRequest(VisitorCookie=f"cookie{i}", BannerId=i % 100)
            for i in range(2000)  # 2000 requests
        ]

        batch_sizes = []

        def mock_send_bulk(requests):
            batch_sizes.append(len(requests))
            return True

        monkeypatch.setattr(connector.showads_client, 'send_bulk_banner_requests', mock_send_bulk)

        result = connector._send_banner_requests_in_batches(banner_requests)

        assert result is True
        # Should be split into batches of 1000 (API limit), not 1500 (config)
        assert len(batch_sizes) == 2
        assert batch_sizes == [1000, 1000]  # Both batches should be 1000

    def test_process_file_multiple_chunks(self, connector, monkeypatch):
        """Test processing file with multiple customer chunks."""
        chunk1 = [Customer(Name="John Doe", Age=35, Cookie="12345678-1234-5678-9abc-123456789012", Banner_id=42)]
        chunk2 = [Customer(Name="Jane Smith", Age=28, Cookie="87654321-4321-8765-dcba-987654321098", Banner_id=25)]

        banner_requests1 = [BannerRequest(VisitorCookie="12345678-1234-5678-9abc-123456789012", BannerId=42)]
        banner_requests2 = [BannerRequest(VisitorCookie="87654321-4321-8765-dcba-987654321098", BannerId=25)]

        customers_to_banner_calls = []
        batch_send_calls = []
        close_called = []

        def mock_customers_to_banner_requests(customers):
            customers_to_banner_calls.append(customers)
            if len(customers_to_banner_calls) == 1:
                return banner_requests1
            else:
                return banner_requests2

        def mock_batch_send(requests):
            batch_send_calls.append(requests)
            return True

        monkeypatch.setattr(connector.csv_processor, 'process_csv_file', lambda x: [chunk1, chunk2])
        monkeypatch.setattr(connector.csv_processor, 'customers_to_banner_requests', mock_customers_to_banner_requests)
        monkeypatch.setattr(connector.csv_processor, 'get_statistics', lambda: {'total_records': 2, 'valid_records': 2})
        monkeypatch.setattr(connector, '_send_banner_requests_in_batches', mock_batch_send)
        monkeypatch.setattr(connector.showads_client, 'close', lambda: close_called.append(True))

        result = connector.process_file('test.csv')

        assert result is True
        # Should be called twice for two chunks
        assert len(customers_to_banner_calls) == 2
        assert len(batch_send_calls) == 2
        assert customers_to_banner_calls == [chunk1, chunk2]
        assert batch_send_calls == [banner_requests1, banner_requests2]
