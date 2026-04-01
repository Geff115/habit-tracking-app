"""
habit.py - Habit domain model for the Habit Tracking Application.

Encapsulates what a habit is and how it behaves. Each Habit instance
represents a single recurring task that a user wants to track.
"""

from datetime import datetime, timedelta


class Habit:
    """
    Represents a single habit with its metadata and completion history.

    A habit has a name, description, and periodicity (daily or weekly).
    Users can check off a habit whenever they complete the associated task,
    and the system tracks whether they maintain a streak or break it.

    Attributes:
        name (str): Unique identifier for the habit.
        description (str): What the habit involves.
        periodicity (str): "daily" or "weekly".
        created_at (datetime): When the habit was first created.
        completions (list[datetime]): Sorted list of check-off timestamps.
    """

    def __init__(self, name, description, periodicity, created_at=None):
        """
        Create a new Habit instance.

        Args:
            name (str): Unique name for the habit.
            description (str): Short description of the task.
            periodicity (str): Either "daily" or "weekly".
            created_at (datetime or str, optional): When the habit was created.
                Accepts a datetime object or an ISO-8601 string. Defaults to now.

        Raises:
            ValueError: If periodicity is not "daily" or "weekly".
        """
        if periodicity not in ("daily", "weekly"):
            raise ValueError(f"Periodicity must be 'daily' or 'weekly', got '{periodicity}'")

        self.name = name
        self.description = description
        self.periodicity = periodicity

        if created_at is None:
            self.created_at = datetime.now()
        elif isinstance(created_at, str):
            self.created_at = datetime.fromisoformat(created_at)
        else:
            self.created_at = created_at

        self.completions = []

    def check_off(self, db, completed_at=None):
        """
        Mark this habit as completed and persist the event.

        Args:
            db (Database): The database instance to record the completion in.
            completed_at (datetime or str, optional): When the task was done.
                Defaults to now.
        """
        if completed_at is None:
            completed_at = datetime.now()
        elif isinstance(completed_at, str):
            completed_at = datetime.fromisoformat(completed_at)

        self.completions.append(completed_at)
        self.completions.sort()
        db.add_completion(self.name, completed_at.isoformat())

    def load_completions(self, db):
        """
        Load all completion timestamps from the database into this habit's
        in-memory list. Called when reconstructing a Habit from stored data.

        Args:
            db (Database): The database to read from.
        """
        raw = db.get_completions(self.name)
        self.completions = sorted([datetime.fromisoformat(ts) for ts in raw])

    def get_streak(self):
        """
        Calculate the current streak for this habit.

        A streak is the number of consecutive periods (days or weeks) where
        the habit was completed at least once, counting backwards from the
        most recent completion.

        Returns:
            int: The current streak count. Returns 0 if there are no completions.
        """
        if not self.completions:
            return 0

        periods = self._get_unique_periods()
        if not periods:
            return 0

        # Count backwards from the last period
        streak = 1
        for i in range(len(periods) - 1, 0, -1):
            expected_gap = 1 if self.periodicity == "daily" else 7
            diff = (periods[i] - periods[i - 1]).days
            if diff <= expected_gap:
                streak += 1
            else:
                break
        return streak

    def get_longest_streak(self):
        """
        Calculate the longest streak ever achieved for this habit.

        Returns:
            int: The longest streak count. Returns 0 if there are no completions.
        """
        if not self.completions:
            return 0

        periods = self._get_unique_periods()
        if not periods:
            return 0

        longest = 1
        current = 1
        for i in range(1, len(periods)):
            expected_gap = 1 if self.periodicity == "daily" else 7
            diff = (periods[i] - periods[i - 1]).days
            if diff <= expected_gap:
                current += 1
                longest = max(longest, current)
            else:
                current = 1
        return longest

    def is_broken(self):
        """
        Check whether the user has broken this habit, meaning they missed
        the current period entirely.

        Returns:
            bool: True if the habit is currently broken (no completion in
                  the latest expected period).
        """
        if not self.completions:
            # Never completed, so technically broken from the start
            return True

        last = self.completions[-1]
        now = datetime.now()

        if self.periodicity == "daily":
            return (now.date() - last.date()).days > 1
        else:
            # Weekly: broken if more than 7 days since last completion
            return (now - last).days > 7

    def _get_unique_periods(self):
        """
        Map each completion to its period start date and return unique
        sorted period dates.

        For daily habits, the period is simply the calendar date.
        For weekly habits, it is the Monday of that ISO week.

        Returns:
            list[datetime.date]: Sorted list of unique period start dates.
        """
        seen = set()
        for dt in self.completions:
            if self.periodicity == "daily":
                period = dt.date()
            else:
                # Get the Monday of the ISO week
                period = (dt - timedelta(days=dt.weekday())).date()
            seen.add(period)
        return sorted(seen)

    def save(self, db):
        """
        Persist this habit's metadata to the database.

        Args:
            db (Database): The database to write to.
        """
        db.add_habit(self.name, self.description, self.periodicity,
                     self.created_at.isoformat())

    @classmethod
    def load(cls, db, name):
        """
        Reconstruct a Habit instance from the database.

        Args:
            db (Database): The database to read from.
            name (str): The habit name to load.

        Returns:
            Habit or None: The loaded Habit, or None if it does not exist.
        """
        data = db.get_habit_data(name)
        if data is None:
            return None
        habit = cls(data[0], data[1], data[2], data[3])
        habit.load_completions(db)
        return habit

    @classmethod
    def load_all(cls, db):
        """
        Load every habit from the database.

        Args:
            db (Database): The database to read from.

        Returns:
            list[Habit]: All habits with their completions loaded.
        """
        rows = db.get_all_habits_data()
        habits = []
        for row in rows:
            habit = cls(row[0], row[1], row[2], row[3])
            habit.load_completions(db)
            habits.append(habit)
        return habits

    def __str__(self):
        """Human-readable representation of the habit."""
        streak = self.get_streak()
        total = len(self.completions)
        return (f"{self.name} ({self.periodicity}) - "
                f"{total} completions, current streak: {streak}")

    def __repr__(self):
        return f"Habit(name='{self.name}', periodicity='{self.periodicity}')"
