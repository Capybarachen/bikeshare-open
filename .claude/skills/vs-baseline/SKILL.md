---
name: vs-baseline
description: Compare one model's validation scores in reports/metrics.json against the mean and persistence baselines. Use when asked whether a model beats its baselines.
allowed-tools: Read
---

# Does `$ARGUMENTS` beat its baselines?

1. Read `reports/metrics.json`. If `$ARGUMENTS` is empty or is not a key in
   that file, list the model keys it does contain and stop.
2. From the `valid` block only, give R^2 and MAE for `$ARGUMENTS`,
   `baseline_mean` and `baseline_persistence`, copied exactly as stored.
   Also give `n_features`, so the reader knows which feature set produced
   these numbers.
3. Compare `$ARGUMENTS` with `baseline_persistence` using these rules, and
   nothing else:
   - R^2: higher is better. The model wins if its R^2 is larger.
   - MAE: lower is better. The model wins if its MAE is smaller.
   For each metric write "model <value> vs persistence <value>: wins" or
   "...: loses", plus the absolute gap. Do not subtract to decide the winner.
4. Do not read, quote or compare anything from the `test` block. Do not
   edit any file. Do not re-run the pipeline; if the user suspects the
   numbers are stale, tell them to run `make all` themselves.
5. End with exactly this line, filling in yes (model wins) or no:
   `$ARGUMENTS vs persistence (valid): R^2 <yes|no>, MAE <yes|no>`
