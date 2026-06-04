#!/usr/bin/env python3
"""
Test script to verify authentication and rate limiting functionality
"""
import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from taq.core.limiter import (
    TIER_LIMITS,
    LimitType,
    UserTier,
    get_investigations_per_day_limit,
    get_scoring_per_day_limit,
    get_queries_per_day_limit,
    get_playbooks_per_user_limit,
    can_access_premium_connectors,
    check_and_increment_daily_limit,
    check_and_increment_scoring_limit,
    check_and_increment_queries_limit
)
from taq.storage.models import UserModel


def test_tier_limits():
    """Test that tier limits are correctly defined"""
    print("Testing tier limits...")

    # Test free tier limits
    assert TIER_LIMITS[UserTier.FREE][LimitType.INVESTIGATIONS_PER_DAY] == 10
    assert TIER_LIMITS[UserTier.FREE][LimitType.CONNECTORS_PER_INVESTIGATION] == 3
    assert TIER_LIMITS[UserTier.FREE][LimitType.PREMIUM_CONNECTORS_ACCESS] == False
    assert TIER_LIMITS[UserTier.FREE][LimitType.PLAYBOOK_STEPS_LIMIT] == 5
    assert TIER_LIMITS[UserTier.FREE][LimitType.SCORING_PER_DAY] == 50
    assert TIER_LIMITS[UserTier.FREE][LimitType.QUERIES_PER_DAY] == 100
    assert TIER_LIMITS[UserTier.FREE][LimitType.PLAYBOOKS_PER_USER] == 5

    # Test premium tier limits
    assert TIER_LIMITS[UserTier.PREMIUM][LimitType.INVESTIGATIONS_PER_DAY] == 1000
    assert TIER_LIMITS[UserTier.PREMIUM][LimitType.CONNECTORS_PER_INVESTIGATION] == 50
    assert TIER_LIMITS[UserTier.PREMIUM][LimitType.PREMIUM_CONNECTORS_ACCESS] == True
    assert TIER_LIMITS[UserTier.PREMIUM][LimitType.PLAYBOOK_STEPS_LIMIT] == 100
    assert TIER_LIMITS[UserTier.PREMIUM][LimitType.SCORING_PER_DAY] == 10000
    assert TIER_LIMITS[UserTier.PREMIUM][LimitType.QUERIES_PER_DAY] == 10000
    assert TIER_LIMITS[UserTier.PREMIUM][LimitType.PLAYBOOKS_PER_USER] == 100

    print("✓ Tier limits test passed")


def test_limit_functions():
    """Test the limit getter functions"""
    print("Testing limit getter functions...")

    # Create mock users
    free_user = UserModel()
    free_user.tier = UserTier.FREE

    premium_user = UserModel()
    premium_user.tier = UserTier.PREMIUM

    # Test free user limits
    assert get_investigations_per_day_limit(free_user) == 10
    assert get_scoring_per_day_limit(free_user) == 50
    assert get_queries_per_day_limit(free_user) == 100
    assert get_playbooks_per_user_limit(free_user) == 5
    assert can_access_premium_connectors(free_user) == False

    # Test premium user limits
    assert get_investigations_per_day_limit(premium_user) == 1000
    assert get_scoring_per_day_limit(premium_user) == 10000
    assert get_queries_per_day_limit(premium_user) == 10000
    assert get_playbooks_per_user_limit(premium_user) == 100
    assert can_access_premium_connectors(premium_user) == True

    # Test unauthenticated user (treated as free)
    assert get_investigations_per_day_limit(None) == 10
    assert get_scoring_per_day_limit(None) == 50
    assert get_queries_per_day_limit(None) == 100
    assert get_playbooks_per_user_limit(None) == 5
    assert can_access_premium_connectors(None) == False

    print("✓ Limit getter functions test passed")


async def test_database_integration():
    """Test integration with database models"""
    print("Testing database model integration...")

    # Test that the UserModel has the new fields
    user = UserModel()

    # Check that new columns exist
    assert hasattr(user, 'scoring_today')
    assert hasattr(user, 'queries_today')
    assert hasattr(user, 'investigations_today')
    assert hasattr(user, 'last_reset_date')

    # Check that they are of correct type (SQLAlchemy Column)
    from sqlalchemy import Integer, DateTime
    assert isinstance(user.__table__.c.scoring_today.type, Integer)
    assert isinstance(user.__table__.c.queries_today.type, Integer)
    assert isinstance(user.__table__.c.investigations_today.type, Integer)
    assert isinstance(user.__table__.c.last_reset_date.type, DateTime)

    print("✓ Database model integration test passed")


def main():
    """Run all tests"""
    print("Running TaQ Engine authentication and limits tests...\n")

    try:
        test_tier_limits()
        test_limit_functions()

        # Run async test
        asyncio.run(test_database_integration())

        print("\n✅ All tests passed!")
        return 0

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())