"""
test_habit.py - Unit test suite for the Habit Tracking Application.

Tests cover:
  - Database CRUD operations
  - Habit creation and attribute validation
  - Completion tracking and timestamp recording
  - Streak calculation for daily and weekly habits
  - Analytics module functions
  - Edge cases like missing periods and empty databases

All tests use an in-memory SQLite database so nothing touches disk.
Run with: python -m unittest test_habit -v
"""

import unittest
from datetime import datetime, timedelta
from db import Database
from habit import Habit
import analytics
from predefined import (
    PREDEFINED_HABITS,
    get_sample_completions,
    seed_database,
    SAMPLE_START,
)


class TestDatabase(unittest.TestCase):
    """Tests for the Database class (db.py)."""

    def setUp(self):
        """Create a fresh in-memory database before each test."""
        self.db = Database(":memory:")

    def tearDown(self):
        """Close the database after each test."""
        self.db.close()

    def test_create_tables(self):
        """Tables should exist after initialisation."""
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        self.assertIn("habits", tables)
        self.assertIn("completions", tables)

    def test_add_and_get_habit(self):
        """Adding a habit should make it retrievable."""
        self.db.add_habit("Test", "A test habit", "daily")
        data = self.db.get_habit_data("Test")
        self.assertIsNotNone(data)
        self.assertEqual(data[0], "Test")
        self.assertEqual(data[1], "A test habit")
        self.assertEqual(data[2], "daily")

    def test_add_duplicate_habit_fails(self):
        """Inserting a habit with the same name should raise an error."""
        self.db.add_habit("Test", "First", "daily")
        with self.assertRaises(Exception):
            self.db.add_habit("Test", "Second", "weekly")

    def test_remove_habit(self):
        """Removing a habit should delete it and its completions."""
        self.db.add_habit("Test", "Desc", "daily")
        self.db.add_completion("Test", "2025-03-01T08:00:00")
        result = self.db.remove_habit("Test")
        self.assertTrue(result)
        self.assertIsNone(self.db.get_habit_data("Test"))
        self.assertEqual(self.db.get_completions("Test"), [])

    def test_remove_nonexistent_habit(self):
        """Removing a habit that doesn't exist should return False."""
        result = self.db.remove_habit("Nonexistent")
        self.assertFalse(result)

    def test_add_completion(self):
        """Completions should be recorded and retrievable."""
        self.db.add_habit("Test", "Desc", "daily")
        self.db.add_completion("Test", "2025-03-01T08:00:00")
        self.db.add_completion("Test", "2025-03-02T08:00:00")
        completions = self.db.get_completions("Test")
        self.assertEqual(len(completions), 2)

    def test_add_completion_nonexistent_habit(self):
        """Completing a nonexistent habit should raise ValueError."""
        with self.assertRaises(ValueError):
            self.db.add_completion("Ghost", "2025-03-01T08:00:00")

    def test_get_all_habits_data(self):
        """Should return all habits in the database."""
        self.db.add_habit("A", "Desc A", "daily")
        self.db.add_habit("B", "Desc B", "weekly")
        data = self.db.get_all_habits_data()
        self.assertEqual(len(data), 2)

    def test_reset_db(self):
        """Resetting should clear all data."""
        self.db.add_habit("Test", "Desc", "daily")
        self.db.add_completion("Test", "2025-03-01T08:00:00")
        self.db.reset_db()
        self.assertEqual(self.db.get_all_habits_data(), [])


class TestHabit(unittest.TestCase):
    """Tests for the Habit class (habit.py)."""

    def setUp(self):
        self.db = Database(":memory:")

    def tearDown(self):
        self.db.close()

    def test_create_habit(self):
        """Habit should be created with correct attributes."""
        h = Habit("Test", "Description", "daily")
        self.assertEqual(h.name, "Test")
        self.assertEqual(h.description, "Description")
        self.assertEqual(h.periodicity, "daily")
        self.assertEqual(h.completions, [])

    def test_invalid_periodicity(self):
        """Creating a habit with wrong periodicity should raise ValueError."""
        with self.assertRaises(ValueError):
            Habit("Bad", "Desc", "monthly")

    def test_save_and_load(self):
        """A habit saved to the database should be loadable."""
        h = Habit("Test", "Desc", "weekly")
        h.save(self.db)
        loaded = Habit.load(self.db, "Test")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.name, "Test")
        self.assertEqual(loaded.periodicity, "weekly")

    def test_load_nonexistent(self):
        """Loading a nonexistent habit should return None."""
        self.assertIsNone(Habit.load(self.db, "Ghost"))

    def test_check_off(self):
        """Checking off a habit should record the completion."""
        h = Habit("Test", "Desc", "daily")
        h.save(self.db)
        h.check_off(self.db)
        self.assertEqual(len(h.completions), 1)
        # Verify it is also in the database
        completions = self.db.get_completions("Test")
        self.assertEqual(len(completions), 1)

    def test_str_representation(self):
        """String representation should include name and streak info."""
        h = Habit("Test", "Desc", "daily")
        result = str(h)
        self.assertIn("Test", result)
        self.assertIn("daily", result)


