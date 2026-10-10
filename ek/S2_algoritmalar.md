# S2 — Algorithms and fixed hyperparameters

Supplementary material. Compiled from `pv10/models.py` and `pv10/config.py`.
No value in this file was produced for it.

---

## 1. The eleven algorithms

All hyperparameters are **fixed in advance** and are never tuned against
validation or test results. This is a deliberate methodological choice: the
study measures how much reported performance moves under common evaluation
errors, and tuning towards the test set would make that measurement
meaningless. `SEED = 42` throughout.

| # | Name | Estimator | Fixed hyperparameters |
|---|---|---|---|
| 1 | Linear Regression | `LinearRegression` | defaults |
| 2 | Polynomial Ridge | `PolynomialFeatures` → `Ridge` | `degree=2`, `include_bias=False`; `alpha=10.0`, `random_state=SEED` |
| 3 | SGD Regression | `SGDRegressor` | `max_iter=2000`, `tol=1e-4`, `random_state=SEED` |
| 4 | K-Nearest Neighbours | `KNeighborsRegressor` | `n_neighbors=15`, `weights="distance"`, `n_jobs=-1` |
| 5 | Support Vector Regression | `SVR` | `kernel="rbf"`, `C=30.0`, `epsilon=5.0` |
| 6 | Decision Tree | `DecisionTreeRegressor` | `max_depth=18`, `random_state=SEED` |
| 7 | Random Forest | `RandomForestRegressor` | `n_estimators=400`, `min_samples_leaf=2`, `random_state=SEED`, `n_jobs=-1` |
| 8 | Extra Trees | `ExtraTreesRegressor` | `n_estimators=400`, `min_samples_leaf=2`, `random_state=SEED`, `n_jobs=-1` |
| 9 | Gradient Boosting | `GradientBoostingRegressor` | `n_estimators=300`, `learning_rate=0.04`, `max_depth=3`, `random_state=SEED` |
| 10 | Hist Gradient Boosting | `HistGradientBoostingRegressor` | `max_iter=400`, `learning_rate=0.06`, `random_state=SEED` |
| 11 | Neural Network | `MLPRegressor` | `hidden_layer_sizes=(96, 48)`, `early_stopping=True`, `max_iter=500`, `random_state=SEED` |

---

## 2. Preprocessing

Every estimator sits in the same two-step pipeline:

```
SimpleImputer(strategy="median")  →  StandardScaler()  →  estimator
```

Tree-based models do not need scaling, but a single shared preprocessing
path is used anyway so that variants remain comparable: if preprocessing
differed by model family, a difference between variants could not be
attributed to the variant.

**The pipeline is the leakage boundary.** Under the *global scaling*
variant the pipeline is built **without** these two steps
(`onisleme=False`), because imputation and scaling have already been fitted
on the full data set outside the pipeline. That is the deliberate bad
practice the variant exists to measure — it is the only place where the
pipeline shape changes.

---

## 3. Model subsets and why they exist

Running eleven algorithms in every cell of every grid is not affordable:
the ablation grid alone is 6 variants × 7 test years × *N* models, and the
saturation grid is 255 cells. Two subsets are declared as constants, before
any run.

| Subset | Constant | Members | Used for |
|---|---|---|---|
| **Fast 3** | `models.HIZLI_ALTKUME` | Linear Regression, Polynomial Ridge, Hist Gradient Boosting | smoke test, Phase 3 ranking, Phase 4 main grid, all Phase 2 uncertainty measurement |
| Ablation subset | `models.ABLASYON_ALTKUMESI` | the fast 3 plus Random Forest, Neural Network | Phase 2 leakage ablation |
| Wide run | all except `config.GENIS_KOSU_HARIC` | 10 of 11 | Phase 4 wide run, `K = all` only |

### Why the fast 3

Measured cost on 350 000–525 000 rows × 29 features:

| Class | Models | Cost |
|---|---|---|
| seconds | Linear Regression, Polynomial Ridge, Hist Gradient Boosting | default choice |
| minutes, high RAM | Random Forest, Extra Trees (400 trees), MLP | affordable only at `K = all` |
| infeasible | Support Vector Regression | O(n²) kernel |

The selection criterion is **computational cost, fixed before the runs**,
not observed accuracy. Stating the criterion is required precisely because
cost is a legitimate reason and a post-hoc accuracy-based selection would
not be.

### Why SVR is excluded from the wide run

`config.GENIS_KOSU_HARIC = ("Support Vector Regression",)`.

SVR's RBF kernel is O(n²). At the wide run's training sizes (260 000–470 000
rows) it is not merely slow but practically impossible; it is the one model
the computational-reality note marks "do not attempt". The wide run
therefore covers **10 of 11** algorithms at `K = all`.

SVR *is* present in the earlier single-year study's eleven-algorithm
comparison, where training sets were an order of magnitude smaller.

---

## 4. Nondeterminism — measured, not assumed

Random Forest and Extra Trees do **not** reproduce bit-identical predictions
across runs, even with `random_state=SEED`. The cause is within-process
parallel reduction (tree aggregation order), not the storage layer.

The measurement used the same cell (sliding, `K = all`, 2020) repeated at
two levels — A: two consecutive runs in one process; B: two separate
processes. **Level A settled it:** all four Random Forest runs and all four
Extra Trees runs produced different prediction hashes. The control witness
was Neural Network, which returned the *same* hash
(`52016056fdc69ba8…`) in all four runs across two measurements on separate
days — so the apparatus does not manufacture differences.

Consequences, all measured:

- The deviation is always present in the prediction vector but reaches the
  metric only sometimes: all four Random Forest runs gave RMSE
  138.710 181 301 924 96 while the grid's stored value for that cell was
  1 ULP lower.
- Across 40 re-run cells, 510 of 520 logged fields matched exactly; the 10
  that moved were 1–2 ULP (relative ≈ 2 × 10⁻¹⁶) and only in these two
  models. `egitim_n`, `n`, `isinma`, `egitim_basla` and `RMSE_persistence`
  matched exactly in every cell.
- **No reported number is affected.** The fast 3 are unaffected, and all
  Phase 2/3/4 headline numbers come from them.

Diagnostic code lives in `arac/`, is never called from the main flow, and
produces no manuscript number.

---

## 5. Thread pinning

`HistGradientBoostingRegressor` uses OpenMP. If the thread count changes,
the summation order changes and bit-level reproducibility is lost.
`OMP_NUM_THREADS = OPENBLAS_NUM_THREADS = MKL_NUM_THREADS = 8` is pinned at
the start of every run (`config.OMP_THREAD_SAYISI = 8`).

## 6. Environment

| Package | Version |
|---|---|
| numpy | 2.5.1 |
| pandas | 3.0.5 |
| scikit-learn | 1.9.0 |
| scipy | 1.18.0 |
| pyarrow | 22.0.0 |

pyarrow is pinned at 22.0.0 rather than 25.0.0: on 3 August 2026 Windows
Smart App Control began blocking 25.0.0's `arrow.dll` (CodeIntegrity
3077/3033), so no run could start. The downgrade used `--only-binary=:all:`
with no source build. The Smart App Control setting itself was **not**
changed, as that is irreversible. The data hash did not change, the
invariant gate passed 18/18 under both versions, and invariants 1–2
reproduced their ablation references to the last digit. The main grid, the
wide run and the 2022 run were produced under 25.0.0; later runs under
22.0.0.
