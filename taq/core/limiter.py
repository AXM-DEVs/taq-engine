from enum import Enum
from datetime import datetime, date
from typing import Optional
from taq.storage.models import UserTier, UserModel
from sqlalchemy.ext.asyncio import AsyncSession


class LimitType(str, Enum):
    INVESTIGATIONS_PER_DAY = "investigations_per_day"
    CONNECTORS_PER_INVESTIGATION = "connectors_per_investigation"
    PREMIUM_CONNECTORS_ACCESS = "premium_connectors_access"
    PLAYBOOK_STEPS_LIMIT = "playbook_steps_limit"
    SCORING_PER_DAY = "scoring_per_day"
    QUERIES_PER_DAY = "queries_per_day"
    PLAYBOOKS_PER_USER = "playbooks_per_user"


# Define limits for each tier
TIER_LIMITS = {
    UserTier.FREE: {
        LimitType.INVESTIGATIONS_PER_DAY: 10,
        LimitType.CONNECTORS_PER_INVESTIGATION: 3,
        LimitType.PREMIUM_CONNECTORS_ACCESS: False,  # No access to premium connectors
        LimitType.PLAYBOOK_STEPS_LIMIT: 5,
        LimitType.SCORING_PER_DAY: 50,  # 50 scorings per day for free tier
        LimitType.QUERIES_PER_DAY: 100,  # 100 queries per day for free tier
        LimitType.PLAYBOOKS_PER_USER: 5,   # Max 5 playbooks per user for free tier
    },
    UserTier.PREMIUM: {
        LimitType.INVESTIGATIONS_PER_DAY: 1000,  # Effectively unlimited for most users
        LimitType.CONNECTORS_PER_INVESTIGATION: 50,
        LimitType.PREMIUM_CONNECTORS_ACCESS: True,  # Access to all connectors
        LimitType.PLAYBOOK_STEPS_LIMIT: 100,
        LimitType.SCORING_PER_DAY: 10000,  # Effectively unlimited scorings
        LimitType.QUERIES_PER_DAY: 10000,   # Effectively unlimited queries
        LimitType.PLAYBOOKS_PER_USER: 100,  # Max 100 playbooks per user for premium
    },
}


async def check_user_limit(
    user: Optional[UserModel],
    limit_type: LimitType,
    current_usage: int,
    session: AsyncSession
) -> bool:
    """
    Check if the user has exceeded a specific limit.

    Args:
        user: The user object (None for unauthenticated, treated as free with stricter limits?)
        limit_type: The type of limit to check
        current_usage: The current usage count for this limit period
        session: Database session (for potential future use, e.g., to get updated limits)

    Returns:
        True if within limit, False if exceeded
    """
    # For now, treat unauthenticated users as free tier with free limits
    # In the future, we might want stricter limits for anonymous users
    tier = user.tier if user else UserTier.FREE

    limit = TIER_LIMITS.get(tier, {}).get(limit_type)

    # If no limit defined, assume no limit (or could raise an error)
    if limit is None:
        return True

    return current_usage < limit


def get_user_limit(
    user: Optional[UserModel],
    limit_type: LimitType
) -> int:
    """
    Get the limit value for a user and limit type.

    Args:
        user: The user object
        limit_type: The type of limit

    Returns:
        The limit value (or a high number if essentially unlimited)
    """
    tier = user.tier if user else UserTier.FREE
    limit = TIER_LIMITS.get(tier, {}).get(limit_type)

    # If limit is None, return a high number (or handle as unlimited)
    if limit is None:
        # For limits that are boolean (like premium access), we return 1 if True else 0
        if limit_type == LimitType.PREMIUM_CONNECTORS_ACCESS:
            return 1 if (tier == UserTier.PREMIUM) else 0
        # For numeric limits, return a high number to indicate unlimited
        return 1000000

    return limit


