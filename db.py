"""
db.py - Database module for the Habit Tracking Application.

Handles all SQLite read/write operations through a dedicated Database class.
The rest of the application never touches raw SQL directly; it all goes through here.
"""

import sqlite3
from datetime import datetime


class Database:
    """
    Wraps a SQLite connection and provides methods for storing
    and retrieving habit data.

    Attributes:
        db_path (str): File path to the SQLite database (or ":memory:" for testing).
        conn (sqlite3.Connection): The active database connection.
    """

    def __init__(self, db_path="habits.db"):
        """
        Open (or create) a SQLite database at the given path.

        Args:
            db_path (str): Path to the database file. Defaults to "habits.db".
                           Pass ":memory:" for an in-memory database (useful for tests).
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.create_tables()

    def create_tables(self):
        """
        Create the habits and completions tables if they do not already exist.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                name        TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                periodicity TEXT NOT NULL CHECK(periodicity IN ('daily', 'weekly')),
                created_at  TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS completions (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_name    TEXT NOT NULL,
                completed_at  TEXT NOT NULL,
                FOREIGN KEY (habit_name) REFERENCES habits(name) ON DELETE CASCADE
            )
        """)
        self.conn.commit()

    def add_habit(self, name, description, periodicity, created_at=None):
        """
        Insert a new habit into the database.

        Args:
            name (str): Unique name for the habit.
            description (str): Short description of the task.
            periodicity (str): Either "daily" or "weekly".
            created_at (str, optional): ISO-8601 timestamp. Defaults to now.

        Raises:
            sqlite3.IntegrityError: If a habit with this name already exists.
        """
        if created_at is None:
            created_at = datetime.now().isoformat()
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO habits (name, description, periodicity, created_at) VALUES (?, ?, ?, ?)",
            (name, description, periodicity, created_at),
        )
        self.conn.commit()

    def remove_habit(self, name):
        """
        Delete a habit and all its completion records.

        Args:
            name (str): The name of the habit to remove.

        Returns:
            bool: True if a habit was actually deleted, False if it did not exist.
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM habits WHERE name = ?", (name,))
        self.conn.commit()
        return cursor.rowcount > 0

    def get_habit_data(self, name):
        """
        Retrieve a single habit's metadata from the database.

        Args:
            name (str): The habit name to look up.

        Returns:
            tuple or None: (name, description, periodicity, created_at) if found.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT name, description, periodicity, created_at FROM habits WHERE name = ?", (name,))
        return cursor.fetchone()

    def get_all_habits_data(self):
        """
        Retrieve all habits from the database.

        Returns:
            list[tuple]: Each tuple is (name, description, periodicity, created_at).
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT name, description, periodicity, created_at FROM habits ORDER BY name")
        return cursor.fetchall()

    def add_completion(self, habit_name, completed_at=None):
        """
        Record a check-off event for a habit.

        Args:
            habit_name (str): Which habit was completed.
            completed_at (str, optional): ISO-8601 timestamp. Defaults to now.

        Raises:
            ValueError: If the habit does not exist in the database.
        """
        if self.get_habit_data(habit_name) is None:
            raise ValueError(f"Habit '{habit_name}' does not exist.")
        if completed_at is None:
            completed_at = datetime.now().isoformat()
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO completions (habit_name, completed_at) VALUES (?, ?)",
            (habit_name, completed_at),
        )
        self.conn.commit()

    def get_completions(self, habit_name):
        """
        Get all completion timestamps for a given habit, sorted chronologically.

        Args:
            habit_name (str): The habit to query.

        Returns:
            list[str]: ISO-8601 timestamps of each check-off event.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT completed_at FROM completions WHERE habit_name = ? ORDER BY completed_at",
            (habit_name,),
        )
        return [row[0] for row in cursor.fetchall()]

    def reset_db(self):
        """
        Drop all data from both tables. Useful for testing.
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM completions")
        cursor.execute("DELETE FROM habits")
        self.conn.commit()

    def close(self):
        """Close the database connection."""
        self.conn.close()
