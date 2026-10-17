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
results were produced with Python 3.14, pandas 3.0.5, NumPy 2.5.1,
scikit-learn 1.9.0 and pyarrow 22.0.0.

pyarrow is pinned to 22.0.0 rather than the latest release because Windows Smart App
Control blocks the `arrow.dll` shipped with 25.0.0 on the machine used for the runs.
The pin affects only Parquet I/O. The frozen dataset is byte-identical under both
versions (`sha256_16 = f722a717bac502c2`), the five experiment invariants pass 18/18
checks under 22.0.0, and the reference metrics they compare against reproduce to the
same digits as under 25.0.0.

## Reproducing the paper

This section maps every table and figure in the manuscript to the command that
produces it and the file it is read from. Figures are referred to by **file name**,
not by number, because figure numbering in the manuscript is not final.

### 1. Environment

```bash
python -m venv .venv                       # results were produced with Python 3.14.6
.venv/Scripts/python -m pip install -r requirements.txt   # Windows
# .venv/bin/python -m pip install -r requirements.txt     # Linux / macOS
```

All commands below are run from the repository root with that interpreter.
Pinned versions are in `requirements.txt`. The random seed is 42; the Phase 4
subsampling seeds are 11, 22 and 33; the thread constant is 8 (recorded in
`sonuclar/doygunluk_ozet_kunye.txt`). Hyperparameters are fixed in `pv10/models.py`
and never tuned.

### 2. Data and hash verification

Neither dataset is committed. Both are regenerated and checked against a frozen hash;
a mismatch means the results will not reproduce exactly.

| Dataset | Command | Output | Hash file | Expected `sha256_16` |
|---|---|---|---|---|
| PVGIS, 6 sites, 2014-2023 | `python pvgis_pipeline.py hepsi` | `veri/pvgis_10yil.parquet` | `veri/veri_surumu.txt` | `f722a717bac502c2` |
| DKASC Alice Springs, array 13, 2017-2022 | `python dkasc_pipeline.py dogrula ham/dkasc` then `python dkasc_pipeline.py duzenle ham/dkasc` | `veri/dkasc_m6b.parquet` | `veri/dkasc_veri_surumu.txt` | `f7f644df5e0d1618` |

The DKASC raw files are not downloadable by script. Obtain the six yearly Alice
Springs files from <https://dkasolarcentre.com.au/> and place them as
`ham/dkasc/Alice_Springs_2017.csv` … `Alice_Springs_2022.csv` (about 1.2 GB in
total). The quality-control rules applied to them were fixed before any row was
processed: `dokumanlar/dkasc-kalite-kurallari.md`.

To check a hash independently of the pipelines:

```bash
python -c "import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest()[:16])" veri/pvgis_10yil.parquet
```

The expected values are also in `pv10/config.py` (`VERI_SHA16`, `DKASC_VERI_SHA16`).

### 3. Gates before any grid

```bash
python run_smoke.py                 # single-split sanity run
python run_doygunluk.py --dogrula   # 5 invariants / 18 checks; must pass before Phase 4
```

### 4. Note on the committed logs

The result logs in `sonuclar/` are committed and every grid **resumes**: cells already
present in a log are skipped. Running a grid command on a fresh clone therefore does
nothing. To regenerate a log from scratch, move the committed file aside first, run
the command, then compare the two without tolerance:

```bash
python -m arac.regresyon_kiyas --referans <moved-aside copy> --yeni sonuclar/ablasyon.csv \
    --anahtar varyant,model,test_yil --nondet ""
```

Random Forest and Extra Trees differ in the last one or two units in the last place
between runs (within-process parallel summation, measured in
`sonuclar/nondeterminizm_olcum.csv`). No reported figure uses them except the
ten-model pool, and no reported digit is affected.

### 5. Tables

