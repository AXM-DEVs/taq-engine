#!/usr/bin/env python3
"""
Test script to verify API endpoints with authentication and rate limiting
"""
import asyncio
import sys
import os
import json
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import httpx
from taq.core.config import config


async def test_auth_endpoints():
    """Test authentication endpoints"""
    print("Testing authentication endpoints...")

    base_url = "http://localhost:8000/api/v1"

    async with httpx.AsyncClient() as client:
        # Test registration
        print("  Testing user registration...")
        register_data = {
            "email": "test2@example.com",
            "password": "securepassword123"
        }

        response = await client.post(f"{base_url}/auth/register", json=register_data)
        assert response.status_code == 200, f"Registration failed: {response.text}"
        user_data = response.json()
        assert "id" in user_data
        assert "email" in user_data
        assert user_data["email"] == "test2@example.com"
        assert user_data["tier"] == "free"
        assert "api_key" in user_data
        print("  ✓ Registration successful")

        api_key = user_data["api_key"]

        # Test login
        print("  Testing user login...")
        login_data = {
            "email": "test2@example.com",
            "password": "securepassword123"
        }

        response = await client.post(f"{base_url}/auth/login", json=login_data)
        assert response.status_code == 200, f"Login failed: {response.text}"
        login_response = response.json()
        assert login_response["id"] == user_data["id"]
        assert login_response["email"] == user_data["email"]
        assert login_response["api_key"] == api_key  # Should return same API key
        print("  ✓ Login successful")

        # Test get current user info
        print("  Testing get current user info...")
        headers = {"Authorization": f"Bearer {api_key}"}
        response = await client.get(f"{base_url}/auth/me", headers=headers)
        assert response.status_code == 200, f"Get user info failed: {response.text}"
        user_info = response.json()
        assert user_info["id"] == user_data["id"]
        assert user_info["email"] == user_data["email"]
        assert user_info["tier"] == "free"
        print("  ✓ Get user info successful")

        # Test invalid login
        print("  Testing invalid login...")
        invalid_login = {
            "email": "test2@example.com",
            "password": "wrongpassword"
        }
        response = await client.post(f"{base_url}/auth/login", json=invalid_login)
        assert response.status_code == 401, f"Invalid login should return 401: {response.text}"
        print("  ✓ Invalid login properly rejected")

        return api_key


async def test_investigation_endpoints(api_key):
    """Test investigation endpoints with authentication"""
    print("Testing investigation endpoints...")

    base_url = "http://localhost:8000/api/v1"
    headers = {"Authorization": f"Bearer {api_key}"}

    async with httpx.AsyncClient() as client:
        # Test creating an investigation
        print("  Testing investigation creation...")
        inv_data = {
            "seed_type": "domain",
            "seed_value": "example.com",
            "metadata": {"test": True}
        }

        response = await client.post(f"{base_url}/investigations/", json=inv_data, headers=headers)
        assert response.status_code == 201, f"Investigation creation failed: {response.text}"
        inv_response = response.json()
        assert "id" in inv_response
        assert inv_response["seed_type"] == "domain"
        assert inv_response["seed_value"] == "example.com"
        inv_id = inv_response["id"]
        print("  ✓ Investigation creation successful")

        # Test listing investigations
        print("  Testing investigation listing...")
        response = await client.get(f"{base_url}/investigations/", headers=headers)
        assert response.status_code == 200, f"Investigation listing failed: {response.text}"
        inv_list = response.json()
        assert "total" in inv_list
        assert "investigations" in inv_list
        assert len(inv_list["investigations"]) >= 1
        print("  ✓ Investigation listing successful")

        # Test getting specific investigation
        print("  Testing get specific investigation...")
        response = await client.get(f"{base_url}/investigations/{inv_id}", headers=headers)
        assert response.status_code == 200, f"Get investigation failed: {response.text}"
        inv_detail = response.json()
        assert inv_detail["id"] == inv_id
        assert inv_detail["seed_type"] == "domain"
        assert inv_detail["seed_value"] == "example.com"
        print("  ✓ Get specific investigation successful")

        # Test unauthenticated access (should fail)
        print("  Testing unauthenticated access...")
        response = await client.get(f"{base_url}/investigations/")
        assert response.status_code == 401, f"Unauthenticated access should return 401: {response.text}"
        print("  ✓ Unauthenticated access properly rejected")

        return inv_id


async def test_rate_limiting():
    """Test rate limiting on auth endpoints"""
    print("Testing rate limiting...")

    base_url = "http://localhost:8000/api/v1"

    async with httpx.AsyncClient() as client:
        # Test rate limiting on login endpoint (5 attempts allowed by default)
        print("  Testing login rate limiting...")
        for i in range(5):
            response = await client.post(f"{base_url}/auth/login", json={
                "email": "nonexistent@example.com",
                "password": "wrongpassword"
            })
            # First 4 attempts should either be 401 (invalid credentials) or 429 (rate limited)
            # The 5th should be 429
            if i < 4:
                assert response.status_code in [401, 429], f"Unexpected status {response.status_code} on attempt {i+1}"
            else:
                # 5th attempt should be rate limited
                assert response.status_code == 429, f"Expected 429 on attempt 5, got {response.status_code}"
                print("  ✓ Rate limiting working correctly")
                break
        else:
            # If we didn't break, rate limiting might not be working as expected
            print("  ⚠ Rate limiting test inconclusive (may need more attempts)")


async def main():
    """Run all tests"""
    print("Running TaQ Engine API endpoint tests...\n")

    try:
        # Test authentication
        api_key = await test_auth_endpoints()
        print()

        # Test investigation endpoints
        inv_id = await test_investigation_endpoints(api_key)
        print()

        # Test rate limiting
        await test_rate_limiting()
        print()

        print("✅ All API endpoint tests completed!")
        return 0

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    # Make sure server is running
    print("Note: This test assumes the TaQ Engine server is running on localhost:8000")
    print("Make sure to start the server with: python -m taq.main --host 0.0.0.0 --port 8000\n")

    asyncio.run(main())