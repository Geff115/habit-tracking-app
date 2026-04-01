"""
main.py - Command-line interface for the Habit Tracking Application.

This is the entry point. Run it with: python main.py

The menu uses the 'questionary' library for polished interactive prompts
if it is installed. Otherwise, it falls back to basic numbered input
so the app works either way.
"""

import sys
from db import Database
from habit import Habit
import analytics
from predefined import seed_database

# Try to import questionary for nicer prompts, but don't require it
try:
    import questionary
    HAS_QUESTIONARY = True
except ImportError:
    HAS_QUESTIONARY = False


def select_option(prompt, choices):
    """
    Present a list of choices to the user and return their selection.

    Uses questionary if available, otherwise falls back to numbered input.

    Args:
        prompt (str): The question to ask.
        choices (list[str]): Available options.

    Returns:
        str: The selected option, or None if the user cancelled.
    """
    if HAS_QUESTIONARY:
        result = questionary.select(prompt, choices=choices).ask()
        return result
    else:
        print(f"\n{prompt}")
        for i, choice in enumerate(choices, 1):
            print(f"  {i}. {choice}")
        while True:
            try:
                raw = input("Enter your choice (number): ").strip()
                idx = int(raw) - 1
                if 0 <= idx < len(choices):
                    return choices[idx]
                print(f"Please enter a number between 1 and {len(choices)}.")
            except ValueError:
                print("Invalid input. Please enter a number.")
            except (EOFError, KeyboardInterrupt):
                return None


def get_input(prompt):
    """
    Get a text input from the user.

    Args:
        prompt (str): The prompt to display.

    Returns:
        str: The user's input, stripped of whitespace.
    """
    if HAS_QUESTIONARY:
        return questionary.text(prompt).ask()
    else:
        try:
            return input(f"{prompt}: ").strip()
        except (EOFError, KeyboardInterrupt):
            return None


def confirm(prompt):
    """
    Ask the user a yes/no question.

    Args:
        prompt (str): The question.

    Returns:
        bool: True if the user confirmed.
    """
    if HAS_QUESTIONARY:
        return questionary.confirm(prompt).ask()
    else:
        try:
            answer = input(f"{prompt} (y/n): ").strip().lower()
            return answer in ("y", "yes")
        except (EOFError, KeyboardInterrupt):
            return False


def create_habit(db):
    """Prompt the user to create a new habit and save it."""
    name = get_input("Habit name")
    if not name:
        print("Cancelled.")
        return

    description = get_input("Short description")
    if not description:
        print("Cancelled.")
        return

    periodicity = select_option("How often?", ["daily", "weekly"])
    if not periodicity:
        print("Cancelled.")
        return

    try:
        habit = Habit(name, description, periodicity)
        habit.save(db)
        print(f"\nCreated habit: {habit}")
    except Exception as e:
        print(f"\nCould not create habit: {e}")


def delete_habit(db):
    """Prompt the user to delete an existing habit."""
    habits = analytics.get_all_habits(db)
    if not habits:
        print("\nNo habits to delete.")
        return

    names = [h.name for h in habits]
    name = select_option("Which habit to delete?", names)
    if not name:
        print("Cancelled.")
        return

    if confirm(f"Are you sure you want to delete '{name}'?"):
        if db.remove_habit(name):
            print(f"\nDeleted '{name}' and all its completion data.")
        else:
            print(f"\nHabit '{name}' not found.")
    else:
        print("Cancelled.")


def check_off_habit(db):
    """Prompt the user to check off a habit for the current period."""
    habits = analytics.get_all_habits(db)
    if not habits:
        print("\nNo habits to check off. Create one first.")
        return

    names = [h.name for h in habits]
    name = select_option("Which habit did you complete?", names)
    if not name:
        print("Cancelled.")
        return

    habit = Habit.load(db, name)
    habit.check_off(db)
    print(f"\nChecked off '{name}'! Current streak: {habit.get_streak()}")


def list_all_habits(db):
    """Display all tracked habits with their stats."""
    habits = analytics.get_all_habits(db)
    if not habits:
        print("\nNo habits tracked yet.")
        return

    print(f"\n{'Name':<20} {'Period':<10} {'Completions':<15} {'Current Streak':<16} {'Longest Streak'}")
    print("-" * 77)
    for h in habits:
        print(f"{h.name:<20} {h.periodicity:<10} {len(h.completions):<15} "
              f"{h.get_streak():<16} {h.get_longest_streak()}")


def list_by_periodicity(db):
    """List habits filtered by daily or weekly."""
    periodicity = select_option("Which periodicity?", ["daily", "weekly"])
    if not periodicity:
        print("Cancelled.")
        return

    habits = analytics.get_habits_by_periodicity(db, periodicity)
    if not habits:
        print(f"\nNo {periodicity} habits found.")
        return

    print(f"\n{periodicity.capitalize()} habits:")
    for h in habits:
        print(f"  - {h}")


def show_longest_streak_all(db):
    """Show which habit has the longest streak overall."""
    name, streak = analytics.get_longest_streak_all(db)
    if name is None:
        print("\nNo habits tracked yet.")
    else:
        print(f"\nLongest streak: {streak} periods, achieved by '{name}'")


def show_longest_streak_single(db):
    """Show the longest streak for a specific habit."""
    habits = analytics.get_all_habits(db)
    if not habits:
        print("\nNo habits tracked yet.")
        return

    names = [h.name for h in habits]
    name = select_option("Which habit?", names)
    if not name:
        print("Cancelled.")
        return

    streak = analytics.get_longest_streak_for(db, name)
    current = analytics.get_current_streak_for(db, name)
    print(f"\n'{name}': longest streak = {streak}, current streak = {current}")


def show_struggled_habits(db):
    """Show which habits the user has struggled with most."""
    struggled = analytics.get_most_struggled(db)
    if not struggled:
        print("\nNo habits tracked yet.")
        return

    print("\nHabits ranked by difficulty (most struggled first):")
    for i, h in enumerate(struggled, 1):
        print(f"  {i}. {h.name} (longest streak: {h.get_longest_streak()}, "
              f"completions: {len(h.completions)})")


def main():
    """Main application loop."""
    db = Database("habits.db")

    # Seed with predefined data if the database is empty
    seeded = seed_database(db)
    if seeded > 0:
        print(f"Welcome! Loaded {seeded} predefined habits with sample data.")
        print("You can explore them or create your own.\n")

    menu_choices = [
        "Create a new habit",
        "Delete a habit",
        "Check off a habit",
        "List all habits",
        "Filter habits by periodicity",
        "Longest streak (all habits)",
        "Longest streak (single habit)",
        "Most struggled habits",
        "Exit",
    ]

    while True:
        action = select_option("\nWhat would you like to do?", menu_choices)

        if action is None or action == "Exit":
            print("Goodbye!")
            db.close()
            break
        elif action == "Create a new habit":
            create_habit(db)
        elif action == "Delete a habit":
            delete_habit(db)
        elif action == "Check off a habit":
            check_off_habit(db)
        elif action == "List all habits":
            list_all_habits(db)
        elif action == "Filter habits by periodicity":
            list_by_periodicity(db)
        elif action == "Longest streak (all habits)":
            show_longest_streak_all(db)
        elif action == "Longest streak (single habit)":
            show_longest_streak_single(db)
        elif action == "Most struggled habits":
            show_struggled_habits(db)


if __name__ == "__main__":
    main()