class TestDailyStreak(unittest.TestCase):
    """Tests for streak calculation with daily habits."""

    def setUp(self):
        self.db = Database(":memory:")

    def tearDown(self):
        self.db.close()

    def test_no_completions(self):
        """A habit with no completions should have streak 0."""
        h = Habit("Empty", "No data", "daily")
        self.assertEqual(h.get_streak(), 0)
        self.assertEqual(h.get_longest_streak(), 0)

    def test_single_completion(self):
        """A single completion should give a streak of 1."""
        h = Habit("Test", "Desc", "daily")
        h.completions = [datetime(2025, 3, 1, 8, 0)]
        self.assertEqual(h.get_streak(), 1)
        self.assertEqual(h.get_longest_streak(), 1)

    def test_consecutive_days(self):
        """Consecutive daily completions should build a streak."""
        h = Habit("Test", "Desc", "daily")
        h.completions = [
            datetime(2025, 3, 1, 8, 0),
            datetime(2025, 3, 2, 8, 0),
            datetime(2025, 3, 3, 8, 0),
            datetime(2025, 3, 4, 8, 0),
            datetime(2025, 3, 5, 8, 0),
        ]
        self.assertEqual(h.get_streak(), 5)
        self.assertEqual(h.get_longest_streak(), 5)

    def test_broken_streak(self):
        """A gap in completions should break the streak."""
        h = Habit("Test", "Desc", "daily")
        h.completions = [
            datetime(2025, 3, 1, 8, 0),
            datetime(2025, 3, 2, 8, 0),
            datetime(2025, 3, 3, 8, 0),
            # gap on March 4
            datetime(2025, 3, 5, 8, 0),
            datetime(2025, 3, 6, 8, 0),
        ]
        self.assertEqual(h.get_streak(), 2)       # current streak: 5, 6
        self.assertEqual(h.get_longest_streak(), 3)  # longest: 1, 2, 3

    def test_multiple_completions_same_day(self):
        """Multiple check-offs on the same day should count as one period."""
        h = Habit("Test", "Desc", "daily")
        h.completions = [
            datetime(2025, 3, 1, 8, 0),
            datetime(2025, 3, 1, 20, 0),  # same day, evening
            datetime(2025, 3, 2, 8, 0),
        ]
        self.assertEqual(h.get_streak(), 2)


class TestWeeklyStreak(unittest.TestCase):
    """Tests for streak calculation with weekly habits."""

    def setUp(self):
        self.db = Database(":memory:")

    def tearDown(self):
        self.db.close()

    def test_consecutive_weeks(self):
        """Completions in consecutive weeks should build a streak."""
        h = Habit("Test", "Desc", "weekly")
        h.completions = [
            datetime(2025, 3, 1, 10, 0),   # week 1 (Sat)
            datetime(2025, 3, 8, 10, 0),   # week 2
            datetime(2025, 3, 15, 10, 0),  # week 3
            datetime(2025, 3, 22, 10, 0),  # week 4
        ]
        self.assertEqual(h.get_streak(), 4)
        self.assertEqual(h.get_longest_streak(), 4)

    def test_missed_week(self):
        """Skipping a week should break the streak."""
        h = Habit("Test", "Desc", "weekly")
        h.completions = [
            datetime(2025, 3, 1, 10, 0),   # week 1
            datetime(2025, 3, 8, 10, 0),   # week 2
            # missed week 3
            datetime(2025, 3, 22, 10, 0),  # week 4
        ]
        self.assertEqual(h.get_streak(), 1)       # only week 4
        self.assertEqual(h.get_longest_streak(), 2)  # weeks 1-2


