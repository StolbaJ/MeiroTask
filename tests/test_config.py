"""Tests for configuration module."""

import os
import pytest

from config import Config


class TestConfig:
    """Tests for Config class."""

    def test_default_values(self):
        """Test default configuration values."""
        # Clear environment variables for this test
        env_vars = ['SHOWADS_API_URL', 'PROJECT_KEY', 'MIN_AGE', 'MAX_AGE', 'BATCH_SIZE', 'MAX_RETRIES', 'RETRY_DELAY', 'LOG_LEVEL']
        original_values = {}

        for var in env_vars:
            original_values[var] = os.environ.get(var)
            if var in os.environ:
                del os.environ[var]

        try:
            config = Config()
            assert config.SHOWADS_API_URL == 'https://golang-assignment-968918017632.europe-west3.run.app'
            assert config.PROJECT_KEY == 'meiro-data-connector-project'
            assert config.MIN_AGE == 18
            assert config.MAX_AGE == 120
            assert config.BATCH_SIZE == 1000
            assert config.MAX_RETRIES == 3
            assert config.RETRY_DELAY == 1
            assert config.LOG_LEVEL == 'INFO'
        finally:
            # Restore original values
            for var, value in original_values.items():
                if value is not None:
                    os.environ[var] = value

    def test_environment_variable_override(self):
        """Test that environment variables override default values."""
        # Set environment variables
        os.environ['MIN_AGE'] = '21'
        os.environ['MAX_AGE'] = '65'
        os.environ['BATCH_SIZE'] = '500'
        os.environ['LOG_LEVEL'] = 'DEBUG'

        try:
            config = Config()
            assert config.MIN_AGE == 21
            assert config.MAX_AGE == 65
            assert config.BATCH_SIZE == 500
            assert config.LOG_LEVEL == 'DEBUG'
        finally:
            # Clean up
            del os.environ['MIN_AGE']
            del os.environ['MAX_AGE']
            del os.environ['BATCH_SIZE']
            del os.environ['LOG_LEVEL']

    def test_validate_success(self):
        """Test successful configuration validation."""
        # Set environment variables with valid values
        original_values = {}
        env_vars = ['MIN_AGE', 'MAX_AGE', 'BATCH_SIZE', 'SHOWADS_API_URL', 'PROJECT_KEY']

        for var in env_vars:
            original_values[var] = os.environ.get(var)

        os.environ['MIN_AGE'] = '18'
        os.environ['MAX_AGE'] = '65'
        os.environ['BATCH_SIZE'] = '500'
        os.environ['SHOWADS_API_URL'] = 'https://test.example.com'
        os.environ['PROJECT_KEY'] = 'test-key'

        try:
            config = Config()
            config.validate()  # Should not raise exception
        finally:
            # Restore original values
            for var, value in original_values.items():
                if value is not None:
                    os.environ[var] = value
                elif var in os.environ:
                    del os.environ[var]

    def test_validate_invalid_min_age(self):
        """Test validation with invalid MIN_AGE."""
        original_value = os.environ.get('MIN_AGE')
        os.environ['MIN_AGE'] = '-5'

        try:
            config = Config()
            with pytest.raises(ValueError, match="Invalid MIN_AGE"):
                config.validate()
        finally:
            if original_value is not None:
                os.environ['MIN_AGE'] = original_value
            elif 'MIN_AGE' in os.environ:
                del os.environ['MIN_AGE']

    def test_validate_invalid_max_age_too_high(self):
        """Test validation with MAX_AGE too high."""
        original_value = os.environ.get('MAX_AGE')
        os.environ['MAX_AGE'] = '200'

        try:
            config = Config()
            with pytest.raises(ValueError, match="Invalid MAX_AGE"):
                config.validate()
        finally:
            if original_value is not None:
                os.environ['MAX_AGE'] = original_value
            elif 'MAX_AGE' in os.environ:
                del os.environ['MAX_AGE']

    def test_validate_invalid_max_age_lower_than_min(self):
        """Test validation with MAX_AGE lower than MIN_AGE."""
        original_values = {'MIN_AGE': os.environ.get('MIN_AGE'), 'MAX_AGE': os.environ.get('MAX_AGE')}
        os.environ['MIN_AGE'] = '25'
        os.environ['MAX_AGE'] = '20'

        try:
            config = Config()
            with pytest.raises(ValueError, match="Invalid MAX_AGE"):
                config.validate()
        finally:
            for var, value in original_values.items():
                if value is not None:
                    os.environ[var] = value
                elif var in os.environ:
                    del os.environ[var]

    def test_validate_invalid_batch_size_zero(self):
        """Test validation with BATCH_SIZE of zero."""
        original_value = os.environ.get('BATCH_SIZE')
        os.environ['BATCH_SIZE'] = '0'

        try:
            config = Config()
            with pytest.raises(ValueError, match="Invalid BATCH_SIZE"):
                config.validate()
        finally:
            if original_value is not None:
                os.environ['BATCH_SIZE'] = original_value
            elif 'BATCH_SIZE' in os.environ:
                del os.environ['BATCH_SIZE']

    def test_validate_invalid_batch_size_too_high(self):
        """Test validation with BATCH_SIZE too high."""
        original_value = os.environ.get('BATCH_SIZE')
        os.environ['BATCH_SIZE'] = '1500'

        try:
            config = Config()
            with pytest.raises(ValueError, match="Invalid BATCH_SIZE"):
                config.validate()
        finally:
            if original_value is not None:
                os.environ['BATCH_SIZE'] = original_value
            elif 'BATCH_SIZE' in os.environ:
                del os.environ['BATCH_SIZE']

    def test_validate_empty_api_url(self):
        """Test validation with empty API URL."""
        original_value = os.environ.get('SHOWADS_API_URL')
        os.environ['SHOWADS_API_URL'] = ''

        try:
            config = Config()
            with pytest.raises(ValueError, match="SHOWADS_API_URL is required"):
                config.validate()
        finally:
            if original_value is not None:
                os.environ['SHOWADS_API_URL'] = original_value
            elif 'SHOWADS_API_URL' in os.environ:
                del os.environ['SHOWADS_API_URL']

    def test_validate_empty_project_key(self):
        """Test validation with empty project key."""
        original_value = os.environ.get('PROJECT_KEY')
        os.environ['PROJECT_KEY'] = ''

        try:
            config = Config()
            with pytest.raises(ValueError, match="PROJECT_KEY is required"):
                config.validate()
        finally:
            if original_value is not None:
                os.environ['PROJECT_KEY'] = original_value
            elif 'PROJECT_KEY' in os.environ:
                del os.environ['PROJECT_KEY']
