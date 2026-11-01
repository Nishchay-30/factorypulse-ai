"""
FactoryPulse AI - Security & Authentication Module
Implements secure salted password hashing (PBKDF2-HMAC-SHA256, 100k iterations),
session verification, and role-based access control (Admin / Operator).
"""

import os
import hmac
import hashlib
import secrets
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from src.common.config import config
from src.database.db import db

logger = logging.getLogger("FactoryPulse.Auth")


def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """
    Hash a password with PBKDF2-HMAC-SHA256 and a cryptographically secure salt.
    Returns (hex_hash, hex_salt).
    """
    if salt is None:
        salt = secrets.token_hex(16)
    salt_bytes = bytes.fromhex(salt)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_bytes, 100000)
    return key.hex(), salt


def verify_password(password: str, salt: str, stored_hash: str) -> bool:
    """Verify password against stored salt and hash using constant-time comparison."""
    try:
        calculated_hash, _ = hash_password(password, salt)
        return hmac.compare_digest(calculated_hash, stored_hash)
    except Exception as e:
        logger.error("Error during password verification: %s", e)
        return False


def seed_default_users():
    """Ensure baseline administrator and operator accounts exist in database."""
    conn = db.get_connection()
    cursor = conn.execute("SELECT COUNT(*) as count FROM users;")
    count = cursor.fetchone()["count"]

    if count == 0:
        logger.info("Seeding initial administrator and operator accounts...")
        # Create Admin
        admin_pwd = config.ADMIN_INITIAL_PASSWORD
        admin_hash, admin_salt = hash_password(admin_pwd)
        # Create Operator
        op_pwd = config.OPERATOR_INITIAL_PASSWORD
        op_hash, op_salt = hash_password(op_pwd)

        with db._write_lock:
            with conn:
                conn.execute(
                    """
                    INSERT INTO users (username, password_hash, salt, role, full_name, created_at)
                    VALUES (?, ?, ?, ?, ?, ?);
                    """,
                    (config.ADMIN_USERNAME, admin_hash, admin_salt, "admin", "System Administrator", datetime.now(timezone.utc).isoformat()),
                )
                conn.execute(
                    """
                    INSERT INTO users (username, password_hash, salt, role, full_name, created_at)
                    VALUES (?, ?, ?, ?, ?, ?);
                    """,
                    (config.OPERATOR_USERNAME, op_hash, op_salt, "operator", "Plant Floor Operator", datetime.now(timezone.utc).isoformat()),
                )
        logger.info("Default accounts created (Admin: '%s', Operator: '%s').", config.ADMIN_USERNAME, config.OPERATOR_USERNAME)


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate credentials and return user record if valid."""
    seed_default_users()
    conn = db.get_connection()
    cursor = conn.execute("SELECT * FROM users WHERE username = ?;", (username.strip(),))
    row = cursor.fetchone()

    if not row:
        return None

    user = dict(row)
    if verify_password(password, user["salt"], user["password_hash"]):
        # Update last_login
        now_iso = datetime.now(timezone.utc).isoformat()
        with db._write_lock:
            with conn:
                conn.execute("UPDATE users SET last_login = ? WHERE username = ?;", (now_iso, username))
        user["last_login"] = now_iso
        # Remove hash and salt before returning user context
        user.pop("password_hash", None)
        user.pop("salt", None)
        return user
    return None