class TestAnalytics(unittest.TestCase):
    """Tests for the analytics module (analytics.py)."""

    def setUp(self):
        """Set up a database with predefined sample data."""
        self.db = Database(":memory:")
        seed_database(self.db)

    def tearDown(self):
        self.db.close()

    def test_get_all_habits(self):
        """Should return all 5 predefined habits."""
        habits = analytics.get_all_habits(self.db)
        self.assertEqual(len(habits), 5)

    def test_get_daily_habits(self):
        """Should return only daily habits."""
        daily = analytics.get_habits_by_periodicity(self.db, "daily")
        self.assertEqual(len(daily), 3)
        for h in daily:
            self.assertEqual(h.periodicity, "daily")

    def test_get_weekly_habits(self):
        """Should return only weekly habits."""
        weekly = analytics.get_habits_by_periodicity(self.db, "weekly")
        self.assertEqual(len(weekly), 2)
        for h in weekly:
            self.assertEqual(h.periodicity, "weekly")

    def test_longest_streak_all(self):
        """Brush Teeth has a perfect 28-day streak, should be the longest."""
        name, streak = analytics.get_longest_streak_all(self.db)
        self.assertEqual(name, "Brush Teeth")
        self.assertEqual(streak, 28)

    def test_longest_streak_brush_teeth(self):
        """Brush Teeth should have a longest streak of 28."""
        streak = analytics.get_longest_streak_for(self.db, "Brush Teeth")
        self.assertEqual(streak, 28)

    def test_longest_streak_exercise(self):
        """Exercise has gaps on days 6, 13, 20, so max streak should be 7 (days 21-27)."""
        streak = analytics.get_longest_streak_for(self.db, "Exercise")
        self.assertEqual(streak, 7)

    def test_longest_streak_read(self):
        """Read has 18 consecutive days."""
        streak = analytics.get_longest_streak_for(self.db, "Read")
        self.assertEqual(streak, 18)

    def test_longest_streak_laundry(self):
        """Laundry has 4 consecutive weeks."""
        streak = analytics.get_longest_streak_for(self.db, "Laundry")
        self.assertEqual(streak, 4)

    def test_longest_streak_meal_prep(self):
        """Meal Prep missed week 2, so longest streak is 2 (weeks 0-1)."""
        streak = analytics.get_longest_streak_for(self.db, "Meal Prep")
        self.assertEqual(streak, 2)

    def test_longest_streak_nonexistent(self):
        """Querying a nonexistent habit should return 0."""
        streak = analytics.get_longest_streak_for(self.db, "Ghost")
        self.assertEqual(streak, 0)

    def test_most_struggled(self):
        """Most struggled habits should come first (lowest streak)."""
        struggled = analytics.get_most_struggled(self.db)
        self.assertEqual(len(struggled), 5)
        # The first habit should have the smallest longest streak
        streaks = [h.get_longest_streak() for h in struggled]
        self.assertEqual(streaks, sorted(streaks))

    def test_habits_summary(self):
        """Summary should contain all expected keys for each habit."""
        summary = analytics.get_habits_summary(self.db)
        self.assertEqual(len(summary), 5)
        for entry in summary:
            self.assertIn("name", entry)
            self.assertIn("periodicity", entry)
            self.assertIn("total_completions", entry)
            self.assertIn("current_streak", entry)
            self.assertIn("longest_streak", entry)
            self.assertIn("is_broken", entry)

    def test_empty_database(self):
        """Analytics should handle an empty database gracefully."""
        empty_db = Database(":memory:")
        self.assertEqual(analytics.get_all_habits(empty_db), [])
        self.assertEqual(analytics.get_habits_by_periodicity(empty_db, "daily"), [])
        name, streak = analytics.get_longest_streak_all(empty_db)
        self.assertIsNone(name)
        self.assertEqual(streak, 0)
        empty_db.close()


class TestPredefinedData(unittest.TestCase):
    """Tests for the predefined data and seeding logic."""

    def setUp(self):
        self.db = Database(":memory:")

    def tearDown(self):
        self.db.close()

    def test_seed_creates_habits(self):
        """Seeding should create all 5 predefined habits."""
        count = seed_database(self.db)
        self.assertEqual(count, 5)
        self.assertEqual(len(self.db.get_all_habits_data()), 5)

    def test_seed_does_not_duplicate(self):
        """Seeding twice should not duplicate data."""
        seed_database(self.db)
        count = seed_database(self.db)
        self.assertEqual(count, 0)

    def test_brush_teeth_completions(self):
        """Brush Teeth should have 28 completions (one per day)."""
        seed_database(self.db)
        completions = self.db.get_completions("Brush Teeth")
        self.assertEqual(len(completions), 28)

    def test_exercise_completions(self):
        """Exercise should have 25 completions (28 - 3 missed days)."""
        seed_database(self.db)
        completions = self.db.get_completions("Exercise")
        self.assertEqual(len(completions), 25)

    def test_laundry_completions(self):
        """Laundry should have 4 completions (one per week)."""
        seed_database(self.db)
        completions = self.db.get_completions("Laundry")
        self.assertEqual(len(completions), 4)

    def test_meal_prep_completions(self):
        """Meal Prep should have 3 completions (missed week 2)."""
        seed_database(self.db)
        completions = self.db.get_completions("Meal Prep")
        self.assertEqual(len(completions), 3)


if __name__ == "__main__":
    unittest.main()
