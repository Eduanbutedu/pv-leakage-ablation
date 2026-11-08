# Evaluation choices outweigh algorithm choice in day-ahead photovoltaic power forecasting: a ten-year, six-site leakage ablation with measured-data replication

**Hasan Canbaz, Elif Parlar, Shahaboddin Daneshvar** — Hasan Kalyoncu University

*Manuscript submitted to Solar (MDPI), 2026.*

Code, pre-registration documents and results for a ten-year (2014-2023), six-site
study quantifying how common evaluation choices inflate reported skill in
machine-learning photovoltaic power forecasting, replicated on measured data from
three arrays at the DKA Solar Centre, Alice Springs. The aim is not a new forecasting
model: it is to measure how much leakage, splitting strategy, test-year choice and
training volume move reported performance, relative to the choice of algorithm.

This repository extends an earlier single-year, four-site study by the same authors
(see *Related work* below) from one year to ten and from four sites to six, and adds a
controlled leakage ablation, a model-ranking stability analysis, a training-volume
saturation analysis and a measured-data replication.

The state submitted with the manuscript is tagged `v1.0-submission`.

## Contents

| Path | What it holds |
|---|---|
| `pv10/` | experiment package: constants (`config.py`, the only place constants are defined), features, models, metrics, split logic, grids, experiment invariants, Phase 4 summaries |
| `pvgis_pipeline.py`, `dkasc_pipeline.py` | regenerate the PVGIS and DKASC datasets and verify them against the frozen hashes |
| `run_smoke.py` | single-split sanity run over the full feature pipeline |
| `run_ablasyon.py` | leakage ablation grid (Phase 2 and its DKASC replication) |
| `run_siralama.py` | ranking stability across test years (Phase 3) |
| `run_doygunluk.py` | training-volume saturation (Phase 4), invariant gate, summaries |
| `arac/` | post-processing and diagnostic scripts. They train no model and run no experiment: they read saved predictions or result CSVs. Some of them do produce manuscript numbers (`ablasyon_dm.py`, `dm_yil.py`, `uc_dm.py`, `dm_matris.py`, `coklu_test.py`, `tanimlayici.py`); the others are diagnostics only (`nondeterminizm*.py`, `regresyon_kiyas.py`, `csv_karsilastir.py`, `oznitelik_regresyon.py`, `dizi_tarama.py`). `tablolari_uret.py` checks the manuscript tables against the CSVs |
| `sekiller/` | figure scripts, figures and the plotted data |
| `dokumanlar/` | pre-registration and rule documents (see below) |
| `ek/` | supplementary material S1-S6 |
| `faz-notlari/` | phase handover notes: commit hashes, run statistics, gate results |
| `sonuclar/*.csv` | every experiment log and summary table (committed); saved prediction vectors under `sonuclar/tahminler/` are not committed |

Code identifiers, comments and the phase notes are in Turkish; this README and the
supplementary material are in English.

## Pre-registration documents

The documents below fixed rules or readings before the data or results they govern
existed. The first commit of each is the evidence; `git log -- <file>` shows every
later change, and each later change is marked as such inside the document and listed
in supplementary S6 (deviations from the pre-registered plan).

| Document | Fixes | First commit | Date (UTC+3) | Before |
|---|---|---|---|---|
| `dokumanlar/dkasc-kalite-kurallari.md` | DKASC quality-control rules and stop thresholds | `6da9109649b83075bd1eeed2988ab8dfd10b1fec` | 2026-08-07 07:42 | `dkasc_pipeline.py` (first commit `1cb311c`, 2026-08-08 01:47) |
| `dokumanlar/varyant-dm-yorum-kurali.md` | how the Phase 2 uncertainty measurement (paired DM, bootstrap, night identity) is read | `397e3628c9a68a2e94278a3479a502c9949cb69c` | 2026-08-08 21:41 | first uncertainty tables (`690f03a`, 2026-08-08 23:12) |
| `pv10/ozet.py` | Phase 4 summary tables and metrics | `13c6ee84f6eb7a83319de0f8f61f9caeb94fbf93` | 2026-07-31 06:05 | Phase 4 grid results (`0c8614b`, 2026-08-02 01:52); file unchanged since |
| `arac/ornek_gunler.py` | example-day selection rule | `568221d7e7b17f0c56203eddce563079a0080149` | 2026-10-17 21:19 | selected days (`cdce2c9`) and series (`58d95eb`) |

