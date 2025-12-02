# test_project.py
import os
import json
import datetime
import tempfile
from main import add_habit, mark_done, load_habits, save_habits

def test_add_and_save_load(tmp_path):
    fname = tmp_path / "h.json"
    habits = {}
    add_habit(habits, "Read")
    assert "Read" in habits
    save_habits(habits, filename=str(fname))
    loaded = load_habits(filename=str(fname))
    assert "Read" in loaded

def test_mark_done_streak(tmp_path):
    fname = tmp_path / "h2.json"
    habits = {}
    add_habit(habits, "Code")
    # mark done on day 1
    day1 = "2025-01-01"
    mark_done(habits, "Code", today=day1)
    assert habits["Code"]["last_done"] == day1
    assert habits["Code"]["streak"] == 1
    # mark done on next day => streak increments
    day2 = "2025-01-02"
    mark_done(habits, "Code", today=day2)
    assert habits["Code"]["streak"] == 2

def test_mark_done_errors():
    habits = {}
    try:
        mark_done(habits, "Nonexistent")
        assert False, "Expected KeyError"
    except KeyError:
        pass
