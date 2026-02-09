#!/usr/bin/env python3
"""
Test script for password reset flow
"""

import asyncio
import sys
from app.db.database import async_session_maker
from app.models.document import User
from app.models.password_reset import PasswordReset
from sqlalchemy import select, delete
from datetime import datetime, timedelta
import secrets


async def test_password_reset():
    """Test the complete password reset flow"""

    print("=" * 60)
    print("🔐 Testing Password Reset Flow")
    print("=" * 60)

    # Test email
    test_email = "test@test.com"

    async with async_session_maker() as db:
        # Step 1: Verify user exists
        print("\n📧 Step 1: Checking if user exists...")
        result = await db.execute(select(User).where(User.email == test_email))
        user = result.scalar_one_or_none()

        if not user:
            print(f"❌ User with email {test_email} not found")
            return False

        print(f"✅ User found: {user.username} ({user.email})")

        # Step 2: Clean up any existing tokens for this email
        print("\n🧹 Step 2: Cleaning up old reset tokens...")
        await db.execute(delete(PasswordReset).where(PasswordReset.email == test_email))
        await db.commit()
        print("✅ Old tokens cleaned up")

        # Step 3: Generate a reset token (simulate API request)
        print("\n🔑 Step 3: Generating password reset token...")
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=24)  # 24 hours

        reset_record = PasswordReset(
            email=test_email,
            token=token,
            expires_at=expires_at
        )

        db.add(reset_record)
        await db.commit()
        await db.refresh(reset_record)

        print(f"✅ Token generated: {token[:20]}...")
        print(f"   Expires at: {expires_at}")

        # Step 4: Verify the token (simulate verify endpoint)
        print("\n✅ Step 4: Verifying token...")
        result = await db.execute(
            select(PasswordReset).where(
                PasswordReset.token == token,
                PasswordReset.email == test_email
            )
        )
        reset_record = result.scalar_one_or_none()

        if not reset_record:
            print("❌ Token not found")
            return False

        # Check if expired
        if reset_record.expires_at < datetime.utcnow():
            print("❌ Token expired")
            return False

        print("✅ Token is valid")

        # Step 5: Confirm password reset (simulate confirm endpoint)
        print("\n🔄 Step 5: Confirming password reset...")
        new_password = "NewPassword123!"

        # Hash the new password
        from app.core.security import get_password_hash
        hashed_password = get_password_hash(new_password)

        # Update user password
        user.hashed_password = hashed_password

        # Delete the token
        await db.execute(delete(PasswordReset).where(PasswordReset.token == token))

        await db.commit()
        print("✅ Password updated successfully")
        print(f"   New password: {new_password}")

        # Step 6: Verify login with new password
        print("\n🔐 Step 6: Verifying login with new password...")
        from app.core.security import verify_password
        if verify_password(new_password, user.hashed_password):
            print("✅ Login successful with new password")
        else:
            print("❌ Login failed")
            return False

        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)

        return True


async def test_token_expiry():
    """Test token expiry validation"""

    print("\n" + "=" * 60)
    print("⏰ Testing Token Expiry")
    print("=" * 60)

    async with async_session_maker() as db:
        # Create an expired token
        print("\n📅 Creating expired token...")
        expired_token = secrets.token_urlsafe(32)
        expired_time = datetime.utcnow() - timedelta(hours=1)  # 1 hour ago

        reset_record = PasswordReset(
            email="test@test.com",
            token=expired_token,
            expires_at=expired_time
        )

        db.add(reset_record)
        await db.commit()

        # Try to verify expired token
        print("🔍 Verifying expired token...")
        result = await db.execute(
            select(PasswordReset).where(PasswordReset.token == expired_token)
        )
        record = result.scalar_one_or_none()

        if record and record.expires_at < datetime.utcnow():
            print("✅ Token correctly identified as expired")
        else:
            print("❌ Expiry check failed")
            return False

        # Clean up
        await db.execute(delete(PasswordReset).where(PasswordReset.token == expired_token))
        await db.commit()

        print("✅ Expiry test passed")
        return True


async def main():
    """Run all tests"""
    try:
        # Test 1: Complete password reset flow
        success1 = await test_password_reset()

        # Test 2: Token expiry
        success2 = await test_token_expiry()

        if success1 and success2:
            print("\n🎉 All password reset tests passed successfully!")
            return 0
        else:
            print("\n❌ Some tests failed")
            return 1

    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
