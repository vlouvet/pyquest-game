"""
Player Service - Points accrual and spending logic
"""
from datetime import datetime, timezone, timedelta
from typing import Tuple

from .. import model


class PlayerService:
    def __init__(self, db_session=None):
        self.db = db_session or model.db.session

    def accrue_points(self, user: model.User) -> int:
        """
        Lazily accrue points at 5 points per whole hour elapsed since last accrual.
        Returns number of points added.
        """
        # Use timezone-aware UTC datetimes. If stored value is naive, assume UTC.
        now = datetime.now(timezone.utc)
        last = user.last_points_accrual_at
        if isinstance(last, datetime) and last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        if last is None:
            # Initialize accrual timestamp without awarding immediately to avoid burst on first run
            user.last_points_accrual_at = now
            self.db.add(user)
            return 0
        # Compute whole hours elapsed
        elapsed_seconds = (now - last).total_seconds()
        hours = int(elapsed_seconds // 3600)
        if hours <= 0:
            return 0
        added = 5 * hours
        user.points = (user.points or 0) + added
        # Advance accrual timestamp by whole hours to preserve remainder
        user.last_points_accrual_at = (last + timedelta(hours=hours)).astimezone(timezone.utc)
        self.db.add(user)
        return added

    def spend_point(self, user: model.User) -> Tuple[bool, int]:
        """
        Spend 1 point for a tile action. Returns (ok, remaining_points).
        Policy: do not block actions when at 0; clamp at 0.
        """
        balance = user.points or 0
        if balance <= 0:
            # Allow action, keep balance at 0
            return True, 0
        user.points = balance - 1
        self.db.add(user)
        return True, user.points