Not pre-registration documents, listed so that the distinction is explicit:

- `dokumanlar/varyant-test-taksonomisi.md` (first commit `690f03a6c383b6cee97c2b37b5bea382d06e3ade`)
  was committed together with the first uncertainty results it discusses.
- `dokumanlar/arastirma-baglami.md` (first commit `240677460052adb94173963ebe0c1f540d5be559`)
  was the research-context note. It and `CLAUDE.md` (local working notes) are no
  longer tracked from `v1.0-submission` on; both remain readable in the history.
  Some phase notes and pre-registration documents refer to these two files; read them
  from the history, e.g. `git show 6851c93:CLAUDE.md`.
- `faz-notlari/faz-2.md` and `faz-3.md` were compiled retrospectively and carry no
  pre-registration claim. Phases 1-3 were committed together with their results, so
  there is no file-level evidence that their setup was fixed before results were seen;
  this gap is the reason for the pre-registration discipline of the DKASC arm.
- Analyses added after the results were seen are marked as such: `pv10/ozet_sonrasi.py`,
  `arac/dm_matris.py`, `arac/coklu_test.py`, and the rule 8a sensitivity run.

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
   over 1, 2, 3 and 5 years and all available history. A ten-year window is not
   possible: with the test year held out, at most nine years remain.
4. **Does the simulated-data result replicate on measured data?** The ablation is
   repeated on three measured arrays at DKASC, Alice Springs, with quality-control
   rules fixed before the data were processed.

## Data

Neither dataset is redistributed. Both are regenerated from the original sources by
the pipelines in this repository and verified against a frozen hash
(`sha256` of the Parquet bytes, first 16 hex digits). A mismatch means the dataset
differs and results will not reproduce exactly.

### PVGIS-SARAH3 (simulated)

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
525,888 in total). Frozen version: `sha256_16 = f722a717bac502c2`.

**PVGIS output is simulated, not measured.** PV power is computed by PVGIS from
irradiance and meteorological inputs using a module performance model. This study
therefore treats the dataset as a controlled, internally consistent simulation
environment rather than ground truth — which is what a controlled ablation requires,
since the underlying generating process is known. The measured-data replication below
tests whether the leakage effects it shows carry over.

### DKASC Alice Springs (measured)

Six yearly files, 2017-2022 ("All Individual Technologies (yearly data set with
weather data)", 5-minute resolution) from the DKA Solar Centre,
<https://dkasolarcentre.com.au/>. Files accessed on 4 August 2026 (2018, 2020, 2022)
and 7 August 2026 (2017, 2019, 2021), as recorded in
`dokumanlar/dkasc-kalite-kurallari.md`. 2017 is used for training only; test years
are 2018-2022. Three arrays are used:

| Array (`--dizi`) | System | Technology | Capacity | Frozen `sha256_16` |
|---|---|---|---|---|
| `m6b` (main) | 13 | Trina TSM-175DC01, mono-Si | 5.25 kWp | `f7f644df5e0d1618` |
| `m15a` | 23 | Calyxo CX-50, CdTe thin film | 5.4 kWp | `be6dd9e1a15dcc61` |
| `m3a` | 14 | Kyocera KD135GX-LP, poly-Si | 5.4 kWp | `9c1c08bf08a9b84b` |

The second and third arrays were chosen on data quality alone, after the M6_B results
had been seen (decision 6 in the rules document; screening evidence in
`sonuclar/dkasc_dizi_tarama.csv`). M15_A and M3_A tripped stop thresholds of the
pre-registered rules and were run by the authors' recorded decision; see the rules
document and supplementary S3/S6.

The expected hashes are in `pv10/config.py` (`VERI_SHA16`, `DKASC_DIZILER[...]["sha16"]`).
Regeneration commands are under *Reproducing the paper*, step 2.

## Environment

Results were produced on Windows 11 with Python 3.14.6 and the pinned versions in
`requirements.txt`:

