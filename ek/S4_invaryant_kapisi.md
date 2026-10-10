# S4 — The invariant gate: specification and results

Supplementary material. Specification from `pv10/dogrulama.py`; results from
`faz-notlari/faz-4.md`. No number in this file was produced for it.

---

## 1. What the gate is for

The hardest question a leakage study faces is: *how do you know the setup
that measures leakage has not leaked itself?* The answer cannot be the
experiment's own output. It has to be a separate test of the setup's
correctness, run **before** the main grid and without looking at results.

Two kinds of validation exist in this repository and they are deliberately
separate:

| | Validates | Where |
|---|---|---|
| `pvgis_pipeline.py: dogrula_*` | the **data** — year range, row counts, gaps | pipeline |
| `pv10/dogrulama.py` | the **experimental construction** — window arithmetic, warm-up boundary, sampling code path, backward compatibility | gate |

**The main grid does not run until the gate passes.**

Five invariants, **18 individual checks**. Expected values come from
`sonuclar/ablasyon.csv` and from hand-done calendar arithmetic — never
derived from the code under test.

## 2. Two design rules that make the gate non-trivial

**The invariant calls the production function.** Invariants that measure
splitting call `egitim_test_bolme` and `hucre_kos` directly; they never
carry their own copy of the logic. If the split logic is copied into the
test, the test becomes a tautology: as long as the copy is right, the gate
goes green even when production is wrong.

**An invariant must have a negative control.** If it cannot catch a
deliberately wrong reference, it is inert and the gate must go red. This was
not hypothetical — invariant 5 originally failed this standard, and the
failure is recorded in [S6](S6_on_kayit_sapmalari.md).

---

## 3. Specification

### Invariant 1 — Window equivalence (2019)

In 2019 the past is exactly five years, so `K = 5` and `K = all` must see
identical data.

Three-way check: pairwise equality is not enough, because a shift in window
arithmetic could move both cells together — the `ablasyon.csv` reference is
therefore mandatory as a third leg.

### Invariant 2 — Phase 2 backward compatibility (2023, `K = all`)

Phase 4's `K = all` cell is the same construction as Phase 2's expanding
window. If this fails, the new code path invalidates the Phase 2 and Phase 3
results.

### Invariant 3 — Warm-up boundary (2023)

Is warm-up consumed at the start of the **window** or at the start of the
**data set**? `K = all` cells cannot tell the difference — they all begin in
2014. Short windows can: if the boundary leaks, `egitim_n` comes out as a
whole year (52 560 / 105 120); if warm-up sits inside the window, it is
short by 191 rows per site.

If this leaks, a model described as "trained on 1 year" carries the previous
years' rolling statistics and the saturation curve flattens artificially.

### Invariant 4 — Sampling code path (2019, `K = 5`, degenerate cell)

In 2019 the pool is exactly five years, so `K = 5` subsampling must draw the
**entire** pool. All three seeds must equal each other and equal sliding
`K = 5` @ 2019 exactly. This is the only direct correctness test of the
sampling path, and it also pins that the draw is without replacement.

### Invariant 5 — Order of computation (2023, `K = 2`, seed 11)

A **non-degenerate** cell. Are the features of the rows production selected
identical to those in the continuous pool — i.e. are features computed
*before* subsampling, not after?

The negative control uses a deliberately wrong reference: select the days
first, then compute features on the selected rows. Rolling statistics over
non-adjacent days produce garbage, and the invariant must detect it.

### Test parameters

| | |
|---|---|
| Relative tolerance | `INVARYANT_TOLERANS = 1e-6` |
| Threads | `OMP/OPENBLAS/MKL_NUM_THREADS = 8` |
| Command | `python run_doygunluk.py --dogrula` |

Bit-level equality is *not* expected (OpenMP summation order); the real
difference is always logged at full precision.

---

## 4. Results — 18/18 passed

Wall clock ≈ 1.2 min. The gate was run twice: under pyarrow 25.0.0 (before
the grid) and under 22.0.0 (after the version change). **Both runs: 18/18,
and the relative differences of invariants 1–2 agreed to the last digit.**

### Invariant 1 — window equivalence (2019)

Expected: `K=5 == K=all ==` `ablasyon.csv` clean/2019; `egitim_n = 261 798`.

| Model | K=5 | K=all | Reference | Rel. diff (pairwise) | Rel. diff (ref) |
|---|---|---|---|---|---|
| Linear Regression | 141.343658 | 141.343658 | 141.343658 | 0.0 | 0.0 |
| Polynomial Ridge | 136.502929 | 136.502929 | 136.502929 | 0.0 | 6.050675e-13 |
| Hist Gradient Boosting | 137.168967 | 137.168967 | 137.168967 | 0.0 | 0.0 |

`egitim_n` observed 261 798, expected 261 798, difference 0.

