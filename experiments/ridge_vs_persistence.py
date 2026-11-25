"""Exercise 5: is ridge worth deploying over the persistence baseline?

Validation split only. Paired daily absolute errors, a moving-block bootstrap
(7-day blocks, since neighbouring days are correlated) for the MAE gap, the
share of days each model wins, and MAE by month.

Run: python -m experiments.ridge_vs_persistence
"""
import numpy as np
import pandas as pd
from sklearn.base import clone

from src.config import PROCESSED, TARGET
from src.features import feature_columns
from src.train import MODELS, temporal_split

BLOCK, N_BOOT, SEED = 7, 5000, 0


def block_bootstrap_mean(x, rng):
    n = len(x)
    starts = rng.integers(0, n - BLOCK + 1, size=(N_BOOT, int(np.ceil(n / BLOCK))))
    idx = (starts[:, :, None] + np.arange(BLOCK)).reshape(N_BOOT, -1)[:, :n]
    return x[idx].mean(axis=1)


def main():
    df = pd.read_parquet(PROCESSED)
    cols = feature_columns(df)
    train, valid, _ = temporal_split(df)  # test split discarded here
    y = valid[TARGET].to_numpy(float)

    err = {"persistence": np.abs(y - valid.cnt_lag_1.to_numpy(float))}
    for name in ["ridge", "hgb_ratio"]:
        m = clone(MODELS[name]).fit(train[cols], train[TARGET])
        err[name] = np.abs(y - m.predict(valid[cols]))

    rng = np.random.default_rng(SEED)
    print(f"validation days: {len(y)}\n")
    for name in ["ridge", "hgb_ratio"]:
        gain = err["persistence"] - err[name]   # > 0 means the model is better that day
        lo, hi = np.percentile(block_bootstrap_mean(gain, rng), [2.5, 97.5])
        print(f"{name} vs persistence")
        print(f"  MAE {err[name].mean():.1f} vs {err['persistence'].mean():.1f}; "
              f"mean daily gain {gain.mean():.1f} rides, 95% block-bootstrap CI [{lo:.1f}, {hi:.1f}]")
        print(f"  model closer on {np.mean(gain > 0):.0%} of days; "
              f"worst single-day loss {-gain.min():.0f} rides\n")

    by_month = pd.DataFrame(err).assign(month=valid.dteday.dt.strftime("%Y-%m").to_numpy())
    print("MAE by month (validation):")
    print(by_month.groupby("month").mean().round(0).to_string())


if __name__ == "__main__":
    main()
