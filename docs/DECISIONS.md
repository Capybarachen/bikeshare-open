# Decisions

One line per methodological decision: what you chose, why, and what it changed.
Agents append here via the `/new-feature` skill; you append here by hand.

- Exclude `casual`, `registered`: they sum to `cnt` exactly. Leaky model R^2 1.000 -> honest ridge 0.583.
- Exclude `cnt_2d_bfr`: a shipped 2-day lag we cannot test the alignment of. Build our own lags instead.
- Exclude `instant`, `yr`, `days_since_2011`: time indexes let a tree predict a flat constant past 2011 and a linear model extrapolate a trend we have no grounds for.
- Split 2011 / H1 2012 / H2 2012 by date. Test set touched once, after all feature work.
- Report mean and persistence baselines with every score. Persistence (test R^2 0.510, MAE 840) is within 0.07 R^2 of ridge and beats it on MAE; that caveat goes in the report.
- 2026-11-24: CLAUDE.md: kept starter rules verbatim; added "Confirm before completion" (3 rules) and "Data and records" (4 rules); cut lines derivable from code (single-stage make targets, module/path conventions, weather labels, Sandy note). Why: the agent must not claim done before verification, and every line must change agent behaviour.
- 2026-11-24: Step 2, verified by hand (not by the agent): 728 rows x 18 cols, 2011-01-03 to 2012-12-31, only 2011-03-10 missing; casual + registered == cnt on all 728 rows; mean cnt 3427 (2011) vs 5600 (2012), +63%. The agent (bikeshare-coder, plan mode) claimed 730 rows, 730 of 731 days, days_since_2011 counting from 2011-01-03, and cnt_2d_bfr as leakage; all four were wrong. Kept the starter exclusions unchanged.
- 2026-11-24: cnt_2d_bfr equals cnt from 2 calendar days earlier on 99.6% of rows (3 rows differ), so it is a real 2-day lag: unverified, not leakage. Keep it in UNVERIFIED_COLS and build our own lags.
