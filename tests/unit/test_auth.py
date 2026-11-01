"""
Unit tests for Authentication, Salted Password Hashing, and Role Verification.
"""

import pytest
from src.common.auth import hash_password, verify_password, authenticate_user
from src.common.config import config


def test_password_hashing_and_verification():
    pwd = "SecureIndustrialSecret123!"
    h1, s1 = hash_password(pwd)
    assert len(h1) == 64  # sha256 hex length
    assert len(s1) == 32  # 16 bytes hex

    # Positive verification
    assert verify_password(pwd, s1, h1) is True

    # Negative verification
    assert verify_password("WrongPassword!", s1, h1) is False


def test_default_user_authentication():
    # Admin
    admin_user = authenticate_user(config.ADMIN_USERNAME, config.ADMIN_INITIAL_PASSWORD)
    assert admin_user is not None
    assert admin_user["username"] == config.ADMIN_USERNAME
    assert admin_user["role"] == "admin"
    assert "password_hash" not in admin_user

    # Operator
    op_user = authenticate_user(config.OPERATOR_USERNAME, config.OPERATOR_INITIAL_PASSWORD)
    assert op_user is not None
    assert op_user["username"] == config.OPERATOR_USERNAME
    assert op_user["role"] == "operator"

    # Bad user
    bad_user = authenticate_user("nonexistent", "fakepwd")
    assert bad_user is None