def can_access_premium_connectors(user: Optional[UserModel]) -> bool:
    """Check if user can access premium connectors"""
    tier = user.tier if user else UserTier.FREE
    return TIER_LIMITS.get(tier, {}).get(LimitType.PREMIUM_CONNECTORS_ACCESS, False)


def get_investigations_per_day_limit(user: Optional[UserModel]) -> int:
    """Get the daily investigation limit for a user"""
    return get_user_limit(user, LimitType.INVESTIGATIONS_PER_DAY)


def get_connectors_per_investigation_limit(user: Optional[UserModel]) -> int:
    """Get the maximum number of connectors per investigation for a user"""
    return get_user_limit(user, LimitType.CONNECTORS_PER_INVESTIGATION)


def get_playbook_steps_limit(user: Optional[UserModel]) -> int:
    """Get the maximum number of steps allowed in a playbook for a user"""
    return get_user_limit(user, LimitType.PLAYBOOK_STEPS_LIMIT)


def get_scoring_per_day_limit(user: Optional[UserModel]) -> int:
    """Get the daily scoring limit for a user"""
    return get_user_limit(user, LimitType.SCORING_PER_DAY)


def get_queries_per_day_limit(user: Optional[UserModel]) -> int:
    """Get the daily query limit for a user"""
    return get_user_limit(user, LimitType.QUERIES_PER_DAY)


def get_playbooks_per_user_limit(user: Optional[UserModel]) -> int:
    """Get the maximum number of playbooks a user can create"""
    return get_user_limit(user, LimitType.PLAYBOOKS_PER_USER)


async def check_and_increment_daily_limit(user: UserModel, session: AsyncSession) -> bool:
    """
    Check if user has exceeded their daily investigation limit and increment if not.

    Args:
        user: The user object
        session: Database session

    Returns:
        True if user can proceed (within limit), False if limit exceeded
    """
    from datetime import date

    today = date.today()

    # Reset daily counter if it's a new day
    if user.last_reset_date.date() != today:
        user.investigations_today = 0
        user.scoring_today = 0
        user.queries_today = 0
        user.last_reset_date = datetime.utcnow()

    # Check if user has exceeded their limit
    daily_limit = get_investigations_per_day_limit(user)
    if user.investigations_today >= daily_limit:
        return False

    # Increment the counter
    user.investigations_today += 1
    await session.commit()

    return True


async def check_and_increment_scoring_limit(user: UserModel, session: AsyncSession) -> bool:
    """
    Check if user has exceeded their daily scoring limit and increment if not.

    Args:
        user: The user object
        session: Database session

    Returns:
        True if user can proceed (within limit), False if limit exceeded
    """
    from datetime import date

    today = date.today()

    # Reset daily counter if it's a new day
    if user.last_reset_date.date() != today:
        user.investigations_today = 0
        user.scoring_today = 0
        user.queries_today = 0
        user.last_reset_date = datetime.utcnow()

    # Check if user has exceeded their limit
    daily_limit = get_scoring_per_day_limit(user)
    if user.scoring_today >= daily_limit:
        return False

    # Increment the counter
    user.scoring_today += 1
    await session.commit()

    return True


async def check_and_increment_queries_limit(user: UserModel, session: AsyncSession) -> bool:
    """
    Check if user has exceeded their daily query limit and increment if not.

    Args:
        user: The user object
        session: Database session

    Returns:
        True if user can proceed (within limit), False if limit exceeded
    """
    from datetime import date

    today = date.today()

    # Reset daily counter if it's a new day
    if user.last_reset_date.date() != today:
        user.investigations_today = 0
        user.scoring_today = 0
        user.queries_today = 0
        user.last_reset_date = datetime.utcnow()

    # Check if user has exceeded their limit
    daily_limit = get_queries_per_day_limit(user)
    if user.queries_today >= daily_limit:
        return False

    # Increment the counter
    user.queries_today += 1
    await session.commit()

    return True