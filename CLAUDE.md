# Bikeshare demand capstone

Daily Capital Bikeshare counts, 2011-2012. We forecast `cnt` (total daily
rides) from calendar, weather, and lagged-demand features.

## Commands
- `make test` - pytest; run this before claiming anything works
- `make all` - the three pipeline stages in order

## Confirm before completion
* Only after pasting the actual results of `make test` from this turn can you say "done", "fixed" or "works". If metrics changed, also paste the output of `make all`.
* Do not modify or skip a test, or relax its conditions, just to get it to pass, unless I ask you to.
* When adding a test, run it on the broken code first, make sure it fails, and post the failure result.
* Before saying a model or feature beats a baseline, run `/vs-baseline <model>` and quote its last line.

## Non-negotiable rules
- **Never** put `casual` or `registered` in a feature set:
  `casual + registered == cnt` exactly. `src/config.py` lists these and the
  other excluded columns (`cnt_2d_bfr`, raw time indexes) with the reason
  for each. Derive feature lists from `FORBIDDEN`; never hand-type them.
- **Never** split this data randomly. Use `src.train.temporal_split`.
  Train = 2011, valid = H1 2012, test = H2 2012. Never tune on test.
- Any new lag or rolling feature must be built on a gap-free calendar
  index (`src.features.reindex_to_calendar`) and must `.shift(1)` before
  it aggregates. Add a test for it in `tests/test_leakage.py`.
- Report the mean baseline **and** the persistence baseline (yesterday's
  count) alongside every model. A negative R^2 is a finding, not a bug
  to hide.

## Data and records
* Do not modify anything in `data/raw/`.
* Before using any new raw data column, classify it in `src/config.py`.
* For every methodological choice, add a dated line in `docs/DECISIONS.md` explaining the decision.
* Don't run `git commit`; I'll commit the changes myself.
* Do not edit `docs/SEEDED_FAULTS.md` or `docs/AUDIT.md`; I write those records myself.

## Style
- Standard library, pandas, scikit-learn only. No new dependencies
  without asking. Versions are pinned in `requirements.txt`.

## Gotchas
- The mirror in `DATA_URL` is missing 2011-03-10. It is NOT the UCI file:
  728 rows from 2011-01-03, not 731 from 2011-01-01.
- Ridership grew ~65% from 2011 to 2012, so tree models trained on 2011
  cannot extrapolate to 2012. That is the headline result, not an error.
