"""Tests for data models."""

import pytest
from pydantic import ValidationError

from models import Customer, AuthRequest, AuthResponse, BannerRequest, BulkBannerRequest


class TestCustomer:
    """Tests for Customer model."""

    def test_valid_customer(self):
        """Test creating a valid customer."""
        customer = Customer(
            Name="John Doe",
            Age=35,
            Cookie="26555324-53df-4eb1-8835-e6c0078bb2c0",
            Banner_id=42
        )
        assert customer.Name == "John Doe"
        assert customer.Age == 35
        assert customer.Cookie == "26555324-53df-4eb1-8835-e6c0078bb2c0"
        assert customer.Banner_id == 42

    def test_invalid_name_with_numbers(self):
        """Test that names with numbers are invalid."""
        with pytest.raises(ValidationError):
            Customer(
                Name="John123",
                Age=35,
                Cookie="26555324-53df-4eb1-8835-e6c0078bb2c0",
                Banner_id=42
            )

    def test_invalid_name_with_special_chars(self):
        """Test that names with special characters are invalid."""
        with pytest.raises(ValidationError):
            Customer(
                Name="John@Doe",
                Age=35,
                Cookie="26555324-53df-4eb1-8835-e6c0078bb2c0",
                Banner_id=42
            )

    def test_valid_name_with_spaces(self):
        """Test that names with spaces are valid."""
        customer = Customer(
            Name="John Doe Smith",
            Age=35,
            Cookie="26555324-53df-4eb1-8835-e6c0078bb2c0",
            Banner_id=42
        )
        assert customer.Name == "John Doe Smith"

    def test_invalid_cookie_format(self):
        """Test that invalid UUID format is rejected."""
        with pytest.raises(ValidationError):
            Customer(
                Name="John Doe",
                Age=35,
                Cookie="invalid-uuid",
                Banner_id=42
            )

    def test_banner_id_below_range(self):
        """Test that Banner_id below 0 is invalid."""
        with pytest.raises(ValidationError):
            Customer(
                Name="John Doe",
                Age=35,
                Cookie="26555324-53df-4eb1-8835-e6c0078bb2c0",
                Banner_id=-1
            )

    def test_banner_id_above_range(self):
        """Test that Banner_id above 99 is invalid."""
        with pytest.raises(ValidationError):
            Customer(
                Name="John Doe",
                Age=35,
                Cookie="26555324-53df-4eb1-8835-e6c0078bb2c0",
                Banner_id=100
            )

    def test_banner_id_boundary_values(self):
        """Test Banner_id boundary values (0 and 99)."""
        customer_0 = Customer(
            Name="John Doe",
            Age=35,
            Cookie="26555324-53df-4eb1-8835-e6c0078bb2c0",
            Banner_id=0
        )
        assert customer_0.Banner_id == 0

        customer_99 = Customer(
            Name="Jane Doe",
            Age=35,
            Cookie="26555324-53df-4eb1-8835-e6c0078bb2c0",
            Banner_id=99
        )
        assert customer_99.Banner_id == 99

    def test_validate_age_within_range(self):
        """Test age validation within valid range."""
        customer = Customer(
            Name="John Doe",
            Age=25,
            Cookie="26555324-53df-4eb1-8835-e6c0078bb2c0",
            Banner_id=42
        )
        # Should not raise exception
        customer.validate_age(18, 65)

    def test_validate_age_below_minimum(self):
        """Test age validation below minimum."""
        customer = Customer(
            Name="John Doe",
            Age=16,
            Cookie="26555324-53df-4eb1-8835-e6c0078bb2c0",
            Banner_id=42
        )
        with pytest.raises(ValueError, match="Age must be between 18 and 65"):
            customer.validate_age(18, 65)

    def test_validate_age_above_maximum(self):
        """Test age validation above maximum."""
        customer = Customer(
            Name="John Doe",
            Age=70,
            Cookie="26555324-53df-4eb1-8835-e6c0078bb2c0",
            Banner_id=42
        )
        with pytest.raises(ValueError, match="Age must be between 18 and 65"):
            customer.validate_age(18, 65)


class TestAPIModels:
    """Tests for API request/response models."""

    def test_auth_request(self):
        """Test AuthRequest model."""
        auth_req = AuthRequest(ProjectKey="test-project")
        assert auth_req.ProjectKey == "test-project"

    def test_auth_response(self):
        """Test AuthResponse model."""
        auth_resp = AuthResponse(AccessToken="test-token")
        assert auth_resp.AccessToken == "test-token"

    def test_banner_request(self):
        """Test BannerRequest model."""
        banner_req = BannerRequest(
            VisitorCookie="26555324-53df-4eb1-8835-e6c0078bb2c0",
            BannerId=42
        )
        assert banner_req.VisitorCookie == "26555324-53df-4eb1-8835-e6c0078bb2c0"
        assert banner_req.BannerId == 42

    def test_bulk_banner_request(self):
        """Test BulkBannerRequest model."""
        banner_requests = [
            BannerRequest(
                VisitorCookie="26555324-53df-4eb1-8835-e6c0078bb2c0",
                BannerId=42
            ),
            BannerRequest(
                VisitorCookie="12345678-1234-5678-9abc-123456789012",
                BannerId=25
            )
        ]
        bulk_req = BulkBannerRequest(Data=banner_requests)
        assert len(bulk_req.Data) == 2
        assert bulk_req.Data[0].BannerId == 42
        assert bulk_req.Data[1].BannerId == 25
