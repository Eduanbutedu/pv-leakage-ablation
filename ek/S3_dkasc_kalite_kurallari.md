# S3 — DKASC quality rules (condensed)

Supplementary material, condensed from `dokumanlar/dkasc-kalite-kurallari.md`.
No number in this file was produced for it.

**These rules were frozen before any DKASC row was processed and before any
model was trained.** Two of them (9 and 10) were added after the first eight,
still before processing; both carry their own "why late" record. Rule 10 was
subsequently corrected twice. Nothing was deleted or struck from the record —
superseded text remains in the source document.

---

## 0. Scope

| | |
|---|---|
| Source | dkasolarcentre.com.au, *All Individual Technologies (yearly data set with weather data)* |
| Files | `Alice_Springs_{2017..2022}.csv` (6 files, ≈ 1.2 GB) |
| Resolution | 5 minutes |
| Columns | 197, identical names and order in all six years |
| Unique ids | 50 (49 PV arrays + 1 weather station) |
| Combined rows | 621 933 (trimmed to calendar years) |
| Full grid | 631 008 (2017-01-01 00:00 … 2022-12-31 23:55) |
| Missing stamps | 9 075 (1.4382 %) |
| Target array | `92_DKA_M6_B_Phase_Active_Power` (system 13), 5.25 kWp |
| Test years | 2018–2022; 2017 is training/warm-up only |
| Frozen version | `sha256_16 = f7f644df5e0d1618`, 52 584 hours |

Counts below are over the full 621 933-row combined series unless stated
otherwise; percentages use that denominator.

**2022 is not dropped despite being anomalous.** The deviations measured in
2022 are real. Discarding a year for being "anomalous" is a post-hoc
selection — exactly the practice this study criticises. The same applies to
2019 (drought year) and 2020-12 (low-irradiance month).

---

## 1. The ten rules

### Rule 1 — Pyranometer night offset

| | |
|---|---|
| **Observation** | With the sun below the horizon (`sin h < 0`), GHI is not zero: median 2.2921 W/m², mean 2.5560, p99 9.9649. GHI is exactly zero in only 12 rows across six years. |
| **Threshold** | Where `sin h < 0`: GHI, DHI, GTI, DTI → 0 |
| **Rationale** | ISO 9060 allows a ±5 W/m² zero offset; night irradiance is zero by definition. Leaving the offset contaminates the clear-sky ratio and the night/day transitions. |
| **Affected** | **311 861 rows (50.1438 %)** zeroed; 13 168 of them (2.1173 %) exceeded 5 W/m² |

This is a *correction*, not an evaluation filter — night rows remain in
training.

### Rule 2 — Relative humidity ceiling

| | |
|---|---|
| **Observation** | RH maximum 131.1584; RH > 100 in 5 054 rows (0.8126 %), RH > 105 in 5 rows (0.0008 %, all 2020-02/03) |
| **Threshold** | `clip(0, 100)`; additionally flag the row if RH > 105 |
| **Rationale** | RH ≤ 100 % by definition. The 100–105 band is sensor calibration tolerance and is clipped; above 105 is measurement error. |
| **Affected** | **5 054 clipped**, 5 flagged |

### Rule 3 — Diffuse cannot exceed global

| | |
|---|---|
| **Observation** | `DHI > GHI` in 6 146 rows (0.9882 %); `DHI > 1.05 × GHI` in 5 134 rows (0.8255 %) |
| **Threshold** | `DHI = min(DHI, GHI)`; flag the row if the ratio exceeded 1.05 |
| **Rationale** | Diffuse is a component of global; exceeding it is physically impossible. |
| **Affected** | **6 146 corrected**, 5 134 flagged |

This count is inversely locked with the night GHI offset (correlation
−0.6354): once rule 1 runs, it is *expected* to fall, and the fall was
measured and reported (production: 5 flagged vs 5 134 raw).

### Rule 4 — Wind channels are not used

| | |
|---|---|
| **Observation** | `Wind_Speed` is **entirely empty in all 72 months** — not one filled value in 621 933 rows. `Wind_Direction` is 99.9038 % filled but out of compass range: min −6.9796, max 11 596.1650, 604 426 distinct values, 3 421 rows (0.5501 %) out of range. The sign/unit convention changes twice: the `WD > 360` regime closes in 2019-06; the `WD < 0` regime opens 2020-10 and closes 2022-02. |
| **Threshold** | None — **both channels are removed from the feature set** |
| **Rationale** | No speed, and direction cannot be validated. Feeding a channel of unknown unit into a model imports an unmeasured uncertainty. |
| **Affected** | The feature set: 29 inputs → 21. See [S6](S6_on_kayit_sapmalari.md) §3 — a departure from the frozen feature-identity rule, reported separately. |

### Rule 5 — Negative power

| | |
|---|---|
| **Observation** | M6_B: `P < 0` in 1 825 rows (0.2934 %), minimum −0.0188 kW. M2_C: 1 711 rows (0.2751 %), minimum −0.0035 kW. Neither array has any row below −0.05 kW. |
| **Threshold** | `\|P\| ≤ 0.05 kW` → 0; `P < −0.05 kW` → missing |
| **Rationale** | Night inverter draw and measurement noise produce small negatives; a large negative is a measurement fault. |
| **Affected** | M6_B **1 825**, M2_C 1 711 rows zeroed |

