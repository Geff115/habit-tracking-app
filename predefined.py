"""
predefined.py - Predefined habits and sample data for the Habit Tracking Application.

Contains 5 example habits (3 daily, 2 weekly) along with 4 weeks of
simulated completion data. This data serves two purposes:
  1. Seeding the database on first run so users have something to explore.
  2. Acting as test fixtures for the unit test suite.

Some habits intentionally have gaps in their completion data so that
streak-break detection can be tested properly.
"""

from datetime import datetime, timedelta


# The sample data covers a 4-week window starting from this date.
# Using a fixed reference makes tests deterministic.
SAMPLE_START = datetime(2025, 3, 1)


PREDEFINED_HABITS = [
    {
        "name": "Brush Teeth",
        "description": "Brush teeth morning and evening",
        "periodicity": "daily",
    },
    {
        "name": "Exercise",
        "description": "At least 30 minutes of physical activity",
        "periodicity": "daily",
    },
    {
        "name": "Read",
        "description": "Read for at least 20 minutes",
        "periodicity": "daily",
    },
    {
        "name": "Laundry",
        "description": "Do the weekly laundry",
        "periodicity": "weekly",
    },
    {
        "name": "Meal Prep",
        "description": "Prepare meals for the upcoming week",
        "periodicity": "weekly",
    },
]


def _daily_completions(start, days_completed):
    """
    Generate completion timestamps for specific days relative to start.

    Args:
        start (datetime): The reference start date.
        days_completed (list[int]): Which day offsets had completions
                                     (0 = start day, 1 = next day, etc.)

    Returns:
        list[str]: ISO-8601 timestamps, each at 08:00 on the given day.
    """
    completions = []
    for day in days_completed:
        dt = start + timedelta(days=day)
        dt = dt.replace(hour=8, minute=0, second=0)
        completions.append(dt.isoformat())
    return completions


def _weekly_completions(start, weeks_completed):
    """
    Generate completion timestamps for specific weeks relative to start.

    Args:
        start (datetime): The reference start date.
        weeks_completed (list[int]): Which week offsets had completions
                                      (0 = first week, 1 = second week, etc.)

    Returns:
        list[str]: ISO-8601 timestamps, each on Saturday at 10:00 of that week.
    """
    completions = []
    for week in weeks_completed:
        dt = start + timedelta(weeks=week, days=5)  # Saturday
        dt = dt.replace(hour=10, minute=0, second=0)
        completions.append(dt.isoformat())
    return completions


def get_sample_completions():
    """
    Build 4 weeks of sample completion data for each predefined habit.

    Returns a dict mapping habit names to lists of ISO-8601 timestamps.

    The data is designed as follows:
      - Brush Teeth: completed every day for 28 days (perfect streak of 28)
      - Exercise: completed most days but missed days 6, 13, 20
        (creates multiple shorter streaks)
      - Read: completed for the first 18 days, then stopped
        (streak of 18, then broken)
      - Laundry: completed all 4 weeks (perfect weekly streak of 4)
      - Meal Prep: completed weeks 0, 1, and 3 but missed week 2
        (broken streak)

    Returns:
        dict[str, list[str]]: Habit name to list of completion timestamps.
    """
    start = SAMPLE_START

    # Brush Teeth: every single day for 28 days
    brush_days = list(range(28))

    # Exercise: most days, but skip day 6, 13, 20 (once per week missed)
    exercise_days = [d for d in range(28) if d not in (6, 13, 20)]

    # Read: first 18 days only, then the user stopped
    read_days = list(range(18))

    # Laundry: all 4 weeks
    laundry_weeks = [0, 1, 2, 3]

    # Meal Prep: weeks 0, 1, 3 (missed week 2)
    meal_prep_weeks = [0, 1, 3]

    return {
        "Brush Teeth": _daily_completions(start, brush_days),
        "Exercise": _daily_completions(start, exercise_days),
        "Read": _daily_completions(start, read_days),
        "Laundry": _weekly_completions(start, laundry_weeks),
        "Meal Prep": _weekly_completions(start, meal_prep_weeks),
    }


def seed_database(db):
    """
    Populate the database with predefined habits and their sample data.

    This is called on first run (when the database is empty) so users
    have something to work with immediately.

    Args:
        db (Database): The database to seed.

    Returns:
        int: Number of habits that were inserted.
    """
    existing = db.get_all_habits_data()
    if len(existing) > 0:
        return 0  # database already has data, do not overwrite

    sample_completions = get_sample_completions()
    count = 0

    for habit_info in PREDEFINED_HABITS:
        db.add_habit(
            habit_info["name"],
            habit_info["description"],
            habit_info["periodicity"],
            SAMPLE_START.isoformat(),
        )
        for ts in sample_completions.get(habit_info["name"], []):
            db.add_completion(habit_info["name"], ts)
        count += 1

    return count
