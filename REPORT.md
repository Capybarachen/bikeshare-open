# Bikeshare demand: Methodology report

Repo: https://github.com/Capybarachen/bikeshare-open

The numbers below come from `reports/metrics.json` or from the code in `experiments/`. D-n represents the nth line of `docs/DECISIONS.md`.

## Results

I split the data by date: 2011 was the training set (348 days), the first half of 2012 was the validation set (182 days), and the second half was the test set (184 days). All the choices here are based on the validation set, and I only looked at the test set once, at the end (D-25).

"Before" means the original 14 features. "After" adds my `temp_x_workday` feature, for a total of 15.

| Model | Features | Valid R² | Valid MAE | Test R² | Test MAE |
|---|---|---|---|---|---|
| baseline_mean | before | −0.9318 | 2002.2 | −2.1441 | 2847.7 |
| baseline_mean | after | −0.9318 | 2002.2 | −2.1441 | 2847.7 |
| baseline_persistence | before | 0.4507 | 900.6 | 0.5099 | 840.1 |
| baseline_persistence | after | 0.4507 | 900.6 | 0.5099 | 840.1 |
| ridge | before | 0.6475 | 832.9 | 0.5833 | 947.1 |
| ridge | after | 0.6611 | 809.2 | 0.5869 | 947.0 |
| hgb | before | 0.2185 | 1296.6 | −0.4975 | 1972.6 |
| hgb | after | 0.2011 | 1318.2 | −0.5822 | 2031.5 |
| hgb_ratio (Exercise 4) | after | 0.7396 | 701.9 | 0.6304 | 837.5 |

The two baselines don't use these features, so the results before and after adding new features are the same.

The first feature I created, `temp_sq`, reduced ridge's R² from 0.6475 to 0.5811, so I deleted it (D-16). `temp_x_workday` increased ridge's R² by 0.014, so I kept it (D-17). The agent reported the wrong result both times.

Now, running `make test` will run 21 tests. I have added the four faults named in the assignment (`docs/SEEDED_FAULTS.md`):

| Fault | Caught by | Hook | Agent turns |
|---|---|---|---|
| Forbidden column added to `feature_columns` | 2 tests | exit 2 | 1 |
| `.shift(1)` deleted from `cnt_roll_7` | starter rolling-mean test | exit 2 | 1 |
| Weather encoder `raise` removed | my new test (D-26) | exit 2 | 1 |
| `cp` into `data/raw/` from Bash | my new hash test (D-27) | doesn't fire | — |

Before I added the new tests, the original tests did not catch the last two faults. I also changed the hook to run all the tests in `tests/` instead of only running `test_leakage.py` (D-21).

## Headline finding

I found that on test data that the models had never seen before, no model clearly outperformed "just using yesterday's count." The persistence test MAE is 840.1, while the ridge model performs worse with 947.0. hgb_ratio has the best test R² of 0.6304, but its MAE is 837.5, which is only 2.6 rides better than persistence. This suggests that it avoids more large errors, but its average daily error is not much better.

This reason may be related to the growth in the rental volume. The average daily rental volume from 2011 to 2012 increased from 3,427 to 5,600, an increase of approximately 63% (D-12). Each model was trained only on data from 2011, so the gap between the training data and later dates may make prediction harder. Persistence does not need to learn from the training data, so it can't go out of date.

Another problem I discovered is related to the agent because it often fails to check its work and just says that the task is completed or the result is correct. It gave the wrong number of rows and said "Done." without running `make test`.

It even misread both results of Exercise 1 (D-19), and another point is that it once tried to modify my record after fault 2, writing the correction that took two rounds as one round (D-20). So the rules of `CLAUDE.md` did not prevent these problems; the tests, the hook, and my own checks helped catch them.

## Exercise 4: target transformation

When directly predicting `cnt`, 39% of validation days had counts outside the training range. hgb struggled to predict counts above the training range, so hgb has only an R² of 0.2011 in the validation. I only used the training set and validation set to try six different prediction targets in `experiments/target_transform.py`.

| hgb target | Valid days outside train range | Valid R² | Valid MAE |
|---|---|---|---|
| `cnt` | 39.0% | 0.2011 | 1318.2 |
| `log1p(cnt)` | 39.0% | 0.1756 | 1336.1 |
| `cnt − cnt_lag_1` | 2.2% | 0.6064 | 831.8 |
| `log(cnt / cnt_roll_7)` | 0.0% | 0.7070 | 740.9 |
| `cnt − cnt_roll_7` | 1.6% | 0.7186 | 726.2 |
| `cnt / cnt_roll_7` | 0.0% | 0.7396 | 701.9 |

From the results, I found that the log transformation did not help, and 39% of validation days were still outside the training range. This suggests the problem was more about extrapolation than skew. By changing the prediction to "today's count compared to the past 7 days," the overall impact of growth could be reduced, and the performance of the tree model also improved.

I chose `cnt / cnt_roll_7` and added hgb_ratio, writing the test first and then implementing it (D-23). Its test R² (0.6304) is lower than the validation (0.7396). This is not surprising, because I chose the best-performing target out of six on validation, and the test set included Hurricane Sandy on 2012-10-29, when there were only 22 rides. This transformation made hgb's performance more competitive, but it did not significantly outperform persistence.

## Exercise 5: ridge vs persistence

I think ridge is not worth deploying. `experiments/ridge_vs_persistence.py` compares the daily errors of both methods during validation. Since nearby days may be related, I used a 7-day block bootstrap (D-24).

| Validation, 182 days | ridge | hgb_ratio |
|---|---|---|
| MAE (persistence 900.6) | 809.2 | 701.9 |
| Average daily gain over persistence | 91.4 | 198.7 |
| 95% CI for the gain | [−35.3, 220.9] | [58.3, 361.1] |
| Days better than persistence | 49% | 54% |

The improvement in ridge could be zero, because the 95% CI [−35.3, 220.9] includes 0, and ridge was better than persistence on less than half of the days. It also lost to persistence in May and June, which are the two months closest to the actual time the model would be used.

The test set points the same way: the MAE for ridge is 947.0, and persistence's is 840.1. Persistence does not require any training or maintenance. If I had to deploy a model, I would choose hgb_ratio; but its test MAE is almost the same as persistence's, so I will continue to use persistence at the moment, while observing the performance of hgb_ratio in the background.