### Invariant 2 — Phase 2 compatibility (2023, `K = all`)

| Model | New | Reference | Rel. diff | Abs. diff |
|---|---|---|---|---|
| Linear Regression | 137.839921 | 137.839921 | 0.0 | 0.0 |
| Polynomial Ridge | 132.614714 | 132.614714 | 7.797529e-12 | 1.034067e-09 |
| Hist Gradient Boosting | 133.404201 | 133.404201 | 0.0 | 0.0 |

`egitim_n` 472 182 = expected; `test_n` 25 792 = expected. Largest observed
deviation 7.797529e-12 against a 1e-6 relative tolerance.

### Invariant 3 — warm-up boundary (2023)

| Window | `egitim_basla` | `egitim_n` observed | Expected | Diff | Warm-up | Boundary leaks |
|---|---|---|---|---|---|---|
| 1 | 2022 | 51 414 | 51 414 | 0 | 191 | False |
| 2 | 2021 | 103 974 | 103 974 | 0 | 191 | False |

Had the boundary leaked, 52 560 and 105 120 would be expected.
`test_n_ham` 52 560. Warm-up 191 = 24 (shift) + 168 (roll168) − 1; six sites
× 191 = 1 146.

### Invariant 4 — sampling code path (2019, `K = 5`, degenerate)

3 models × 3 seeds = 9 checks; every one with relative and absolute
difference 0.0, `egitim_n` 261 798 (subsampling == sliding).

| Model | Seed 11 | Seed 22 | Seed 33 | Sliding |
|---|---|---|---|---|
| Linear Regression | 141.343658 | 141.343658 | 141.343658 | 141.343658 |
| Polynomial Ridge | 136.502929 | 136.502929 | 136.502929 | 136.502929 |
| Hist Gradient Boosting | 137.168967 | 137.168967 | 137.168967 | 137.168967 |

### Invariant 5 — order of computation (2023, `K = 2`, seed 11)

```
secilen_n              103974   (target 103974, diff 0)
havuz_gun_konum          3280
secilen_gun_konum         723
gun_orani_konum        0.2204
gun_kopuklugu_konum       560
farkli_oznitelik            0   (29 features, all identical)
ters_sira_farkli_oran     1.0
ters_sira_maks_fark  168.053036 W
```

**The last two lines are the negative control** and are the test's
discriminating power: had features been computed in the wrong order
(subsample first, then compute), 100 % of `P_roll168_mean_lag24` values
would change, with a maximum difference of 168.053036 W. Without those two
lines the invariant was a tautology.

---

## 5. Run statistics

| Run | Cells | Status | Wall clock | pyarrow |
|---|---|---|---|---|
| main grid | 255/255 | 255 ok, 0 errors | 9.5 min (log) / 11.0 min (wall) | 25.0.0 |
| wide run | 50/50 | 50 ok, 0 errors | 81.0 / 81.2 min | 25.0.0 |
| 2022 verification | 10/10 | 10 ok, 0 errors | 19.6 min | 25.0.0 |
| remaining four years | 40/40 | 40 ok, 0 errors | 96.3 / 96.5 min | 22.0.0 |
| **invariant gate** | **18/18 checks** | **all passed** | **1.2 min** | both |

Main grid, 255 cells:

```
sliding       {1,2,3,5,all} x 5 years x 3 models x 1 seed  =  75
subsampling   {1,2,3,5}     x 5 years x 3 models x 3 seeds = 180
```

Subsampling `K = all` is **not** produced: it is the same cell as sliding
`K = all` (`paylasilan = True` in `doygunluk_ozet_egri.csv`).

A failed cell is written to disk with `durum = "hata"`; it is never silently
skipped, and the grid resumes where it stopped.

---

## 6. A gate that caught a real error

The Class B gate in the Phase 2 uncertainty measurement — *the logged RMSE
of the night variant must equal the RMSE recomputed over all rows from the
clean variant's stored predictions* — **failed on DKASC at 12/15**, maximum
deviation 0.5787 W.

It was diagnosed before anything was reported:

- the failing cells were **only the three models of 2018**;
- of six `ariza`-flagged hours, five were in 2017 (training-only, never in a
  test set) and one in 2018 (2018-12-06 08:00);
- so the failing set coincided exactly with the year whose test set
  contained a fault row.

**The cause was not the taxonomy but the diagnostic's population
definition:** `hucre_kos` excludes fault rows from evaluation under rule 7,
while the identity computation did not. The `ariza` column was added to the
prediction files, all measures were put on the same population, and the
DKASC grid was re-run. The gate then passed **15/15, deviation 5.684e-14**,
and the regression gate showed zero differences across 810 comparisons.

The general lesson, which goes into the paper: **in a leakage study the
"same population" assumption must be verified separately for every measure.**
Had the gate not caught this, DKASC's Class B identity would have been
reported 0.1 % wrong.
