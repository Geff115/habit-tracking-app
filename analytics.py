"""
analytics.py - Analytics module for the Habit Tracking Application.

All functions in this module follow the functional programming paradigm.
Each one is a pure function that takes input, computes a result, and
returns it without modifying any external state.
"""

from habit import Habit


def get_all_habits(db):
    """
    Retrieve every habit currently stored in the database.

    Args:
        db (Database): The database to query.

    Returns:
        list[Habit]: All habits with their completion history loaded.
    """
    return Habit.load_all(db)


def get_habits_by_periodicity(db, periodicity):
    """
    Filter habits by their periodicity using a list comprehension.

    Args:
        db (Database): The database to query.
        periodicity (str): Either "daily" or "weekly".

    Returns:
        list[Habit]: Only the habits matching the given periodicity.
    """
    all_habits = Habit.load_all(db)
    return [h for h in all_habits if h.periodicity == periodicity]


def get_longest_streak_all(db):
    """
    Find the longest streak across all defined habits.

    Uses max() with a key function to find the habit with the best
    longest-ever streak.

    Args:
        db (Database): The database to query.

    Returns:
        tuple: (habit_name, longest_streak) for the habit with the best streak.
               Returns (None, 0) if there are no habits.
    """
    all_habits = Habit.load_all(db)
    if not all_habits:
        return (None, 0)

    best = max(all_habits, key=lambda h: h.get_longest_streak())
    return (best.name, best.get_longest_streak())


def get_longest_streak_for(db, habit_name):
    """
    Calculate the longest streak ever achieved for a specific habit.

    Args:
        db (Database): The database to query.
        habit_name (str): The name of the habit to analyse.

    Returns:
        int: The longest streak count, or 0 if the habit does not exist
             or has no completions.
    """
    habit = Habit.load(db, habit_name)
    if habit is None:
        return 0
    return habit.get_longest_streak()


def get_current_streak_for(db, habit_name):
    """
    Get the current (most recent) streak for a specific habit.

    Args:
        db (Database): The database to query.
        habit_name (str): The name of the habit.

    Returns:
        int: The current streak count.
    """
    habit = Habit.load(db, habit_name)
    if habit is None:
        return 0
    return habit.get_streak()


def get_most_struggled(db):
    """
    Find habits where the user has struggled the most, defined as
    habits with the lowest longest streak relative to their age.

    This gives an idea of which habits have been hardest to maintain.

    Args:
        db (Database): The database to query.

    Returns:
        list[Habit]: Habits sorted by longest streak (ascending),
                     so the most struggled ones come first.
    """
    all_habits = Habit.load_all(db)
    return sorted(all_habits, key=lambda h: h.get_longest_streak())


def get_habits_summary(db):
    """
    Generate a summary of all habits with their key statistics.

    Args:
        db (Database): The database to query.

    Returns:
        list[dict]: Each dict contains name, periodicity, total_completions,
                    current_streak, longest_streak, and is_broken.
    """
    all_habits = Habit.load_all(db)
    return list(map(
        lambda h: {
            "name": h.name,
            "periodicity": h.periodicity,
            "total_completions": len(h.completions),
            "current_streak": h.get_streak(),
            "longest_streak": h.get_longest_streak(),
            "is_broken": h.is_broken(),
        },
        all_habits
    ))
