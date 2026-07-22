import pytest
from app.domain.entities.user import UserRole


def test_user_role_values():
    """Test that UserRole enum has the expected values."""
    assert UserRole.USER.value == "user"
    assert UserRole.ADMIN.value == "admin"
    assert UserRole.RESEARCHER.value == "researcher"

def test_user_role_members():
    """Test that all expected roles exist in the enum."""
    expected_roles = {"USER", "ADMIN", "RESEARCHER"}
    actual_roles = set(UserRole.__members__.keys())
    assert expected_roles == actual_roles
