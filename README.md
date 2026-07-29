# Leakage-Aware Day-Ahead PV Power Forecasting: A Ten-Year Multi-Site Ablation Study

Code and experiment harness for a ten-year, six-site study quantifying how common
evaluation choices inflate reported skill in machine-learning photovoltaic power
forecasting.

This repository extends an earlier single-year study (see *Related work* below) from
one year to ten, from four sites to six, and adds a controlled leakage ablation and a
model-ranking stability analysis.

## Research questions

1. **How much does each form of data leakage inflate reported performance?**
   Six variants are compared against a leakage-free reference: contemporaneous
   meteorological predictors, random rather than chronological splitting, inclusion of
   night-time zero-production records, preprocessing fitted on the full dataset, and a
   combination representing worst-case common practice.
2. **Can single-year benchmarks distinguish algorithms at all?** Rankings are
   recomputed across rolling annual origins and tested with Diebold-Mariano,
   reporting effect size alongside statistical significance.
3. **How much training history is actually needed?** Learning curves are computed
   over 1, 2, 3, 5 and 10 years of history.

## Data

Hourly data are obtained from the **PVGIS** hourly radiation tool
(PVGIS-SARAH3 radiation database) for identically configured 1 kWp crystalline-silicon
systems: 30° tilt, 0° azimuth (south-facing), 14% system losses, free-standing mounting.

| Site | Country | Latitude | Mean annual yield (kWh/kWp) |
|---|---|---|---|
| Ouarzazate | Morocco | 30.93 °N | 1895.9 |
| Portimão | Portugal | 37.19 °N | 1703.4 |
| Konya | Turkey | 37.43 °N | 1583.8 |
| Adana | Turkey | 36.82 °N | 1536.4 |
| Brăila | Romania | 45.32 °N | 1280.3 |
| Leipzig | Germany | 51.34 °N | 1069.9 |

Period: 1 January 2014 – 31 December 2023 (87,648 hourly observations per site;
525,888 in total).

**PVGIS output is simulated, not measured.** PV power is computed by PVGIS from
irradiance and meteorological inputs using a module performance model. This study
therefore treats the dataset as a controlled, internally consistent simulation
environment rather than ground truth — which is what a controlled ablation requires,
since the underlying generating process is known.

### Reproducing the dataset

Raw data are **not** committed. Regenerate them exactly:

```bash
pip install -r requirements.txt
python pvgis_pipeline.py hepsi
```

Verify you obtained the identical dataset by checking the frozen version hash written
to `veri/veri_surumu.txt`:

```
sha256_16: f722a717bac502c2
```

Any mismatch means the dataset differs and results will not reproduce exactly.

## Repository layout

```
pvgis_pipeline.py    download, verify and assemble the dataset
run_smoke.py         single-split sanity run over the full feature pipeline
run_ablasyon.py      leakage ablation grid (variant x model x test year)
pv10/
  config.py          all constants: lags, seed, paths, leakage variant registry
  features.py        solar geometry and feature construction
  models.py          eleven regression algorithms with fixed hyperparameters
  evaluate.py        metrics, day-block bootstrap, Diebold-Mariano
  experiment.py      grid execution, resumable, per-cell logging
sonuclar/            experiment logs (committed)
```

## Forecasting design

24-hour-ahead hourly PV power. Predictors are restricted to information available at
least 24 hours before the target hour: lagged power, irradiance, temperature and wind
speed (24, 48 and 168 h); lagged rolling statistics; cyclic calendar encodings; a
lagged clear-sky performance ratio; and site one-hot encoding.

Solar elevation is **recomputed astronomically** from latitude, longitude and
timestamp using Spencer approximations for declination and the equation of time. It is
deterministic and therefore available at any horizon. PVGIS's own solar-elevation
column is used *only* to define daylight hours, never as a predictor.

Evaluation is restricted to daylight hours and benchmarked against 24-hour
persistence. Metrics: MAE, RMSE, nRMSE (relative to both mean daylight power and
installed capacity), R², and persistence-based skill.

## Running the experiments

```bash
python run_smoke.py                     # verify the pipeline end to end
python run_ablasyon.py --tahmin         # estimate runtime without running
python run_ablasyon.py                  # full grid, resumable
python run_ablasyon.py --ozet           # summarise the existing log
```

Interrupted runs resume automatically: completed cells are read from
`sonuclar/ablasyon.csv` and skipped.

## Reproducibility

Random seed 42 throughout. Hyperparameters are fixed a priori and never tuned on
validation or test partitions. Pinned dependency versions are in `requirements.txt`;
results were produced with Python 3.14, pandas 3.0.5, NumPy 2.5.1 and
scikit-learn 1.9.0.

## Related work

This study builds on a previous single-year, four-site comparison of eleven machine
learning algorithms by the same authors. Preliminary findings were reported there; the
multi-year leakage ablation and ranking-stability analysis are new to this work.

## Data source and licence

Radiation and PV data: **Photovoltaic Geographical Information System (PVGIS)**,
European Commission Joint Research Centre — <https://re.jrc.ec.europa.eu/pvg_tools/en/>

Code in this repository is released under the MIT Licence.