The second branch stays empty in both arrays. The rule is written anyway,
because the threshold was chosen from physics, not from the data.

### Rule 6 — Irradiance ceiling

| | |
|---|---|
| **Observation** | `GHI > 1400` W/m² in 27 rows (0.0043 %); `GHI > 1.5 × G0` in 1 126 rows (0.1810 %) |
| **Threshold** | `GHI > 1.5 × G0` → missing (G0 = extraterrestrial horizontal irradiance) |
| **Rationale** | Cloud-edge reflection can genuinely cause 1.4× overshoot; above 1.5× is not physical. Normalising by G0 rather than a fixed W/m² keeps the threshold independent of season and hour. |
| **Affected** | **1 126 rows → missing** (1 117 in production; the difference comes from rule 1 running first and from solar position being computed at label + 2.5 min) |

**Diagnosed, not changed.** When rule 10 collapsed, rule 6's firing pattern
was measured against an interpretation rule written *before* the
measurement. Of the 1 117 hits, 99.64 % occur at `sin h < 0.05` (median
elevation 0.128°), median GHI at firing is 12.949 W/m², and zero hits fall
within 180 min of solar noon. The mechanism: `G0 = E0 · sin h` → 0 near the
horizon (median G0 at firing 3.103 W/m²), while the pyranometer offset rule 1
measures is the same magnitude — so the `1.5 × G0` line falls *inside* the
sensor's own noise.

**The rule was not relaxed.** Loosening a pre-registered threshold because
its firing pattern caused downstream trouble is precisely the post-hoc
behaviour this study criticises. It is recorded and reported as is.

### Rule 7 — Daytime zero production

| | |
|---|---|
| **Observation** | `GHI > 200` W/m² while `P == 0`: M6_B **108** rows (0.0174 %), M2_C 109 (0.0175 %); 234 954 rows have GHI > 200 |
| **Threshold** | `GHI > 200` and `P == 0` → fault flag. **Excluded from evaluation only, never from training.** |
| **Rationale** | Same lesson as the night rows: filters apply at evaluation. Fault days are real operating conditions; removing them from training flatters the model, while leaving them in evaluation blames the forecaster for an unforecastable event. |
| **Affected** | M6_B **110**, M2_C 110 rows (counting `P ≤ 0`) |

### Rule 8a — Partial-fault day flag (leak-free version)

| | |
|---|---|
| **Observation** | Some days show a mid-day collapse; system 12 (M5_B) was excluded for this reason |
| **Threshold** | Flag the day if its daytime median is below **0.3 ×** a single daytime median computed **from the training split only** |
| **Rationale** | The first version defined the threshold against a *monthly* median computed over the whole year, test period included — which is exactly the *global scaling* variant this paper measures. Unacceptable in a leakage replication. The threshold is now recomputed per fold, from the training split only, and sits in the same place as the scaler. |
| **Affected** | Indicative only (production recomputes per fold): with all six years as reference, M6_B daytime median 2.6351 kW, threshold 0.7905, **70/2164 days flagged (3.235 %)**; M2_C 2.9371 / 0.8811 / 69/2164 (3.189 %) |

No calendar-month reference is used: a monthly reference is undefined when
the training split never saw that month.

