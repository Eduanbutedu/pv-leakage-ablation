# S1 — Feature definitions

Supplementary material. Compiled from `pv10/features.py`, `pv10/config.py`
and `dokumanlar/dkasc-kalite-kurallari.md`. No number in this file was
produced for it; every value is read from the frozen configuration or from
an existing result file.

Feature definitions reproduce Section 2.3 of the authors' earlier
single-year study verbatim. The core set is **fixed**: it is not tuned, and
a feature added for a later data set is reported as a separate deviation
(see [S6](S6_on_kayit_sapmalari.md)), never folded into the main analysis.

---

## 1. The core set (PVGIS, clean variant)

**29 model inputs.** Forecast horizon is 24 h; every dynamic feature is
therefore lagged by at least 24 h.

| # | Feature | Definition | Lag / window |
|---|---|---|---|
| 1 | `elev_sin` | Sine of solar elevation at the **target** hour, clipped at 0. Derived astronomically from latitude, longitude and timestamp (Spencer 1971 declination and equation-of-time approximations). | none (target hour) |
| 2–4 | `P_lag{24,48,168}` | PV power, lagged | 24, 48, 168 h |
| 5–7 | `G_i_lag{24,48,168}` | Plane-of-array irradiance, lagged | 24, 48, 168 h |
| 8–10 | `T2m_lag{24,48,168}` | Air temperature at 2 m, lagged | 24, 48, 168 h |
| 11–13 | `WS10m_lag{24,48,168}` | Wind speed at 10 m, lagged | 24, 48, 168 h |
| 14 | `P_roll24_mean_lag24` | Rolling mean of power | 24 h window, shifted 24 h |
| 15 | `P_roll24_std_lag24` | Rolling standard deviation of power | 24 h window, shifted 24 h |
| 16 | `P_roll168_mean_lag24` | Rolling mean of power | 168 h window, shifted 24 h |
| 17 | `G_i_roll24_mean_lag24` | Rolling mean of irradiance | 24 h window, shifted 24 h |
| 18 | `bg_orani_lag24` | Clear-sky performance ratio `P / (1000 · sin h_s)`, lagged | 24 h |
| 19 | `bg_orani_roll24_lag24` | Rolling mean of the clear-sky ratio | 24 h window, shifted 24 h |
| 20–21 | `h_sin`, `h_cos` | Cyclical hour-of-day encoding, period 24 | none (calendar) |
| 22–23 | `d_sin`, `d_cos` | Cyclical day-of-year encoding, period 365.25 | none (calendar) |
| 24–29 | `loc_*` | Site one-hot encoding, six levels: `adana`, `konya`, `braila`, `portimao`, `leipzig`, `ouarzazate` | none (identity) |

Rolling statistics use `min_periods = window`, so a window is emitted only
when it is complete. The single exception is `bg_orani_roll24_lag24`, which
uses `min_periods = 6`, because the clear-sky ratio is undefined at night
by construction.

### Columns carried but never used as inputs

`oznitelik_kolonlari` excludes these from the design matrix:

| Column | Role |
|---|---|
| `y` | Target (PV power at the target hour) |
| `konum`, `time_utc` | Identity / join keys |
| `H_sun` | **Daylight mask only.** Never a feature — see §2 |
| `persistence` | 24-hour persistence reference, for skill scores |
| `kismi`, `ariza` | Exclusion flags (DKASC only; rules 10 and 7) |

---

## 2. Two definitions that carry the leakage argument

**`H_sun` is never a feature.** PVGIS supplies a solar-elevation column, but
it is used *only* to build the daylight evaluation mask. Elevation entering
the model is re-derived astronomically (`elev_sin`) from coordinates and
time, so it is legitimately available at any forecast horizon. Using the
supplied column as an input would make the feature set depend on a quantity
the provider computed, not one a forecaster can know.

**Solar geometry uses the observation timestamp.** The PVGIS timestamp
carries the satellite observation minute (`:09`, `:10`). Computing geometry
from the hour-rounded stamp introduces a systematic offset of roughly 1.5°.
Geometry is therefore computed from `time_gozlem` where that column exists,
falling back to `time_utc` otherwise.

**Warm-up is consumed inside the window, not at the start of the data set.**
If features are generated over the whole record and then sliced by year, a
model described as "trained on 1 year" silently carries rolling statistics
from earlier years. Warm-up is 191 rows per site (24 from the longest shift
plus 168 from the longest rolling window, minus 1). Invariant 3 measures
this; see [S4](S4_invaryant_kapisi.md).

**Night rows stay in training.** The clear-sky ratio is missing at night by
definition. Putting it on the mandatory-dropna list would delete every night
observation. Training *includes* night hours; the daylight filter is applied
at **evaluation only**.

---

## 3. Variant feature sets

Only the **contemporaneous** variant changes the feature set. The other
leakage variants change the split, the preprocessing fit scope, or the
evaluation mask — not the inputs.

| Variant | Inputs added | Count (PVGIS) |
|---|---|---|
| clean | — | **29** |
| contemporaneous | `G_i_eszaman`, `T2m_eszaman`, `WS10m_eszaman`, `H_sun_eszaman` — all four at the **target** hour | **33** |
| shuffled split | — | 29 |
| night | — | 29 |
| global scaling | — | 29 |
| worst case | same four as contemporaneous | 33 |

The contemporaneous variant is a deliberate bad practice: it hands the model
the weather at the hour it is supposed to forecast.

---

## 4. The DKASC (reduced) set

The declared feature set is a **parameter**, not a code branch. The
measurement-data replication declares a shorter tuple rather than adding a
`wind=False` flag, so the deviation is a reportable value instead of a side
effect of the code path.

| | PVGIS | DKASC |
|---|---|---|
| Lagged variables | `P`, `G_i`, `T2m`, `WS10m` | `P`, `G_i`, `T2m` |
| Contemporaneous variables | `G_i`, `T2m`, `WS10m` | `G_i`, `T2m` |
| Site one-hot levels | 6 | 1 (`loc_dkasc_m6b`) |
| **Inputs, clean** | **29** | **21** |
| **Inputs, contemporaneous** | **33** | **24** |

Wind is absent because both DKASC wind channels fail quality rule 4: wind
speed is empty in all 72 months, and wind direction cannot be validated
(range −6.9796 to 11 596.1650, with the sign/unit convention changing twice).
See [S3](S3_dkasc_kalite_kurallari.md), rule 4, and
[S6](S6_on_kayit_sapmalari.md) §3.

Because the two feature sets differ, PVGIS and DKASC inflation ratios are
not directly comparable. A **matched control** — PVGIS data run with the
DKASC feature set, reported throughout as *PVGIS reduced* — separates the
feature-set contribution from the data contribution.

---

## 5. Provenance

| Item | Value |
|---|---|
| Data source | PVGIS-SARAH3, 1 kWp c-Si |
| Coverage | 2014–2023, six sites, 525 888 rows |
| Frozen data version | `sha256_16 = f722a717bac502c2` |
| DKASC data version | `sha256_16 = f7f644df5e0d1618`, 52 584 hours |
| Feature code | `pv10/features.py` |
| Constants | `pv10/config.py` (`GECIKMELER`, `GECIKMELI_DEGISKEN`, `YUVARLANAN`, `ESZAMAN_DEGISKEN`, `DKASC_GECIKMELI`, `DKASC_ESZAMAN`) |

The feature frame was verified byte-for-byte against the pre-parameterisation
reference three times (after tuple parameterisation, after the target-dropna
change, and after flag propagation): shapes `(524742, 34)` and
`(524742, 38)`, 17 841 228 and 19 940 196 values, identical each time.