| Table | Content | Command | Source file(s) |
|---|---|---|---|
| 1 | Literature audit, 27 studies | none: manual coding | Supplementary S7 (not in this repository) |
| 2 | Sites and mean annual specific yield | `python pvgis_pipeline.py duzenle ham/` (printed at the end) | `veri/pvgis_10yil.parquet` |
| 3 | The six configurations | none: definitions | leakage variant registry in `pv10/config.py` |
| 4 | Mapping to the Kapoor and Narayanan (2023) taxonomy | none: descriptive | — |
| 5 | Ablation, simulated data | `python run_ablasyon.py` | `sonuclar/ablasyon.csv` |
| 6 | Inflation ratios, three runs | `python run_ablasyon.py` · `python run_ablasyon.py --set dkasc --etiket pvgis_indirgenmis` · `python run_ablasyon.py --set dkasc --veri veri/dkasc_m6b.parquet --yillar 2018,2019,2020,2021,2022 --etiket dkasc` | `sonuclar/ablasyon.csv`, `ablasyon_pvgis_indirgenmis.csv`, `ablasyon_dkasc.csv` |
| 7 | Population-free effect A of shuffled splitting | see *Phase 2 uncertainty* below | `sonuclar/ablasyon_belirsizlik_dm_{ana,pvgis_indirgenmis,dkasc}_dm.csv` (`A_model`) |
| 8 | Learning curves | `python run_doygunluk.py` (summary written automatically; `--ozet` rewrites it from the logs) | `sonuclar/doygunluk.csv` → `sonuclar/doygunluk_ozet_egri.csv` |
| 9 | Variance decomposition | as Table 8 | `sonuclar/doygunluk_ozet_varyans.csv` |

**Verifying Tables 5-9 against the manuscript.** `python -m arac.tablolari_uret` recomputes
every value in Tables 5-9 from the CSVs above and compares it, at the precision printed
in the manuscript, with the value in the manuscript. It lists every value that does not
match and exits with status 1 if there is one. Current state: 65 of 65 match.

**Phase 2 uncertainty (Table 7, Section 5.1-5.3 counts).** The three ablation grids are
re-run with prediction saving under their own labels, then the three uncertainty
measures (paired clustered DM, day-block bootstrap, night identity) are applied:

```bash
python run_ablasyon.py --etiket dm_ana --tahmin-kaydet
python run_ablasyon.py --set dkasc --etiket dm_pvgis_indirgenmis --tahmin-kaydet
python run_ablasyon.py --set dkasc --veri veri/dkasc_m6b.parquet \
    --yillar 2018,2019,2020,2021,2022 --etiket dm_dkasc --tahmin-kaydet

python -m arac.ablasyon_dm --etiket dm_ana --log sonuclar/ablasyon_dm_ana.csv
python -m arac.ablasyon_dm --etiket dm_pvgis_indirgenmis --log sonuclar/ablasyon_dm_pvgis_indirgenmis.csv
python -m arac.ablasyon_dm --etiket dm_dkasc --log sonuclar/ablasyon_dm_dkasc.csv --kapasite 5250
```

Outputs: `sonuclar/ablasyon_belirsizlik_dm_<source>_{dm,bootstrap,gece_ozdeslik}.csv`. The
re-run grids reproduce `ablasyon*.csv` exactly. The interpretation rules were fixed
before the first test statistic existed: `dokumanlar/varyant-dm-yorum-kurali.md`.

**Phase 3 (Section 5.4, ranking across seven test years).**
`python run_siralama.py` → `sonuclar/siralama_rmse.csv`, `siralama_karsilastirma.csv`,
`siralama_kendall.csv`.

**Phase 4 ten-model pool and paired tests (Sections 5.4-5.5).** These runs write to their
own labelled logs so that the main grid's summary is not contaminated. The commands
below are reconstructed from the shape of the committed logs and the commit messages;
the exact invocations were not recorded.

