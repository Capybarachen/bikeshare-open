# Audit

Repository audited: https://github.com/xiaocheng05/bikeshare-open (DSC 180A partner xiaocheng)

Run in a fresh Claude Code session in a separate clone (~/dsc180/audit-c), model bikeshare-coder (qwen3.5:9b). I asked the leakage-auditor subagent to audit all changes in `src` and `tests` since the first commit, using:
`git diff $(git rev-list --max-parents=0 HEAD) HEAD -- src tests`
I waited for it to finish and copied the full report exactly as it is.

## Auditor output (verbatim)

```text
Five-Check Audit Results

1. Target leakage: ✓ PASS
- FORBIDDEN = LEAKAGE_COLS | TIME_INDEX_COLS | UNVERIFIED_COLS explicitly excludes casual, registered, and cnt
- Test test_no_feature_restates_the_target verifies no feature can be an exact affine copy of cnt via regression
- Arithmetic check casual + registered == cnt confirmed in test_leakage_identity_holds

2. Temporal ordering: ✓ PASS
- temporal_split() uses date-based split (train=2011, valid=H1 2012, test=H2 2012), not random
- .shift(1) and .shift(LAG_WARMUP) occur before aggregation on line 80-82 of features.py
- Scalers/encoders fit only on train data (see train.py line 78: model.fit(train[cols], train[TARGET]))

3. Calendar gaps: ✓ PASS
- reindex_to_calendar() fills missing days with date_range before shifting (line 54 of features.py)
- Test test_calendar_is_complete_before_lagging confirms all inter-row differences are exactly 1 day
- Tests verify lag correctness on named dates (2011-01-22, etc.)

4. Silent row loss: ✓ PASS
- Row count accounting is explicit: lost rows = LAG_WARMUP + LAG_WARMUP × missing_days (line 43 of test_contract.py)
- No .dropna() without bound; only after shifts and rolling means which naturally produce NaN

5. Unreported baseline: ✓ PASS
- Both baseline_mean AND baseline_persistence are reported alongside every model in reports/metrics.json
- See the output: each model has valid and test metrics while both baselines are also present for comparison

---

Conclusion

All five checks pass. The code correctly forbids target leakage, uses temporal splits only, handles calendar gaps, bounds row loss, and reports both baseline methods alongside all models.
```

## My verdict

None of the auditor's findings change any numbers; I agree with all five PASS results. I checked that in lines 80–82 of `features.py`, the code shifts the data before creating the lags and rolling mean; in line 78 of `train.py`, the model is fit using only the training data; and in line 43 of `test_contract.py`, there is indeed a limit on how many rows can be dropped. However, I noticed that the auditor got one thing wrong. It says that the lags are checked using specific dates, for example 2011-01-22, but this date is only used in the temp_sq test. The lag test actually checks every date, and more than 600 dates need to pass for the test to succeed. So in reality, it checks more comprehensively than the auditor claims. But this error does not affect the results. I also ran make test in my clone of the repo, and the result was 22 passed.