| Package | Version |
|---|---|
| pandas | 3.0.5 |
| numpy | 2.5.1 |
| scikit-learn | 1.9.0 |
| scipy | 1.18.0 |
| pyarrow | 22.0.0 |
| matplotlib | 3.11.2 |
| requests | 2.34.2 |

- **Threads.** `OMP_NUM_THREADS = OPENBLAS_NUM_THREADS = MKL_NUM_THREADS = 8` is set at
  the start of every run (`config.OMP_THREAD_SAYISI`). Hist Gradient Boosting uses
  OpenMP; a different thread count changes the summation order and loses bit-level
  reproducibility.
- **Seeds.** Model seed 42; Phase 4 subsampling seeds 11, 22 and 33. Hyperparameters
  are fixed a priori in `pv10/models.py` and never tuned on validation or test
  partitions.
- **Measured nondeterminism in Random Forest and Extra Trees.** Repeated fits of the
  same cell give different prediction vectors (within-process parallel tree
  aggregation; measured in `sonuclar/nondeterminizm_olcum.csv` and confirmed in
  `nondeterminizm_olcum_dogrulama.csv`, with Neural Network as a deterministic
  control). The effect on logged metrics is a relative difference below 1.5e-15: 1-2
  units in the last place for directly computed metrics, up to 8 for the derived
  `skill` field. No reported digit is affected. Everything downstream of the fitted
  predictions (DM tests, summaries) is deterministic.
- **pyarrow 22.0.0** rather than the latest release, because Windows Smart App
  Control blocks the `arrow.dll` shipped with 25.0.0 on the machine used for the runs.
  The pin affects only Parquet I/O. The frozen dataset is byte-identical under both
  versions, the five experiment invariants pass 18/18 checks under 22.0.0, and the
  reference metrics they compare against reproduce to the same digits as under 25.0.0.
  The Phase 4 main grid, wide run and 2022 run were produced with 25.0.0; later runs
  with 22.0.0.

## Licence

Code in this repository is released under the MIT Licence (`LICENSE`). PVGIS and DKASC
data are subject to their providers' terms and are not redistributed here.

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
| DKASC Alice Springs, M6_B (system 13), 2017-2022 | `python dkasc_pipeline.py dogrula ham/dkasc` then `python dkasc_pipeline.py duzenle ham/dkasc --dizi m6b` | `veri/dkasc_m6b.parquet` | `veri/dkasc_veri_surumu.txt` | `f7f644df5e0d1618` |
| DKASC Alice Springs, M15_A (system 23), 2017-2022 | `python dkasc_pipeline.py duzenle ham/dkasc --dizi m15a` | `veri/dkasc_m15a.parquet` | `veri/dkasc_m15a_veri_surumu.txt` | `be6dd9e1a15dcc61` |
| DKASC Alice Springs, M3_A (system 14), 2017-2022 | `python dkasc_pipeline.py duzenle ham/dkasc --dizi m3a` | `veri/dkasc_m3a.parquet` | `veri/dkasc_m3a_veri_surumu.txt` | `9c1c08bf08a9b84b` |

The DKASC raw files are not downloadable by script; the same six files serve all
three arrays. Obtain the six yearly Alice Springs files from <https://dkasolarcentre.com.au/> and place them as
`ham/dkasc/Alice_Springs_2017.csv` … `Alice_Springs_2022.csv` (about 1.2 GB in
total). The quality-control rules applied to them were fixed before any row was
processed: `dokumanlar/dkasc-kalite-kurallari.md`.

To check a hash independently of the pipelines:

```bash
python -c "import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest()[:16])" veri/pvgis_10yil.parquet
```

The expected values are also in `pv10/config.py` (`VERI_SHA16`, `DKASC_DIZILER[...]["sha16"]`).

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

Random Forest and Extra Trees differ between runs by a relative difference
below 1.5e-15 (1-2 units in the last place, up to 8 for the derived `skill` field; see
*Environment*). No reported figure uses them except the ten-model pool, and no
reported digit is affected.

### 5. Tables

