"""Guard rails on the ingest contract and the trained model's behaviour."""
import pandas as pd
import pytest
from sklearn.base import clone
from sklearn.metrics import r2_score

from src.config import CLASSIFIED_COLS, LAG_WARMUP, TARGET
from src.features import build_features, feature_columns, reindex_to_calendar
from src.ingest import load_raw
from src.train import MODELS, temporal_split


@pytest.fixture(scope="module")
def raw():
    return load_raw().sort_values("dteday").reset_index(drop=True)


@pytest.fixture(scope="module")
def feats(raw):
    return build_features(raw)


def test_calendar_is_complete_before_lagging(raw):
    """The reindexed frame must have no gaps, or the lags are wrong."""
    grid = reindex_to_calendar(raw)
    assert set(grid.dteday.diff().dropna().dt.days.unique()) == {1}


def test_only_expected_rows_are_dropped(raw, feats):
    """Rows may only vanish for the lag warm-up or downstream of a genuinely
    absent day -- never because an encoder produced a silent NaN.

    Accounting: the first LAG_WARMUP days have no complete history. Each
    absent calendar day m costs the LAG_WARMUP rows after it (cnt_lag_1 is
    NaN on m+1, cnt_roll_7 is NaN on m+1..m+7, cnt_lag_7 on m+7; their
    union is 7 rows). Day m itself was never in `raw`, so it is not a loss.
    The bound is exact for the current feature set; add a longer lag and
    LAG_WARMUP in src/config.py must grow with it.
    """
    full = pd.date_range(raw.dteday.min(), raw.dteday.max(), freq="D")
    missing_days = len(full) - len(raw)
    allowed_loss = LAG_WARMUP + LAG_WARMUP * missing_days
    lost = len(raw) - len(feats)
    assert lost <= allowed_loss, f"lost {lost} rows; expected at most {allowed_loss}"


def test_beats_the_mean_baseline(feats):
    """A model that cannot beat predicting the training mean is not a result."""
    cols = feature_columns(feats)
    train, valid, _ = temporal_split(feats)
    ridge = MODELS["ridge"]
    ridge.fit(train[cols], train[TARGET])
    assert r2_score(valid[TARGET], ridge.predict(valid[cols])) > 0.4


def test_persistence_baseline_is_reported():
    """The baseline that matters for a lag-driven model is 'yesterday again'.
    It must be in the comparison, whatever its score."""
    assert "baseline_persistence" in MODELS


def test_every_raw_column_is_classified(raw):
    """A new or renamed column in the raw CSV must be classified in
    src/config.py before it can silently reach (or miss) the model."""
    cols = set(raw.columns)
    unclassified = cols - CLASSIFIED_COLS
    assert not unclassified, f"unclassified raw columns: {sorted(unclassified)}"
    stale = CLASSIFIED_COLS - cols
    assert not stale, f"classified columns missing from the raw CSV: {sorted(stale)}"


def test_hgb_ratio_beats_persistence_on_valid(feats):
    """hgb_ratio predicts cnt / cnt_roll_7 and multiplies back. If the
    multiply-back is lost, predictions are ratios near 1 and this fails."""
    cols = feature_columns(feats)
    train, valid, _ = temporal_split(feats)
    model = clone(MODELS["hgb_ratio"]).fit(train[cols], train[TARGET])
    r2 = r2_score(valid[TARGET], model.predict(valid[cols]))
    assert r2 > r2_score(valid[TARGET], valid.cnt_lag_1), f"hgb_ratio valid R^2 {r2:.4f}"


def test_weather_encoder_rejects_unknown_labels():
    """An unknown weather label must raise, not turn into NaN and get dropped."""
    from src.features import encode_weather
    with pytest.raises(ValueError):
        encode_weather(pd.Series(["GOOD", "FOGGY"]))


def test_raw_csv_is_unchanged():
    """Catches edits to data/raw/ that bypass the hook, e.g. a cp from Bash."""
    import hashlib
    from src.config import RAW
    digest = hashlib.sha256(RAW.read_bytes()).hexdigest()
    assert digest.startswith("a6bed1577f6e4de5"), f"raw CSV changed: sha256 {digest[:16]}"
