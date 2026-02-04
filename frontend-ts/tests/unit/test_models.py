"""
Unit tests for data models and validation.
"""
import pytest
from datetime import datetime
from pydantic import ValidationError


class TestUserModel:
    """Test suite for User model."""
    
    def test_user_creation_valid(self, sample_user_data):
        """Test creating user with valid data."""
        from src.models import User
        
        user = User(**sample_user_data)
        
        assert user.id == sample_user_data["id"]
        assert user.email == sample_user_data["email"]
        assert user.name == sample_user_data["name"]
    
    def test_user_email_validation(self):
        """Test email validation."""
        from src.models import User
        
        with pytest.raises(ValidationError) as exc_info:
            User(
                id="123",
                email="invalid-email",
                name="Test User"
            )
        
        assert "email" in str(exc_info.value).lower()
    
    def test_user_required_fields(self):
        """Test that required fields are enforced."""
        from src.models import User
        
        with pytest.raises(ValidationError) as exc_info:
            User(id="123")
        
        errors = exc_info.value.errors()
        error_fields = [e["loc"][0] for e in errors]
        assert "email" in error_fields
    
    def test_user_serialization(self, sample_user_data):
        """Test user model serialization."""
        from src.models import User
        
        user = User(**sample_user_data)
        serialized = user.model_dump()
        
        assert serialized["id"] == sample_user_data["id"]
        assert serialized["email"] == sample_user_data["email"]


class TestItemModel:
    """Test suite for Item model."""
    
    def test_item_creation(self):
        """Test creating item with valid data."""
        from src.models import Item
        
        item = Item(id=1, name="Test Item", value=100)
        
        assert item.id == 1
        assert item.name == "Test Item"
        assert item.value == 100
    
    def test_item_value_validation(self):
        """Test value validation (must be positive)."""
        from src.models import Item
        
        with pytest.raises(ValidationError):
            Item(id=1, name="Test", value=-10)
    
    def test_item_default_values(self):
        """Test default values are set correctly."""
        from src.models import Item
        
        item = Item(id=1, name="Test Item", value=100)
        
        assert item.created_at is not None
        assert isinstance(item.created_at, datetime)
    
    def test_item_update(self):
        """Test updating item fields."""
        from src.models import Item
        
        item = Item(id=1, name="Original", value=100)
        updated_data = {"name": "Updated", "value": 200}
        
        updated_item = item.model_copy(update=updated_data)
        
        assert updated_item.name == "Updated"
        assert updated_item.value == 200
        assert updated_item.id == item.id  # ID should not change


class TestRequestValidation:
    """Test suite for request validation models."""
    
    def test_pagination_params(self):
        """Test pagination parameter validation."""
        from src.models import PaginationParams
        
        params = PaginationParams(page=1, per_page=10)
        
        assert params.page == 1
        assert params.per_page == 10
    
    def test_pagination_limits(self):
        """Test pagination limits are enforced."""
        from src.models import PaginationParams
        
        with pytest.raises(ValidationError):
            PaginationParams(page=0, per_page=10)  # Page must be >= 1
        
        with pytest.raises(ValidationError):
            PaginationParams(page=1, per_page=1000)  # Per page max 100
    
    def test_filter_params(self):
        """Test filter parameter validation."""
        from src.models import FilterParams
        
        filters = FilterParams(
            search="test",
            category="electronics",
            min_price=10.0,
            max_price=100.0
        )
        
        assert filters.search == "test"
        assert filters.category == "electronics"
        assert filters.min_price < filters.max_price