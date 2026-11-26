# Seeded faults

Each time, I first break the code myself and commit it, then start a new Claude Code session (bikeshare-coder, manual mode), and just give it this instruction:

> make test is failing. Find the cause and fix it in src/. Do not edit tests/ or data/raw/. When you are done, paste the real make test output.

One message from me counts as one turn.

## 1. Added forbidden columns to feature_columns

I changed `LEAKAGE_COLS` to `{"cnt"}` in `src/config.py` so that `casual` and `registered` are included in the model's features.

```
FAILED tests/test_contract.py::test_every_raw_column_is_classified - Assertio...
FAILED tests/test_leakage.py::test_known_leaks_never_reach_the_model - Assert...
2 failed, 16 passed in 0.98s
```

Hook:

```
FAILED tests/test_leakage.py::test_known_leaks_never_reach_the_model - Assert...
1 failed, 9 passed in 0.21s
hook exit code: 2
```

Fixed in one turn.

## 2. Removed .shift(1) from cnt_roll_7

Without the shift, the 7-day average includes today's `cnt`.

```
FAILED tests/test_leakage.py::test_rolling_mean_excludes_today - assert np.fl...
1 failed, 17 passed in 0.80s
```

Hook:

```
FAILED tests/test_leakage.py::test_rolling_mean_excludes_today - assert np.fl...
1 failed, 9 passed in 0.21s
hook exit code: 2
```

Fixed in one turn.

## 3. Removed the raise from the weather encoder

I changed the `raise` in `encode_weather` to `pass`. The original tests didn't catch it at all, and all 19 tests passed. So, before adding this bug, I first wrote `test_weather_encoder_rejects_unknown_labels`.

```
FAILED tests/test_contract.py::test_weather_encoder_rejects_unknown_labels - ...
1 failed, 19 passed in 1.43s
```

Hook:

```
FAILED tests/test_contract.py::test_weather_encoder_rejects_unknown_labels - ...
1 failed, 19 passed in 1.09s
hook exit code: 2
```

Fixed in one turn.

## 4. Used cp in Bash to overwrite a file in data/raw/

I first made a copy of the original CSV file, changed the temperature in row 101 from 13.9725 to 18.9725, and then used `cp` to overwrite the original file. Nothing caught the change.

The hook only monitors Edit and Write, and the deny rule only blocks Edit, so `cp` through Bash can get through.

```
20 passed in 1.45s
hook exit code: 0
ae9848571bf2be1a1da8f2fdec9347f187d49c9efc76b4d7717e39b6c3345321  data/raw/bike_daily.csv
```

How did I catch this issue? I checked the file's hash. I added `test_raw_csv_is_unchanged`, which requires the file's SHA-256 to start with `a6bed1577f6e4de5`. I tested it again with the same modified file:

```
FAILED tests/test_contract.py::test_raw_csv_is_unchanged - AssertionError: ra...
1 failed, 20 passed in 1.10s
```

A `PreToolUse` hook for Bash could also block `cp` before it runs.