*(Rule 8b — a physical `power / GTI` threshold — was evaluated and
**rejected**, because it rests on GTI, whose plane was measured and found
not to match the array's. It is recorded as rejected.)*

### Rule 9 — Temperature validity range `[added later — 8 Aug 2026]`

**Why late:** the first eight rules never addressed temperature; the gap was
recorded as an open defect at the time. Still written before any row was
processed.

| | |
|---|---|
| **Observation** | `T ≤ −39` (analog rail, ≈ −39.9879) 1 649 rows (0.2651 %); `−39 < T ≤ −20` 1 390 (0.2235 %); `45.2 < T ≤ 50` 29 (0.0047 %); `T > 50` 4 (0.0006 %); `T` missing 600 (0.0965 %). The rail is not exactly constant (−39.987949 … −39.987919), forms 56 unbroken blocks clustered in three months. |
| **Threshold** | `T < −10 °C` or `T > 50 °C` → missing. Where `T ≤ −39`, **RH is also set missing.** |
| **Rationale** | Alice Springs record low −7.5 °C, record high 45.2 °C. The bracket is deliberately **wide** (−10 … +50): chosen from the site's climate records, not from the data, and placed outside the records so a genuine record-breaking value is not clipped by our own hand. The 29 rows in `45.2 < T ≤ 50` are therefore **kept**. |
| **Affected** | **3 046 rows (0.4898 %)** → missing in T; of those **1 649** also in RH. Under rule 10 (12/12), **259 hours** drop. |

RH is tied to the rail itself, not to an RH threshold: all rail rows have RH
between 0.0116 and 0.9518 (median 0.1498), whereas only 19 non-rail rows have
RH < 0.1. An `RH < 0.1` threshold would have caught just 646 of the 1 649.

### Rule 10 — Complete-slot requirement in hourly aggregation `[added later — 8 Aug 2026; corrected twice]`

**Why late:** 5-minute → hourly aggregation was listed as a step but its
*missing-slot* behaviour was never defined. Leaving it undefined is silent
failure.

| | |
|---|---|
| **Observation** | Of 52 584 hourly buckets, GHI has 12/12 slots filled in **51 736 (98.387 %)**, 0/12 in 787 (1.497 %), partial in **61 (0.116 %)**. DHI identical; M6_B 12/12 = 51 742. |
| **Threshold (in force)** | **Input** (source of lag and rolling features): valid if **≥ 9/12** slots are filled in each of the four channels; the partial mean is used. **Target and evaluation: the 12/12 requirement stands unchanged.** Hours passing the input threshold but short of 12/12 are flagged `kismi` and are never a training target or a test observation. |
| **Rationale** | A mean of three slots and a mean of twelve are not the same estimator. 9/12 is three quarters of an hour; 1/12 is a point sample disguised as an hourly mean. |
| **Affected** | Hours valid **as input** 50 375 → **51 520**; hours valid as **target and evaluation 50 375 — unchanged**. |

**The correction that matters.** The original "61 hours" cost was measured on
*raw* data. In production rule 10 is step 7: rules 6 and 9 run first and
void individual 5-minute slots. Each was counted correctly on its own; their
*interaction* was never computed. The real cost:

| Source | Hours | Share |
|---|---|---|
| Entirely empty (0/12) | 787 | 35.63 % |
| Genuinely partial (1–11 slots) | 62 | 2.81 % |
| **Raw 12/12 was complete, a rule voided it** | **1 360** | **61.57 %** |
| — of which rule 6 (GHI) | 1 115 | |
| — of which rule 9 (T2m) | 257 | |
| **Total invalid hours** | **2 209** | **4.2009 %** |

So rule 10's marginal cost was not 61 hours but **1 422**. Downstream this
was destructive: `roll168` needs 168 *consecutive* valid hours, and rule 6's
dropped hours are almost all isolated single holes that shatter every window
they fall inside. Only 22 unbroken ≥168-hour blocks survived, and the feature
table fell from 52 584 rows to **1 344 (2.56 %)** — 57 rows in 2022. The
DKASC ablation could not have been run.

**Why relax the input threshold and not interpolate.** Interpolation was
measured and came out *worse*: it yields 46 748 usable rows against 46 857
for the `≥ 9` input threshold — it invents numbers and saves fewer rows. The
reason is that these hours were not empty: in 97.43 % of isolated single
hours the raw data was 12/12 complete and a rule had voided it, and the
remaining 2.57 % held genuine partial measurement. **None were empty (0/12
share: 0.00 %).** There was no hole to fill, only an unused measurement.

| Input threshold | Feature rows | Target also present | Share |
|---|---|---|---|
| 12/12 (original) | 1 344 | 1 321 | 2.51 % |
| ≥ 11 slots | 46 109 | 44 856 | 85.30 % |
| **≥ 9 slots (selected)** | **48 162** | **46 857** | **89.11 %** |
| ≥ 1 slot | 49 181 | 47 854 | 91.00 % |
| *(comparison) linear interpolation* | *48 044* | *46 748* | *88.90 %* |

**This pattern is not new in this project.** Night rows stay in training
while the daylight filter applies at evaluation only; rules 1 and 7 carry
the same note. Relaxing at the input and holding firm at the target is the
distinction the study has defended throughout: training sees real operating
conditions, evaluation is measured under clean ones.

---

## 2. Application order

The rules are order-dependent. The order in force:

1. Read six yearly files, trim the 288 out-of-calendar rows, concatenate (621 933 rows)
2. Snap to the full 5-minute grid; absent stamps are **missing**, never silently skipped
3. **Rule 1** — zero the irradiance channels at night
4. **Rules 2, 3, 6, 9**
5. **Rule 5**
6. Transposition at **5-minute** resolution (`Rb` is non-linear within the hour and explodes at low sun angles)
7. **Rule 10** — aggregate into local-hour buckets; ≥ 9/12 for input, 12/12 for target and evaluation
8. **Reindex onto the full hourly grid** — critical: `features.py` uses positional `shift(k)`. PVGIS had no gaps; DKASC has 787+ missing hours, and in a gapped series `shift(24)` takes *24 rows back, not 24 hours back*. The study's strongest feature, `G_i_lag24`, would come from the wrong row **and nothing would raise an error**
9. **Rule 7** at hourly level — excluded from evaluation, never from training
10. Convert to the common schema (`P` kW → W, `konum = "dkasc_m6b"`, `utc_ofset = +9.5`)
11. Transposition gate + schema gate — **stop if either fails**
12. Freeze: parquet + `sha256_16` + version record
13. **Split.** Only *after* this: **rule 8a**, threshold recomputed per fold from the training split
14. Generate features. No wind (rule 4).

Rule 8a arriving *after* the split matters as much as the rule itself: moved
earlier, the leak returns.