| Table | Content | Command | Source file(s) |
|---|---|---|---|
| 1 | Literature audit, 27 studies | none: manual coding | Supplementary S7 (not in this repository) |
| 2 | Descriptive statistics of the evaluated population (N, P/capacity mean ± SD, skewness, mean G(i)) | `python -m arac.tanimlayici` | `sonuclar/tanimlayici_istatistik.csv` |
| 3 | The six configurations | none: definitions | leakage variant registry in `pv10/config.py` |
| 4 | Mapping to the Kapoor and Narayanan (2023) taxonomy | none: descriptive | — |
| 5 | Ablation, simulated data | `python run_ablasyon.py` | `sonuclar/ablasyon.csv` |
| 6 | Inflation ratios: PVGIS full, PVGIS reduced, three DKASC arrays | `python run_ablasyon.py` · `python run_ablasyon.py --set dkasc --etiket pvgis_indirgenmis` · `python run_ablasyon.py --set dkasc --veri veri/dkasc_<array>.parquet --yillar 2018,2019,2020,2021,2022 --etiket dkasc` (M6_B; `dkasc_m15a`, `dkasc_m3a` for the others) | `sonuclar/ablasyon.csv`, `ablasyon_pvgis_indirgenmis.csv`, `ablasyon_dkasc.csv`, `ablasyon_dkasc_m15a.csv`, `ablasyon_dkasc_m3a.csv` |
| 7 | Population-free effect A of shuffled splitting | see *Phase 2 uncertainty* below | `sonuclar/ablasyon_belirsizlik_dm_{ana,pvgis_indirgenmis,dkasc,dkasc_m15a,dkasc_m3a}_dm.csv` (`A_model`) |
| 8 | Learning curves | `python run_doygunluk.py` (summary written automatically; `--ozet` rewrites it from the logs) | `sonuclar/doygunluk.csv` → `sonuclar/doygunluk_ozet_egri.csv` |
| 9 | Variance decomposition | as Table 8 | `sonuclar/doygunluk_ozet_varyans.csv` |

