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
