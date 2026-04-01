# Habit Tracking Application

A Python command-line application for tracking daily and weekly habits. Built with object-oriented and functional programming principles.

## Features

- Create, delete, and manage daily or weekly habits
- Check off habits when you complete them
- Track streaks (consecutive periods of completing a habit)
- Analyse your habits with built-in analytics
- 5 predefined habits with 4 weeks of sample data included

## Requirements

- Python 3.7 or later
- No mandatory external dependencies (the app works with just the standard library)
- Optional: `questionary` for a nicer interactive menu experience

## Installation

1. Clone or download this repository:
   ```
   git clone https://github.com/Geff115/habit-tracking-app.git
   cd habit-tacking-app
   ```

2. (Optional) Install questionary for polished CLI prompts:
   ```
   pip install questionary or sudo apt install python3-questionary
   ```

## Usage

Run the application:
```
python main.py
```

On first run, the app loads 5 predefined habits with sample data so you have something to explore right away. You will see an interactive menu with these options:

1. **Create a new habit** - define a name, description, and choose daily or weekly
2. **Delete a habit** - remove a habit and all its completion data
3. **Check off a habit** - mark a habit as completed for the current period
4. **List all habits** - see every habit with its completion count and streaks
5. **Filter habits by periodicity** - view only daily or only weekly habits
6. **Longest streak (all habits)** - find which habit has the best overall streak
7. **Longest streak (single habit)** - check a specific habit's best streak
8. **Most struggled habits** - see which habits have been hardest to maintain
9. **Exit** - close the application

## Project Structure

```
habit_tracker/
    main.py          - CLI entry point and user interaction
    habit.py         - Habit class (OOP domain model)
    db.py            - Database class (SQLite persistence layer)
    analytics.py     - Analytics functions (functional programming)
    predefined.py    - Predefined habits and 4-week sample data
    test_habit.py    - Unit test suite
    habits.db        - SQLite database (created on first run)
```

## Running Tests

```
python -m unittest test_habit -v
```

Tests use an in-memory SQLite database, so they do not affect your real data.

## Predefined Habits

| Habit       | Periodicity | Description                           |
|-------------|-------------|---------------------------------------|
| Brush Teeth | Daily       | Brush teeth morning and evening       |
| Exercise    | Daily       | At least 30 min of physical activity  |
| Read        | Daily       | Read for at least 20 minutes          |
| Laundry     | Weekly      | Do the weekly laundry                 |
| Meal Prep   | Weekly      | Prepare meals for the week ahead      |

Each comes with 4 weeks of sample completion data, including intentional gaps for testing streak-break detection.

## License

This project is a part of my coursework for Object Oriented And Functional Programming With Python (OOFPP), that said, feel free to contribute or share your thoughts. See [LICENSE](./LICENSE) for details.
