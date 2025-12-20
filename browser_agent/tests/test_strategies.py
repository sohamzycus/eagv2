"""
Tests for form filling strategies.
"""

import pytest
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.interfaces import FormField
from strategies.rule_strategy import RuleBasedStrategy


class TestRuleBasedStrategy:
    """Tests for the rule-based form filling strategy."""
    
    @pytest.fixture
    def strategy(self):
        """Create a rule-based strategy instance."""
        return RuleBasedStrategy(
            user_data={
                "name": "Test User",
                "email": "test@example.com",
                "github_url": "https://github.com/test",
                "youtube_url": "https://youtube.com/test",
                "default_text": "Test response"
            }
        )
    
    @pytest.mark.asyncio
    async def test_name_field(self, strategy):
        """Test that name fields are filled correctly."""
        field = FormField(
            field_type="text",
            label="Your Name",
            name="name",
            required=True
        )
        
        value = await strategy.determine_field_value(field, {})
        assert value == "Test User"
    
    @pytest.mark.asyncio
    async def test_email_field(self, strategy):
        """Test that email fields are filled correctly."""
        field = FormField(
            field_type="email",
            label="Email Address",
            name="email",
            required=True
        )
        
        value = await strategy.determine_field_value(field, {})
        assert value == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_github_field(self, strategy):
        """Test that GitHub URL fields are filled correctly."""
        field = FormField(
            field_type="url",
            label="GitHub Repository URL",
            name="github",
            required=True
        )
        
        value = await strategy.determine_field_value(field, {})
        assert value == "https://github.com/test"
    
    @pytest.mark.asyncio
    async def test_radio_field(self, strategy):
        """Test that radio fields return first option."""
        field = FormField(
            field_type="radio",
            label="Choose an option",
            name="option",
            required=True,
            options=["Option A", "Option B", "Option C"]
        )
        
        value = await strategy.determine_field_value(field, {})
        assert value == "Option A"
    
    @pytest.mark.asyncio
    async def test_validation_email(self, strategy):
        """Test email validation."""
        field = FormField(
            field_type="email",
            label="Email",
            name="email",
            required=True
        )
        
        assert await strategy.validate_response(field, "test@example.com")
        assert not await strategy.validate_response(field, "invalid-email")
    
    @pytest.mark.asyncio
    async def test_validation_url(self, strategy):
        """Test URL validation."""
        field = FormField(
            field_type="url",
            label="URL",
            name="url",
            required=True
        )
        
        assert await strategy.validate_response(field, "https://example.com")
        assert not await strategy.validate_response(field, "not-a-url")
    
    @pytest.mark.asyncio
    async def test_validation_required(self, strategy):
        """Test that required fields must have values."""
        field = FormField(
            field_type="text",
            label="Required Field",
            name="required",
            required=True
        )
        
        assert not await strategy.validate_response(field, "")
        assert await strategy.validate_response(field, "some value")


class TestFormField:
    """Tests for the FormField dataclass."""
    
    def test_form_field_creation(self):
        """Test creating a form field."""
        field = FormField(
            field_type="text",
            label="Test Label",
            name="test_field",
            required=True,
            options=["A", "B"],
            placeholder="Enter value"
        )
        
        assert field.field_type == "text"
        assert field.label == "Test Label"
        assert field.name == "test_field"
        assert field.required == True
        assert field.options == ["A", "B"]
        assert field.placeholder == "Enter value"
    
    def test_form_field_defaults(self):
        """Test default values for form field."""
        field = FormField(
            field_type="text",
            label="Test",
            name="test"
        )
        
        assert field.required == False
        assert field.options == []
        assert field.placeholder == ""
        assert field.current_value == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

