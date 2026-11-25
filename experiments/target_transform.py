"""Exercise 4: which target transformation lets gradient boosting compete?

Uses the train and validation splits only. The test split is discarded on
the first line that touches it and is never scored here.

Run: python -m experiments.target_transform
"""
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import mean_absolute_error, r2_score

from src.config import PROCESSED, TARGET
from src.features import feature_columns
from src.train import MODELS, temporal_split

# name -> (forward: rows -> transformed target, inverse: (rows, prediction) -> cnt)
TRANSFORMS = {
    "none":           (lambda d: d[TARGET],                          lambda d, p: p),
    "log":            (lambda d: np.log1p(d[TARGET]),                lambda d, p: np.expm1(p)),
    "diff_lag1":      (lambda d: d[TARGET] - d.cnt_lag_1,            lambda d, p: p + d.cnt_lag_1),
    "diff_roll7":     (lambda d: d[TARGET] - d.cnt_roll_7,           lambda d, p: p + d.cnt_roll_7),
    "ratio_roll7":    (lambda d: d[TARGET] / d.cnt_roll_7,           lambda d, p: p * d.cnt_roll_7),
    "logratio_roll7": (lambda d: np.log(d[TARGET] / d.cnt_roll_7),   lambda d, p: np.exp(p) * d.cnt_roll_7),
}


def main():
    df = pd.read_parquet(PROCESSED)
    cols = feature_columns(df)
    train, valid, _ = temporal_split(df)  # test split discarded here

    rows = []
    for tname, (fwd, inv) in TRANSFORMS.items():
        y_train, y_valid = fwd(train), fwd(valid)
        outside = ((y_valid < y_train.min()) | (y_valid > y_train.max())).mean()
        for mname in ["ridge", "hgb"]:
            model = clone(MODELS[mname]).fit(train[cols], y_train)
            pred = inv(valid, model.predict(valid[cols]))
            rows.append({
                "model": mname,
                "target": tname,
                "valid_r2": round(r2_score(valid[TARGET], pred), 4),
                "valid_mae": round(mean_absolute_error(valid[TARGET], pred), 1),
                "valid_target_outside_train_range": round(float(outside), 3),
            })

    pers = valid.cnt_lag_1
    print(f"baseline_persistence  valid_r2={r2_score(valid[TARGET], pers):.4f}  "
          f"valid_mae={mean_absolute_error(valid[TARGET], pers):.1f}")
    out = pd.DataFrame(rows).sort_values(["model", "valid_r2"], ascending=[True, False])
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
