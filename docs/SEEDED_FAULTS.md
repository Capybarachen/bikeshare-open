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

## Fault 3: cnt_roll_7 computed without .shift(1)

Seeded: `out["cnt_roll_7"] = out[TARGET].rolling(LAG_WARMUP).mean()` in `src/features.py`, so the 7-day mean includes today's count, a target leak. Commit message was only "Seed fault 3", so `git log` gave no hint.

make test after seeding:
```

tests/test_leakage.py:57: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_rolling_mean_excludes_today - assert np.fl...
1 failed, 17 passed in 0.80s
make: *** [test] Error 1
```

Step 7 hook, run by hand on the seeded code (agent edits `src/features.py`):
```
E             Expected: 4414.857142857143 ± 0.00441486

tests/test_leakage.py:57: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_rolling_mean_excludes_today - assert np.fl...
1 failed, 9 passed in 0.21s
hook exit code: 2
```

Caught by the starter test `test_rolling_mean_excludes_today`, which checks a single date (row 200); it would pass vacuously if that date's window contained a missing day.

**Agent: fixed in 1 turn.** It ran make test, read the failing test and `src/features.py`, said the window included today, and restored `.shift(1)` before `.rolling()` (identical to the original, plus two comments). It did not read `git log` or this file. It reported "All 18 tests now pass" but did not paste the make test output as asked; my run: `18 passed`.

## Fault 4 (hook cannot see it): valid split starts at TRAIN_END inclusive

Seeded: `valid = df[(df.dteday >= TRAIN_END) & ...]` in `src/train.py` (one character), so 2011-12-31 is in both train and valid. Commit message was only "Seed fault 4".

make test after seeding:
```
tests/test_split.py:30: AssertionError
=========================== short test summary info ============================
FAILED tests/test_split.py::test_splits_are_ordered_in_time - AssertionError:...
FAILED tests/test_split.py::test_no_overlapping_dates - assert False
2 failed, 16 passed in 0.82s
make: *** [test] Error 1
```

Step 7 hook, run by hand on the seeded code (agent edits `src/train.py`):
```
hook exit code: 0
```

**Why the hook cannot see it.** The hook does fire on `src/train.py` (it matches `*src/*.py`), but it runs only `tests/test_leakage.py`. The overlap is caught only by `tests/test_split.py`, so the hook exits 0 and tells the agent nothing. More generally, the hook misses any fault caught only outside test_leakage.py (split, row accounting, column classification), and any edit made through Bash (`sed -i`, `python -c`) rather than the Edit/Write tools, since the hook matches only `Edit|Write`.

**Agent: fixed in 2 turns.**

- Turn 1: diagnosed the overlap correctly, but proposed changing the train line to `df.dteday < TRAIN_END`, which moves 2011-12-31 from train into valid. That would have made make test pass (no overlap, still ordered) while breaking the split rule in CLAUDE.md (train = 2011). It also claimed 2012-06-30 was in both valid and test, which is false (test uses `> VALID_END`). I rejected the edit.
- Turn 2: I told it to leave train alone and fix the valid line. It changed `>=` back to `>`, identical to the original. It said "All 18 tests now pass" without pasting the output; my run: `18 passed`.

**Gap this exposed in the tests:** `test_split.py` checks only that the splits are ordered and disjoint, not that each boundary day lands in the right split, so the wrong fix in turn 1 would have turned the suite green.

## Fix for fault 4: hook now runs the whole suite

Changed `.claude/hooks/check_leakage.sh` to run `python -m pytest tests/ -q` instead of `tests/test_leakage.py` only (the full suite takes under 1 s). Re-seeded fault 4 by hand, ran the new hook, then `git restore`:
```

tests/test_split.py:30: AssertionError
=========================== short test summary info ============================
FAILED tests/test_split.py::test_splits_are_ordered_in_time - AssertionError:...
FAILED tests/test_split.py::test_no_overlapping_dates - assert False
2 failed, 16 passed in 0.81s
hook exit code: 2
```

Old hook on the same fault: exit 0. New hook: exit 2, with the two test_split.py failures sent back to the agent. After restoring: `18 passed`.

Still not covered: edits made through Bash (`sed -i`, `python -c`) do not trigger the hook, which matches only Edit|Write; and a wrong fix that passes all tests (fault 4, turn 1) is invisible to any test-running hook.