```bash
python run_doygunluk.py --pencere 1,tum --etiket dm --tahmin-kaydet           # 75 cells
python run_doygunluk.py --modeller tumu --kol kaydirmali --pencere tum --etiket genis   # 50 cells
python run_doygunluk.py --modeller tumu --kol kaydirmali --pencere tum \
    --yillar 2022 --etiket dm2022 --tahmin-kaydet                             # 10 cells
python run_doygunluk.py --modeller tumu --kol kaydirmali --pencere tum \
    --yillar 2019,2020,2021,2023 --etiket dm_kalan --tahmin-kaydet            # 40 cells
python -m arac.dm_yil        # within-year DM, five years -> sonuclar/doygunluk_ozet_dm_yil.csv
python run_doygunluk.py --ozet
```

`sonuclar/doygunluk_ozet_dm.csv` (45 paired tests between the two ends of the learning
curve) is computed by `pv10/ozet_sonrasi.py:uc_dm` from the `dm` predictions. **No
script in this repository calls that function and writes the file**; the driver that
produced it was not retained. This is a known gap.

**Multiple-testing correction (robustness, added after the results).**
`python -m arac.coklu_test` applies Holm and Benjamini-Hochberg corrections to the
existing p-values without recomputing them → `sonuclar/coklu_test_ozet.csv`,
`coklu_test_iddialar.csv`, `coklu_test_detay.csv`. This analysis was not pre-registered.

### 6. Figures

| File | Command | Source |
|---|---|---|
| `sekiller/F1_ogrenme_egrileri.{pdf,png}` (learning curves) | `python -m sekiller.sekil_uret` | `sonuclar/doygunluk.csv` |
| `sekiller/F2_rastgele_kfold_A.{pdf,png}` (effect A of shuffled splitting) | `python -m sekiller.sekil_uret` | `sonuclar/ablasyon_belirsizlik_dm_*_dm.csv` |
| `sekiller/F1_veri/egri_havuz.csv`, `egri_model.csv` (plotted values of the learning-curve figure) | `python -m sekiller.f1_veri` | `sonuclar/doygunluk.csv` |

Both scripts embed the manuscript values and refuse to write output if any of them
fails to match.

### 7. Supplementary material

| Item | File | Built from |
|---|---|---|
| S1 Feature definitions | `ek/S1_oznitelikler.md` | `pv10/features.py`, `pv10/config.py` |
| S2 Algorithms, settings, model subsets, nondeterminism | `ek/S2_algoritmalar.md` | `pv10/models.py`, `sonuclar/nondeterminizm_olcum*.csv` |
| S3 DKASC quality-control rules | `ek/S3_dkasc_kalite_kurallari.md` | `dokumanlar/dkasc-kalite-kurallari.md`, `faz-notlari/dkasc-replikasyon.md` |
| S4 Invariant gate | `ek/S4_invaryant_kapisi.md` | `pv10/dogrulama.py`, `python run_doygunluk.py --dogrula` |
| S5 Cell-level decomposition | `ek/S5_ayristirma_hucre.md` | `sonuclar/ablasyon_belirsizlik_dm_*_{dm,bootstrap}.csv` |
| S6 Deviations from the pre-registered plan | `ek/S6_on_kayit_sapmalari.md` | git history, `dokumanlar/` |
| S7 Literature-audit protocol and coding | not in this repository | — |

The phase handover notes in `faz-notlari/` record commit hashes, run statistics and
gate results for each phase. The notes for Phases 2 and 3 were compiled
retrospectively and make no pre-registration claim.

## Related work

This study builds on a previous single-year, four-site comparison of eleven machine
learning algorithms by the same authors. Preliminary findings were reported there; the
multi-year leakage ablation and ranking-stability analysis are new to this work.

## Data source and licence

Radiation and PV data: **Photovoltaic Geographical Information System (PVGIS)**,
European Commission Joint Research Centre — <https://re.jrc.ec.europa.eu/pvg_tools/en/>

Code in this repository is released under the MIT Licence.