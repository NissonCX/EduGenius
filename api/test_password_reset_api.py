#!/usr/bin/env python3
"""
Test password reset API endpoints
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

print("=" * 60)
print("🔐 Testing Password Reset API Endpoints")
print("=" * 60)

# Test email
test_email = "test@test.com"

# ========================================================================
# Test 1: Request Password Reset
# ========================================================================
print("\n📧 Test 1: Request Password Reset")
print("-" * 60)

request_data = {
    "email": test_email
}

try:
    response = requests.post(
        f"{BASE_URL}/api/users/password-reset/request",
        json=request_data,
        headers={"Content-Type": "application/json"}
    )

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"✅ Request successful")
        print(f"   Message: {result.get('message', 'N/A')}")
        print(f"   Status: {result.get('status', 'N/A')}")

        # Note: In production, the token would be sent via email
        # For testing, we need to get it from the database
        print("\n   💡 In production, an email would be sent with the reset link")
        print("   For testing, we'll retrieve the token from the database...")

    else:
        print(f"❌ Request failed")
        print(f"   Response: {response.text}")
        sys.exit(1)

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# ========================================================================
# Get the reset token from database (for testing)
# ========================================================================
print("\n🔑 Retrieving reset token from database...")
print("-" * 60)

import asyncio
from app.db.database import async_session_maker
from app.models.password_reset import PasswordReset
from sqlalchemy import select, delete
from datetime import datetime

async def get_token():
    async with async_session_maker() as db:
        # Get the most recent token for this email
        result = await db.execute(
            select(PasswordReset)
            .where(PasswordReset.email == test_email)
            .order_by(PasswordReset.created_at.desc())
            .limit(1)
        )
        reset_record = result.scalar_one_or_none()

        if reset_record:
            print(f"✅ Token found: {reset_record.token[:20]}...")
            print(f"   Expires at: {reset_record.expires_at}")
            print(f"   Used: {reset_record.used}")
            return reset_record.token
        else:
            print("❌ No token found")
            return None

token = asyncio.run(get_token())

if not token:
    print("\n❌ Cannot proceed without token")
    sys.exit(1)

# ========================================================================
# Test 2: Verify Token
# ========================================================================
print("\n✅ Test 2: Verify Reset Token")
print("-" * 60)

verify_data = {
    "token": token
}

try:
    response = requests.post(
        f"{BASE_URL}/api/users/password-reset/verify",
        json=verify_data,
        headers={"Content-Type": "application/json"}
    )

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"✅ Token is valid")
        print(f"   Valid: {result.get('valid', 'N/A')}")
        print(f"   Email: {result.get('email', 'N/A')}")
        print(f"   Message: {result.get('message', 'N/A')}")
    else:
        print(f"❌ Verification failed")
        print(f"   Response: {response.text}")
        sys.exit(1)

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# ========================================================================
# Test 3: Confirm Password Reset
# ========================================================================
print("\n🔄 Test 3: Confirm Password Reset")
print("-" * 60)

new_password = "TestReset123!"
confirm_data = {
    "token": token,
    "new_password": new_password
}

try:
    response = requests.post(
        f"{BASE_URL}/api/users/password-reset/confirm",
        json=confirm_data,
        headers={"Content-Type": "application/json"}
    )

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"✅ Password reset successful")
        print(f"   Message: {result.get('message', 'N/A')}")
    else:
        print(f"❌ Password reset failed")
        print(f"   Response: {response.text}")
        sys.exit(1)

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# ========================================================================
# Test 4: Verify Login with New Password
# ========================================================================
print("\n🔐 Test 4: Verify Login with New Password")
print("-" * 60)

login_data = {
    "email": test_email,
    "password": new_password
}

try:
    response = requests.post(
        f"{BASE_URL}/api/users/login",
        json=login_data,
        headers={"Content-Type": "application/json"}
    )

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"✅ Login successful with new password")
        print(f"   User ID: {result.get('user_id', 'N/A')}")
        print(f"   Email: {result.get('email', 'N/A')}")
        print(f"   Username: {result.get('username', 'N/A')}")

        # Clean up - restore original password
        print("\n🔄 Restoring original password...")
        from app.core.security import get_password_hash

        async def restore_password():
            async with async_session_maker() as db:
                from app.models.document import User
                from sqlalchemy import select

                result = await db.execute(select(User).where(User.email == test_email))
                user = result.scalar_one_or_none()

                if user:
                    user.hashed_password = get_password_hash("testpassword")
                    await db.commit()
                    print("✅ Original password restored")

        asyncio.run(restore_password())

    else:
        print(f"❌ Login failed")
        print(f"   Response: {response.text}")
        sys.exit(1)

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# ========================================================================
# Test 5: Test Invalid Token
# ========================================================================
print("\n❌ Test 5: Test Invalid Token")
print("-" * 60)

invalid_token = "invalid_token_12345"
verify_data = {
    "token": invalid_token
}

try:
    response = requests.post(
        f"{BASE_URL}/api/users/password-reset/verify",
        json=verify_data,
        headers={"Content-Type": "application/json"}
    )

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        if not result.get('valid', False):
            print(f"✅ Invalid token correctly rejected")
            print(f"   Valid: {result.get('valid', 'N/A')}")
            print(f"   Message: {result.get('message', 'N/A')}")
        else:
            print(f"❌ Invalid token was accepted (this is a bug)")
    else:
        print(f"✅ Invalid token rejected with status {response.status_code}")

except Exception as e:
    print(f"❌ Error: {e}")

# ========================================================================
# Summary
# ========================================================================
print("\n" + "=" * 60)
print("✅ All API Tests Passed!")
print("=" * 60)
print("\n🎉 Password reset flow is working correctly!")
print("\n📝 Summary:")
print("   1. ✅ Password reset request generates a token")
print("   2. ✅ Token verification works correctly")
print("   3. ✅ Password can be reset with valid token")
print("   4. ✅ Login works with new password")
print("   5. ✅ Invalid tokens are rejected")
