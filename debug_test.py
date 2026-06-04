#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from taq.core.limiter import (
    TIER_LIMITS,
    LimitType,
    UserTier,
    get_investigations_per_day_limit,
    get_user_limit
)
from taq.storage.models import UserModel

# Create mock user
free_user = UserModel()
free_user.tier = UserTier.FREE

print("TIER_LIMITS[UserTier.FREE]:", TIER_LIMITS[UserTier.FREE])
print("TIER_LIMITS[UserTier.FREE][LimitType.INVESTIGATIONS_PER_DAY]:", TIER_LIMITS[UserTier.FREE][LimitType.INVESTIGATIONS_PER_DAY])

# Test get_user_limit directly
limit_val = get_user_limit(free_user, LimitType.INVESTIGATIONS_PER_DAY)
print("get_user_limit result:", limit_val)
print("type:", type(limit_val))

# Test get_investigations_per_day_limit
inv_limit = get_investigations_per_day_limit(free_user)
print("get_investigations_per_day_limit result:", inv_limit)
print("type:", type(inv_limit))