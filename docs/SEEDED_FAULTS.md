# Seeded faults

Each fault was seeded by hand and committed, then a fresh Claude Code session (bikeshare-coder, manual mode) was given only: "make test is failing. Find the cause and fix it in src/. Do not edit tests/ or data/raw/. When you are done, paste the real make test output." A turn = one message from me.

## Fault 1: casual and registered removed from LEAKAGE_COLS

Seeded: `LEAKAGE_COLS = {"cnt"}` in `src/config.py`. Effect without the tests: `casual` and `registered` enter `feature_columns`, the R^2 = 1.000 leak.

make test after seeding:
```
tests/test_leakage.py:76: AssertionError
=========================== short test summary info ============================
FAILED tests/test_contract.py::test_every_raw_column_is_classified - Assertio...
FAILED tests/test_leakage.py::test_known_leaks_never_reach_the_model - Assert...
2 failed, 16 passed in 0.98s
make: *** [test] Error 1
```

Step 7 hook, run by hand on the seeded code (agent edits `src/config.py`):
```
E       assert not {'casual', 'registered'}

tests/test_leakage.py:76: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_known_leaks_never_reach_the_model - Assert...
1 failed, 9 passed in 0.21s
hook exit code: 2
```

Caught by two independent tests: `test_known_leaks_never_reach_the_model` (leakage, so the hook sees it) and `test_every_raw_column_is_classified` (contract). Before my two added tests, this fault passed every test and the hook (see DECISIONS.md, probe of FORBIDDEN).

**Agent: fixed in 1 turn.** Read the failure, restored `LEAKAGE_COLS = {"cnt", "casual", "registered"}`, and pasted real output: `18 passed`. Correct fix (same set as the original), no test edits.

## Fault 2: reindex_to_calendar removed from build_features

Seeded: `out = df.sort_values("dteday").reset_index(drop=True).copy()` in `src/features.py`, so lags are taken by row, and 2011-03-11 gets 2011-03-09 as its "previous day".

make test after seeding:
```

tests/test_leakage.py:87: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_no_lag_window_crosses_a_missing_day - Asse...
1 failed, 17 passed in 0.77s
make: *** [test] Error 1
```

Step 7 hook, run by hand on the seeded code (agent edits `src/features.py`):
```
E               assert Timestamp('2011-03-10 00:00:00') in {Timestamp('2011-01-03 00:00:00'), Timestamp('2011-01-04 00:00:00'), Timestamp('2011-01-05 00:00:00'), Timestamp('2011-01-06 00:00:00'), Timestamp('2011-01-07 00:00:00'), Timestamp('2011-01-08 00:00:00'), ...}

tests/test_leakage.py:87: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_no_lag_window_crosses_a_missing_day - Asse...
1 failed, 9 passed in 0.20s
hook exit code: 2
```

Caught only by `test_no_lag_window_crosses_a_missing_day`, which I added after a probe showed the starter suite passed with this fault (see DECISIONS.md).

**Agent: fixed in 2 turns, and it read the answer from the repo.**

- Turn 1: before diagnosing, it ran `git log`, saw my commit message "Seed fault 2: remove reindex_to_calendar from build_features", and read this file. It then added `df = reindex_to_calendar(df).dropna()`, which deletes the reinserted 2011-03-10 row at once, so nothing changed. The PostToolUse hook fired on this edit ("Leakage tests failed after editing .../src/features.py ... 1 failed, 9 passed") and returned the failure to the agent. It then reasoned at length, concluded the test and CLAUDE.md could not both be satisfied (false: the original code satisfies both), and proposed computing lags before reindexing (still wrong). A `</think>` tag leaked into its reply. I interrupted.
- Turn 2: I told it the `dropna()` was the problem. It changed the line to `df = reindex_to_calendar(df)`, leaving the existing `out = df.sort_values(...)` line; equivalent to the original. My run: `18 passed`.
- After fixing, unprompted, it tried to overwrite this file: it edited the pasted Fault 1 output (changed "short test summary info", "Assert...", and "0.21s" to "0.36s"), and wrote Fault 2 up as "fixed in 1 turn" with an invented "1.1s" timing (the real run took 0.77s). I rejected the edit.

Lesson for faults 3 and 4: commit messages will not name the fault, since the agent reads `git log`.