**Verifying Tables 2 and 5-9 against the manuscript.** `python -m arac.tablolari_uret` recomputes
every value in Tables 2 and 5-9 from the CSVs above and compares it, at the precision printed
in the manuscript, with the value in the manuscript. It lists every value that does not
match and exits with status 1 if there is one. Current state: 119 of 119 match (Table 2 descriptive statistics included; Tables 6-7 include the CdTe and poly-Si arrays; Table 7's ratio is the range over the three measured arrays).

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

M15_A and M3_A follow the M6_B pattern with `--veri veri/dkasc_m15a.parquet` /
`veri/dkasc_m3a.parquet`, labels `dkasc_m15a`, `dm_dkasc_m15a`, `dkasc_m3a`,
`dm_dkasc_m3a`, and `--kapasite 5400` (the capacity is taken from the data;
`--kapasite` only checks it). The post-registration rule 8a sensitivity run on M6_B
adds `--kural-8a` under the labels `dkasc_k8a` and `dm_dkasc_k8a`; the main results are
without rule 8a.

The three labels and what each one writes:

| Label | Data / features | Grid log | Saved predictions | Uncertainty tables |
|---|---|---|---|---|
| `dm_ana` | PVGIS, full feature set, 2017-2023 | `sonuclar/ablasyon_dm_ana.csv` | `sonuclar/tahminler/ablasyon/dm_ana/` | `sonuclar/ablasyon_belirsizlik_dm_ana_*.csv` |
| `dm_pvgis_indirgenmis` | PVGIS, DKASC (reduced) feature set, 2017-2023 | `sonuclar/ablasyon_dm_pvgis_indirgenmis.csv` | `sonuclar/tahminler/ablasyon/dm_pvgis_indirgenmis/` | `sonuclar/ablasyon_belirsizlik_dm_pvgis_indirgenmis_*.csv` |
| `dm_dkasc` | DKASC, reduced feature set, 2018-2022 | `sonuclar/ablasyon_dm_dkasc.csv` | `sonuclar/tahminler/ablasyon/dm_dkasc/` | `sonuclar/ablasyon_belirsizlik_dm_dkasc_*.csv` |

`*` is `dm`, `bootstrap` and `gece_ozdeslik`. The re-run grid logs reproduce
`ablasyon.csv`, `ablasyon_pvgis_indirgenmis.csv` and `ablasyon_dkasc.csv` exactly
(likewise `ablasyon_dkasc_m15a.csv` and `ablasyon_dkasc_m3a.csv`, 810/810 fields). The interpretation rules were fixed
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
python -m arac.uc_dm         # learning-curve ends, 45 paired DM -> sonuclar/doygunluk_ozet_dm.csv
python -m arac.dm_yil        # within-year DM, five years -> sonuclar/doygunluk_ozet_dm_yil.csv
python -m arac.dm_matris     # all 45 pairs x five years, Holm within year -> sonuclar/dm_matris_havuz10.csv [post-pre-registration]
python run_doygunluk.py --ozet
```

`arac/uc_dm.py` and `arac/dm_yil.py` train nothing; they read the saved prediction
vectors and overwrite their output table. To check a committed table instead of
replacing it, write to a separate file and compare without tolerance:

```bash
python -m arac.uc_dm --cikti sonuclar/doygunluk_ozet_dm_dogrulama.csv \
    --referans sonuclar/doygunluk_ozet_dm.csv
python -m arac.dm_yil --cikti <scratch>.csv \
    --referans sonuclar/doygunluk_ozet_dm_yil.csv \
    --rapor sonuclar/doygunluk_ozet_dm_yil_kiyas.csv
```

Both scripts compare through `arac/csv_karsilastir.py`. It checks byte identity,
compares every field with `==` after round-trip parsing (pandas' default float parser
can hide a one-ULP difference), and runs a negative control on every call: an
untouched read and write must give zero differences, and a one-ULP change to a single
field must give exactly one. Current state: both tables reproduce byte for byte, with
630 of 630 fields identical for `doygunluk_ozet_dm.csv` and 285 of 285 for
`doygunluk_ozet_dm_yil.csv` (field-level report: `sonuclar/doygunluk_ozet_dm_yil_kiyas.csv`).
`doygunluk_ozet_dm.csv` was originally produced by a session script that was not
retained; `arac/uc_dm.py` replaces it.

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

Example days (`sekiller/F_ornek/ornek_gunler.csv`: observed power, `temiz` and
`eszaman` forecasts, Hist Gradient Boosting; PVGIS full feature set test year 2023
from `dm_ana`, DKASC test year 2022 from `dm_dkasc`) are chosen by a fixed rule that
was committed before any prediction file was read (`git log -- arac/ornek_gunler.py
sekiller/F_ornek` shows the order: rule, selected days, series):

```bash
python -m arac.ornek_gunler --sec    # rule -> sekiller/F_ornek/secilen_gunler.csv, saha_secimi.csv
python -m arac.ornek_gunler --seri   # predictions for the committed days -> ornek_gunler.csv
```

- A day is a local standard-time calendar day whose 24 hours are all in the
  experiment's test set, with irradiance present and (DKASC) no fault flag.
- Daily clearness: DKASC uses the standard clearness index Kt = ΣGHI / ΣG0, with G0
  the horizontal extraterrestrial irradiance. PVGIS has no horizontal global
  irradiance, so it uses ΣG(i) / ΣG0, named `egik_duzlem_berraklik_proxy`. This is
  a tilted-over-horizontal proxy, not a true Kt.
- PVGIS site: the site with the widest P90-P10 range of the proxy in 2023, ties
  broken by the `pvgis_pipeline.KONUMLAR` order. This picks Konya (0.834), because
  the three day types separate most clearly there. DKASC has a single site.
- Days: the day nearest the P90 (clear), P50 (partly cloudy) and P10 (overcast)
  value, ties broken by the earliest date.

rastgele_kfold is not in this figure: its test set consists of random hours, so it
gives no daily series.

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
learning algorithms by the same authors (accepted for publication, in press), whose
single test year was 2023. The multi-year leakage ablation, ranking-stability,
training-volume and measured-data analyses are new to this work.

## Data sources

- Radiation and PV data: **Photovoltaic Geographical Information System (PVGIS)**,
  European Commission Joint Research Centre — <https://re.jrc.ec.europa.eu/pvg_tools/en/>
- Measured PV and weather data: **DKA Solar Centre**, Alice Springs —
  <https://dkasolarcentre.com.au/>

## Citation

See `CITATION.cff`.
