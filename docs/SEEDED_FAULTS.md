# Seeded faults

Each fault was committed, then a fresh Claude Code session (bikeshare-coder, manual mode) got one message: "make test is failing. Find the cause and fix it in src/. Do not edit tests/ or data/raw/. When you are done, paste the real make test output." A turn is one message from me.

## 1. A forbidden column added to feature_columns

Change: `LEAKAGE_COLS = {"cnt"}` in `src/config.py`, so `casual` and `registered` get into `feature_columns`.

Tests:
```
tests/test_leakage.py:76: AssertionError
=========================== short test summary info ============================
FAILED tests/test_contract.py::test_every_raw_column_is_classified - Assertio...
FAILED tests/test_leakage.py::test_known_leaks_never_reach_the_model - Assert...
2 failed, 16 passed in 0.98s
make: *** [test] Error 1
```
Hook:
```
E       assert not {'casual', 'registered'}

tests/test_leakage.py:76: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_known_leaks_never_reach_the_model - Assert...
1 failed, 9 passed in 0.21s
hook exit code: 2
```

Turns to fix: 1.

## 2. The .shift(1) deleted from cnt_roll_7

Change: `out["cnt_roll_7"] = out[TARGET].rolling(LAG_WARMUP).mean()` in `src/features.py`, so the 7-day mean includes today.

Tests:
```

tests/test_leakage.py:57: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_rolling_mean_excludes_today - assert np.fl...
1 failed, 17 passed in 0.80s
make: *** [test] Error 1
```
Hook:
```
E             Expected: 4414.857142857143 ± 0.00441486

tests/test_leakage.py:57: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_rolling_mean_excludes_today - assert np.fl...
1 failed, 9 passed in 0.21s
hook exit code: 2
```

Turns to fix: 1.

## 3. The weather encoder raise removed

Change: `raise ValueError(...)` replaced by `pass` in `encode_weather`. No starter test caught this (all 19 passed), so I added `test_weather_encoder_rejects_unknown_labels` first.

Tests:
```

tests/test_contract.py:85: Failed
=========================== short test summary info ============================
FAILED tests/test_contract.py::test_weather_encoder_rejects_unknown_labels - ...
1 failed, 19 passed in 1.43s
make: *** [test] Error 1
```
Hook:
```
E       Failed: DID NOT RAISE ValueError

tests/test_contract.py:85: Failed
=========================== short test summary info ============================
FAILED tests/test_contract.py::test_weather_encoder_rejects_unknown_labels - ...
1 failed, 19 passed in 1.09s
hook exit code: 2
```

Turns to fix: 1.

## 4. A cp into data/raw/ from Bash (the hook cannot see it)

What happened: I copied a version of `bike_daily.csv` with one temperature changed (row 101, 13.9725 -> 18.9725) over the raw file with `cp`. The hook only runs on Edit and Write, so it never fired, and the deny rule on `data/raw/` only covers the Edit tool. All tests still passed.

```
....................                                                     [100%]
20 passed in 1.45s
hook exit code: 0
ae9848571bf2be1a1da8f2fdec9347f187d49c9efc76b4d7717e39b6c3345321  data/raw/bike_daily.csv
```

What would catch it: a hash check on the raw file. I added `test_raw_csv_is_unchanged` (the sha256 must start with `a6bed1577f6e4de5`). With the copied file:
```
FAILED tests/test_contract.py::test_raw_csv_is_unchanged - AssertionError: ra...
1 failed, 20 passed in 1.10s
make: *** [test] Error 1
```
A `PreToolUse` hook on Bash that blocks writes to `data/raw/` would stop it before it happens.

## Extra faults

- Removed `reindex_to_calendar`: caught by `test_no_lag_window_crosses_a_missing_day`, hook exit 2, fixed in 2 turns.
- Valid split started at `>= TRAIN_END`: caught only by `test_split.py`. The starter hook ran only `test_leakage.py` and missed it (exit 0), so I changed the hook to run all of `tests/` (now exit 2). Fixed in 2 turns.
