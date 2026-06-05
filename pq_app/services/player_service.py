"""
Player Service - Points accrual and spending logic
"""
from datetime import datetime, timezone, timedelta
from typing import Tuple, Dict, Any

from flask import current_app

from .. import model


class PlayerService:
    def __init__(self, db_session=None):
        self.db = db_session or model.db.session

    def xp_to_next(self, level: int) -> int:
        """XP required to advance from the given level to the next one."""
        cfg = current_app.config if current_app else {}
        base = int(cfg.get("XP_BASE", 100))
        growth = float(cfg.get("XP_GROWTH", 1.5))
        return int(base * (growth ** max(0, level - 1)))

    def award_xp(self, user: model.User, amount: int) -> Dict[str, Any]:
        """
        Award XP to a player, applying any resulting level-ups.

        exp_points tracks progress toward the next level (it resets on each level up).
        Each level grants HP_PER_LEVEL max HP and heals the player by that amount.

        Returns a summary dict describing what happened.
        """
        amount = max(0, int(amount))
        cfg = current_app.config if current_app else {}
        hp_per_level = int(cfg.get("HP_PER_LEVEL", 10))

        user.exp_points = (user.exp_points or 0) + amount
        levels_gained = 0
        hp_gained = 0
        # Loop so a single large award can grant multiple levels.
        while user.exp_points >= self.xp_to_next(user.level):
            user.exp_points -= self.xp_to_next(user.level)
            user.level += 1
            user.max_hp += hp_per_level
            hp_gained += hp_per_level
            levels_gained += 1

        if hp_gained:
            user.heal(hp_gained)
        self.db.add(user)

        return {
            "xp_awarded": amount,
            "leveled_up": levels_gained > 0,
            "levels_gained": levels_gained,
            "new_level": user.level,
            "hp_gained": hp_gained,
            "xp_to_next": self.xp_to_next(user.level),
        }

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
