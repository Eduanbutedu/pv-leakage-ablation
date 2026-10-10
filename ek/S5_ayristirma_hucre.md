# S5 — Cell-level decomposition (A / B / C / D)

Supplementary material. Narrative from `dokumanlar/varyant-test-taksonomisi.md`
and `dokumanlar/varyant-dm-yorum-kurali.md`; cell values read from
`sonuclar/ablasyon_belirsizlik_dm_{ana,pvgis_indirgenmis,dkasc}_dm.csv`.
No number in this file was produced for it.

---

## 1. Why a decomposition and not a test

The headline ratio for the **shuffled split** variant compares RMSE values
computed on two *different populations*. The clean arm is evaluated on the
test year only; the shuffled arm on a sample drawn at random from the whole
pool (`year ≤ test year`). If earlier years are systematically easier or
harder, the population difference can **mask** the real leakage effect — it
can even work in the opposite direction and produce a headline ratio near
zero.

The discriminating tool is not a test but **algebra**. The headline
difference splits exactly into three terms:

```
D  =  RMSE_v(full) − RMSE_c(full)
   =  [ RMSE_v(int) − RMSE_c(int) ]      ← A: MODEL effect, population FIXED
    + [ RMSE_v(full) − RMSE_v(int) ]     ← B: variant's population term
    − [ RMSE_c(full) − RMSE_c(int) ]     ← C: clean arm's population term
```

where *int* is the intersection of the two arms' test sets and *full* is
each arm's own complete daylight test set. The identity `A + B − C = D` is
exact; it follows from cancellation, not from estimation. The same logic as
the Class B night identity: where the relationship is exact, report the
decomposition, not a test.

**Intersection RMSE is not headline RMSE and is never presented as such.**

### Pre-registered reading rule

| Case | Reading |
|---|---|
| \|A\| large, \|B − C\| ≈ 0 | Leakage effect is real and passes through to the headline one-for-one. |
| \|A\| large, (B − C) opposite in sign and comparable in size | **POPULATION MASKING.** Shuffling genuinely produces leakage, but the reported metric hides it, because the population shift works the other way. |
| \|A\| ≈ 0, \|B − C\| large | The headline deviation is entirely compositional, not leakage. |
| \|A\| ≈ 0, \|B − C\| ≈ 0 | No demonstrable effect by any measure. |

All four were written down before `arac/ablasyon_dm.py` was ever run, when
none of the `ablasyon_belirsizlik_*` files existed.

### Test parameters (fixed before measurement)

| | |
|---|---|
| Significance | α = 0.05, two-sided |
| Loss | squared error |
| HAC correction | Newey–West / Bartlett, `h = 24` (lags 1 … 23) |
| Clustering | `time_utc` — same as Phase 3 and Phase 4 |
| Bootstrap | day block, 1000 replicates, seed = 42 |
| Pairing | `(konum, time_utc)` |
| Multiplicity | **no correction applied** |

Capacity normalisation: 1000 W for both PVGIS arms, 5250 W for DKASC.

---

## 2. Cell-level tables — shuffled split

One row per (test year × model). `resid.` is `|A + B − C − D|`, the
numerical closure of the identity.

### 2.1 PVGIS full

| Year | Model | A (W) | B (W) | C (W) | D (W) | resid. | A / cap (%) | p | sig. |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| 2017 | HGB | -9.565226 | 0.532867 | -2.942847 | -6.089512 | 0.0e+00 | -0.9565 | 5.41522e-23 | yes |
| 2017 | LR | -0.143864 | -0.355077 | -2.531250 | 2.032309 | 0.0e+00 | -0.0144 | 0.00476522 | yes |
| 2017 | PolyRidge | -1.946389 | 0.593240 | -2.735571 | 1.382422 | 2.2e-16 | -0.1946 | 2.60691e-06 | yes |
| 2018 | HGB | -7.425381 | 0.368253 | 1.120513 | -8.177641 | 0.0e+00 | -0.7425 | 3.64631e-17 | yes |
| 2018 | LR | -0.057929 | 0.600243 | 1.033835 | -0.491521 | 5.6e-17 | -0.0058 | 0.362713 | no |
| 2018 | PolyRidge | -2.032910 | 0.134807 | 1.393739 | -3.291841 | 0.0e+00 | -0.2033 | 6.13855e-07 | yes |
| 2019 | HGB | -6.318712 | -3.073374 | -3.691330 | -5.700756 | 0.0e+00 | -0.6319 | 2.26848e-17 | yes |
| 2019 | LR | -0.038919 | -1.694685 | -2.833770 | 1.100167 | 0.0e+00 | -0.0039 | 0.0826341 | no |
| 2019 | PolyRidge | -0.770118 | -3.046004 | -3.541196 | -0.274926 | 3.9e-16 | -0.0770 | 1.16125e-05 | yes |
| 2020 | HGB | -5.530799 | 0.507055 | 0.830758 | -5.854501 | 0.0e+00 | -0.5531 | 6.53532e-13 | yes |
| 2020 | LR | -0.037078 | -0.512963 | -1.115863 | 0.565821 | 0.0e+00 | -0.0037 | 0.364125 | no |
| 2020 | PolyRidge | -0.906278 | -0.011477 | 0.380106 | -1.297861 | 0.0e+00 | -0.0906 | 3.34503e-05 | yes |
| 2021 | HGB | -5.244497 | 0.785598 | -0.183888 | -4.275011 | 0.0e+00 | -0.5244 | 3.91001e-10 | yes |
| 2021 | LR | -0.019333 | 2.068406 | 0.574741 | 1.474332 | 0.0e+00 | -0.0019 | 0.327129 | no |
| 2021 | PolyRidge | -0.651715 | 1.103244 | 0.197349 | 0.254181 | 1.1e-16 | -0.0652 | 1.48364e-09 | yes |
| 2022 | HGB | -5.724063 | -3.326624 | -1.561484 | -7.489203 | 8.9e-16 | -0.5724 | 3.06251e-08 | yes |
| 2022 | LR | -0.026654 | -3.369401 | -1.607331 | -1.788723 | 0.0e+00 | -0.0027 | 0.403275 | no |
| 2022 | PolyRidge | -0.687410 | -3.350245 | -0.984176 | -3.053480 | 0.0e+00 | -0.0687 | 0.000377987 | yes |
| 2023 | HGB | -4.354738 | 7.285392 | 2.706398 | 0.224256 | 2.8e-17 | -0.4355 | 4.53643e-08 | yes |
| 2023 | LR | -0.025939 | 6.499256 | 1.682580 | 4.790737 | 8.9e-16 | -0.0026 | 0.207314 | no |
| 2023 | PolyRidge | -0.621278 | 7.688010 | 2.868081 | 4.198651 | 0.0e+00 | -0.0621 | 2.502e-07 | yes |

### 2.2 PVGIS reduced

| Year | Model | A (W) | B (W) | C (W) | D (W) | resid. | A / cap (%) | p | sig. |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| 2017 | HGB | -9.313664 | 0.302224 | -2.590753 | -6.420687 | 0.0e+00 | -0.9314 | 7.038e-27 | yes |
| 2017 | LR | -0.134169 | -0.329223 | -2.508421 | 2.045029 | 0.0e+00 | -0.0134 | 0.0030559 | yes |
| 2017 | PolyRidge | -1.261284 | 0.584287 | -2.791115 | 2.114118 | 4.4e-16 | -0.1261 | 1.80996e-09 | yes |
| 2018 | HGB | -7.680627 | 0.320708 | 0.406433 | -7.766351 | 0.0e+00 | -0.7681 | 1.04849e-20 | yes |
| 2018 | LR | -0.057650 | 0.615198 | 1.011089 | -0.453541 | 1.1e-16 | -0.0058 | 0.358841 | no |
| 2018 | PolyRidge | -1.249162 | 0.033163 | 0.691362 | -1.907361 | 2.2e-16 | -0.1249 | 5.24129e-07 | yes |
| 2019 | HGB | -5.824899 | -3.023950 | -3.826932 | -5.021916 | 0.0e+00 | -0.5825 | 8.32453e-12 | yes |
| 2019 | LR | -0.037248 | -1.698100 | -2.841496 | 1.106148 | 2.2e-16 | -0.0037 | 0.087013 | no |
| 2019 | PolyRidge | -0.656333 | -3.113657 | -3.517764 | -0.252226 | 0.0e+00 | -0.0656 | 3.42974e-05 | yes |
| 2020 | HGB | -5.884032 | 0.885008 | 0.905513 | -5.904537 | 0.0e+00 | -0.5884 | 1.73298e-10 | yes |
| 2020 | LR | -0.043467 | -0.527165 | -1.150003 | 0.579371 | 0.0e+00 | -0.0043 | 0.26109 | no |
| 2020 | PolyRidge | -0.822276 | 0.079296 | 0.399140 | -1.142120 | 0.0e+00 | -0.0822 | 7.45629e-05 | yes |
| 2021 | HGB | -4.343891 | 1.009754 | 0.744118 | -4.078255 | 0.0e+00 | -0.4344 | 8.83981e-12 | yes |
| 2021 | LR | -0.014494 | 2.068214 | 0.574578 | 1.479142 | 0.0e+00 | -0.0014 | 0.393419 | no |
| 2021 | PolyRidge | -0.571584 | 1.310883 | 0.279257 | 0.460042 | 0.0e+00 | -0.0572 | 1.15678e-08 | yes |
| 2022 | HGB | -5.644573 | -3.524130 | -1.781106 | -7.387597 | 0.0e+00 | -0.5645 | 7.49941e-07 | yes |
| 2022 | LR | -0.027864 | -3.385152 | -1.624345 | -1.788671 | 0.0e+00 | -0.0028 | 0.405235 | no |
| 2022 | PolyRidge | -0.498808 | -3.282620 | -0.855488 | -2.925941 | 0.0e+00 | -0.0499 | 0.00263797 | yes |
| 2023 | HGB | -4.073750 | 8.013960 | 3.501241 | 0.438968 | 0.0e+00 | -0.4074 | 3.43397e-09 | yes |
| 2023 | LR | -0.018955 | 6.457356 | 1.669090 | 4.769311 | 0.0e+00 | -0.0019 | 0.327673 | no |
| 2023 | PolyRidge | -0.540410 | 7.885246 | 2.985427 | 4.359409 | 0.0e+00 | -0.0540 | 1.30935e-06 | yes |

### 2.3 DKASC

| Year | Model | A (W) | B (W) | C (W) | D (W) | resid. | A / cap (%) | p | sig. |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| 2018 | HGB | -154.423372 | 15.991066 | -3.062641 | -135.369665 | 0.0e+00 | -2.9414 | 8.48197e-12 | yes |
| 2018 | LR | -3.659836 | 13.418016 | -10.618538 | 20.376717 | 0.0e+00 | -0.0697 | 0.17078 | no |
| 2018 | PolyRidge | -42.552955 | 23.574392 | -5.106125 | -13.872438 | 7.1e-15 | -0.8105 | 0.000449031 | yes |
| 2019 | HGB | -100.031167 | 86.056778 | 2.878505 | -16.852893 | 0.0e+00 | -1.9054 | 1.7608e-08 | yes |
| 2019 | LR | -3.303401 | 110.114134 | 0.868362 | 105.942371 | 1.4e-14 | -0.0629 | 0.0370241 | yes |
| 2019 | PolyRidge | -31.130778 | 105.080131 | 3.589091 | 70.360263 | 1.4e-14 | -0.5930 | 1.51599e-05 | yes |
| 2020 | HGB | -103.880174 | -23.258487 | -10.358387 | -116.780274 | 0.0e+00 | -1.9787 | 0.000131955 | yes |
| 2020 | LR | -2.251745 | -16.709093 | -3.135021 | -15.825818 | 0.0e+00 | -0.0429 | 0.277162 | no |
| 2020 | PolyRidge | -21.696739 | -13.925689 | 4.393490 | -40.015917 | 0.0e+00 | -0.4133 | 0.0326078 | yes |
| 2021 | HGB | -152.305970 | -44.942192 | -41.347066 | -155.901096 | 0.0e+00 | -2.9011 | 0.000209454 | yes |
| 2021 | LR | -2.324688 | -81.609195 | -34.606148 | -49.327736 | 0.0e+00 | -0.0443 | 0.0451404 | yes |
| 2021 | PolyRidge | -31.846223 | -85.754098 | -44.633322 | -72.966999 | 0.0e+00 | -0.6066 | 0.00685893 | yes |
| 2022 | HGB | -122.558555 | -36.126385 | 47.659812 | -206.344752 | 0.0e+00 | -2.3344 | 6.45262e-05 | yes |
| 2022 | LR | -2.285260 | -53.211992 | 30.853857 | -86.351109 | 0.0e+00 | -0.0435 | 0.0122027 | yes |
| 2022 | PolyRidge | -33.373172 | -45.880571 | 32.181166 | -111.434908 | 1.4e-14 | -0.6357 | 0.00986469 | yes |

---

## 3. What the cells show

### Model-level means (W)

| Source | Model | **A** (pop. fixed) | A / cap. | (B−C) pop. | **D** (headline) | D / cap. | A sig. | sign REVERSED |
|---|---|---|---|---|---|---|---|---|
| PVGIS full | Linear Regression | **−0.050** | −0.0050 % | +1.148 | **+1.098** | +0.1098 % | 1/7 | **5/7** |
| PVGIS full | Polynomial Ridge | −1.088 | −0.1088 % | +0.790 | −0.298 | −0.0298 % | 7/7 | 3/7 |
| PVGIS full | Hist Gradient Boosting | −6.309 | −0.6309 % | +0.972 | −5.337 | −0.5337 % | 7/7 | 1/7 |
| PVGIS reduced | Linear Regression | −0.048 | −0.0048 % | +1.153 | +1.105 | +0.1105 % | 1/7 | 5/7 |
| PVGIS reduced | Polynomial Ridge | −0.800 | −0.0800 % | +0.901 | +0.101 | +0.0101 % | 7/7 | 3/7 |
| PVGIS reduced | Hist Gradient Boosting | −6.109 | −0.6109 % | +0.946 | −5.163 | −0.5163 % | 7/7 | 1/7 |
| DKASC | Linear Regression | −2.765 | −0.0527 % | −2.272 | −5.037 | −0.0959 % | 3/5 | 2/5 |
| DKASC | Polynomial Ridge | −32.120 | −0.6118 % | −1.466 | −33.586 | −0.6397 % | 5/5 | 1/5 |
| DKASC | Hist Gradient Boosting | **−126.640** | **−2.4122 %** | +0.390 | −126.250 | −2.4048 % | 5/5 | 0/5 |

### The cleanest single cell — PVGIS 2023, Hist Gradient Boosting

```
A  (model effect, same rows)      = -4.354738 W   p = 4.5e-08
(B - C) population term           = +4.578994 W
D  (reported headline difference) = +0.224256 W
```

Shuffling improves the model by **4.35 W** and that is unambiguously
significant — yet the reported number says a **0.22 W deterioration**. The
population term swallows the effect and flips its sign.

### Counts

| Source | A significant | A sig. **and** bootstrap CI contains zero | A sig. **and** sign reversed |
|---|---|---|---|
| PVGIS full | 15/21 | **10** | **5** |
| PVGIS reduced | 15/21 | **10** | **5** |
| DKASC | 13/15 | 4 | 2 |

**In PVGIS, 10 of 21 cells carry a demonstrable leakage effect that
disappears from the headline metric.** In DKASC it is 4 of 15. Counting
cells where the headline *sign* is opposite to the real effect: **9/21 in
PVGIS, 3/15 in DKASC.**

---

## 4. Two readings the decomposition changes

### 4.1 Quantitative — the real effect is larger in DKASC

With the population fixed (`A`, as % of capacity):

| Model | PVGIS full | DKASC | Ratio |
|---|---|---|---|
| Hist Gradient Boosting | −0.6309 % | −2.4122 % | **3.82** |
| Polynomial Ridge | −0.1088 % | −0.6118 % | 5.62 |
| Linear Regression | −0.0050 % | −0.0527 % | 10.54 |

**The headline number is HGB's 3.82.** The other two ratios are reported but
carry no claim: both numerators are very close to zero (order 0.005 % and
0.05 % of capacity), so the ratio is volatile — a small shift in the
numerator moves it a great deal. In LR the effect is significant in only 1
of 7 cells. HGB is significant 7/7, 7/7 and 5/5 and has the largest effect.

### 4.2 Qualitative — this is the actual finding

Ratio of the population term to the model effect, `|B−C| / |A|`:

| Model | PVGIS full | PVGIS reduced | DKASC | **PVGIS / DKASC** |
|---|---|---|---|---|
| Hist Gradient Boosting | 0.1540 | 0.1549 | **0.0031** | **50.0** |
| Linear Regression | 22.9697 | 24.1746 | 0.8218 | **28.0** |
| Polynomial Ridge | 0.7265 | 1.1261 | 0.0456 | **15.9** |

In all three models the population term carries **16–50 times** more weight
in PVGIS than in DKASC. In PVGIS it is comparable to the effect — larger
than it for LR and Polynomial Ridge — so it largely cancels the effect in
the headline. In DKASC it is one to two orders of magnitude smaller, so the
effect passes through almost intact.

So "simulated data understates the effect" is an incomplete summary. The
correct statement: **simulated data corrupts the effect's measurability.**
What is problematic is not the presence of leakage but its *visibility* in
the reported metric. This is exactly why validating leakage control on
simulated data is insufficient: the effect is there, the metric does not
show it.

### 4.3 The memorisation hypothesis, cleared of population difference

Pre-registered in the DKASC replication: if shuffling works on real data
because series-specific noise is **memorised**, the gain should be larger
for a flexible model (HGB) than for a rigid one (LR). On the full sets this
held (LR −0.0080 / −0.0080 / −0.0087; HGB +0.0387 / +0.0374 / +0.2085).

On the intersection, with the population fixed, the ordering is the same in
all three sources and DKASC's HGB effect is **3.82×** PVGIS's.
**The hypothesis is confirmed independently of population difference** — the
model breakdown on the full sets is not a composition artefact.

---

## 5. Worst case — the headline is sound

The **worst case** variant carries four interventions at once
(contemporaneous + shuffled split + night + global scaling), so it has both
a Class C and a Class B component. In the decomposition the mask is **fixed
to daylight on both sides**, so `D` here is *not* the logged headline
difference; the remainder is carried in a separate `sinifB_payi` column and
every row is labelled by `manset_esdeger`.

Full attribution of the logged headline difference (cell means, W):

| Source | RMSE clean | RMSE worst case | **D (log)** | A (model) | (B−C) pop. | Class B (night) | A share | pop. share | B share |
|---|---|---|---|---|---|---|---|---|---|
| PVGIS full | 138.146780 | 4.613977 | **−133.532803** | **−132.373740** | +0.572642 | −1.731705 | **99.13 %** | **−0.43 %** | 1.30 % |
| PVGIS reduced | 138.206410 | 6.765264 | **−131.441146** | −129.286093 | +0.619851 | −2.774903 | 98.36 % | −0.47 % | 2.11 % |
| DKASC | 554.005025 | 116.643961 | **−437.361064** | −461.433496 | +71.319291 | −47.246859 | **105.50 %** | **−16.31 %** | 10.80 % |

`A + (B−C) + ClassB = D` closes **exactly** in all three sources (check
0.000000).

| Source | \|B−C\| / \|A\| median | A sig. | A and D **sign reversed** |
|---|---|---|---|
| PVGIS full | **0.0095** | **21/21** | **0/21** |
| PVGIS reduced | 0.0097 | 21/21 | **0/21** |
| DKASC | **0.1654** | **15/15** | **0/15** |

**No masking in any cell.** Unlike the shuffled split, the worst case's
population term is nowhere large enough to flip a sign — the model effect is
two orders of magnitude bigger.

Population-cleared counterpart of the ratio (on the intersection, in
daylight, `RMSE_worstcase / RMSE_clean`, cell means):

| Source | headline ratio | headline change | **cleared ratio** | **cleared change** |
|---|---|---|---|---|
| PVGIS full | 0.033115 | **−96.69 %** | 0.044977 | **−95.50 %** |
| PVGIS reduced | 0.048798 | −95.12 % | 0.067638 | −93.24 % |
| DKASC | 0.217019 | −78.30 % | 0.172974 | −82.70 % |

**The −96.66 % is not a population artefact.** Cleared of population it
retreats to −95.50 %, a deviation of **1.19 points** — four parts per
thousand of the headline difference in the PVGIS arm. In DKASC the direction
**reverses**: the headline (−78.30 %) *understates* the real effect
(−82.70 %), because there the population term (+71.3 W) and the Class B
share (−47.2 W) do not cancel.

**Counter-note:** in DKASC the components are an order of magnitude larger
than in PVGIS (population share −16.31 %, Class B share 10.80 %). For the
worst case the headline is safe, but that is a **source-dependent**
observation, not a general one — it could not have been assumed without
decomposing.

### 5.1 Cell-level tables — worst case

Reminder: with the mask fixed to daylight on both sides, `D` in these tables
is the daylight-equivalent difference, not the logged headline.

#### PVGIS full

| Year | Model | A (W) | B (W) | C (W) | D (W) | resid. | A / cap (%) | p | sig. |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| 2017 | HGB | -135.066142 | -0.018805 | -2.942847 | -132.142100 | 0.0e+00 | -13.5066 | 8.46794e-93 | yes |
| 2017 | LR | -129.273408 | -0.128209 | -2.531250 | -126.870366 | 0.0e+00 | -12.9273 | 8.21753e-94 | yes |
| 2017 | PolyRidge | -132.255155 | -0.112858 | -2.735571 | -129.632442 | 0.0e+00 | -13.2255 | 2.75738e-85 | yes |
| 2018 | HGB | -134.876247 | -0.054406 | 1.120513 | -136.051166 | 0.0e+00 | -13.4876 | 9.44942e-87 | yes |
| 2018 | LR | -129.335517 | -0.207439 | 1.033835 | -130.576791 | 0.0e+00 | -12.9336 | 5.93041e-95 | yes |
| 2018 | PolyRidge | -133.858561 | 0.152501 | 1.393739 | -135.099799 | 0.0e+00 | -13.3859 | 1.51262e-88 | yes |
| 2019 | HGB | -137.947166 | 0.024317 | -3.691330 | -134.231519 | 2.8e-14 | -13.7947 | 4.23314e-69 | yes |
| 2019 | LR | -132.287569 | 0.056291 | -2.833770 | -129.397508 | 0.0e+00 | -13.2288 | 1.96177e-83 | yes |
| 2019 | PolyRidge | -136.034589 | 0.187784 | -3.541196 | -132.305609 | 2.8e-14 | -13.6035 | 1.64817e-69 | yes |
| 2020 | HGB | -133.112422 | 0.041041 | 0.830758 | -133.902139 | 0.0e+00 | -13.3112 | 4.25504e-70 | yes |
| 2020 | LR | -130.091112 | -0.072540 | -1.115863 | -129.047789 | 2.8e-14 | -13.0091 | 6.7084e-77 | yes |
| 2020 | PolyRidge | -131.933925 | 0.127528 | 0.380106 | -132.186503 | 2.8e-14 | -13.1934 | 3.61283e-72 | yes |
| 2021 | HGB | -134.326102 | -0.110245 | -0.183888 | -134.252460 | 2.8e-14 | -13.4326 | 5.02836e-54 | yes |
| 2021 | LR | -129.246215 | 0.304071 | 0.574741 | -129.516885 | 2.8e-14 | -12.9246 | 2.26365e-58 | yes |
| 2021 | PolyRidge | -132.634366 | 0.199115 | 0.197349 | -132.632600 | 0.0e+00 | -13.2634 | 2.65036e-56 | yes |
| 2022 | HGB | -138.847337 | -0.091322 | -1.561484 | -137.377176 | 0.0e+00 | -13.8847 | 7.35478e-50 | yes |
| 2022 | LR | -133.280982 | -0.336829 | -1.607331 | -132.010479 | 0.0e+00 | -13.3281 | 1.63735e-54 | yes |
| 2022 | PolyRidge | -136.528819 | -0.093147 | -0.984176 | -135.637790 | 0.0e+00 | -13.6529 | 2.0907e-53 | yes |
| 2023 | HGB | -127.799580 | 0.002168 | 2.706398 | -130.503810 | 2.8e-14 | -12.7800 | 2.04198e-49 | yes |
| 2023 | LR | -125.207520 | 0.920092 | 1.682580 | -125.970008 | 0.0e+00 | -12.5208 | 1.2343e-57 | yes |
| 2023 | PolyRidge | -125.905810 | 0.295758 | 2.868081 | -128.478133 | 0.0e+00 | -12.5906 | 4.88791e-47 | yes |

#### PVGIS reduced

| Year | Model | A (W) | B (W) | C (W) | D (W) | resid. | A / cap (%) | p | sig. |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| 2017 | HGB | -130.982510 | 0.177079 | -2.590753 | -128.214677 | 0.0e+00 | -13.0983 | 8.95992e-94 | yes |
| 2017 | LR | -128.283666 | -0.145372 | -2.508421 | -125.920617 | 0.0e+00 | -12.8284 | 2.44718e-93 | yes |
| 2017 | PolyRidge | -128.202352 | 0.158298 | -2.791115 | -125.252939 | 1.4e-14 | -12.8202 | 1.09695e-85 | yes |
| 2018 | HGB | -131.054781 | 0.020921 | 0.406433 | -131.440292 | 0.0e+00 | -13.1055 | 1.04664e-86 | yes |
| 2018 | LR | -128.474520 | -0.155287 | 1.011089 | -129.640896 | 2.8e-14 | -12.8475 | 1.01264e-94 | yes |
| 2018 | PolyRidge | -129.455167 | -0.005960 | 0.691362 | -130.152490 | 0.0e+00 | -12.9455 | 8.8759e-89 | yes |
| 2019 | HGB | -133.367181 | 0.152309 | -3.826932 | -129.387940 | 0.0e+00 | -13.3367 | 5.40122e-67 | yes |
| 2019 | LR | -131.474807 | 0.161715 | -2.841496 | -128.471596 | 0.0e+00 | -13.1475 | 2.28585e-83 | yes |
| 2019 | PolyRidge | -132.406231 | 0.238822 | -3.517764 | -128.649645 | 0.0e+00 | -13.2406 | 2.76002e-69 | yes |
| 2020 | HGB | -128.687710 | -0.277410 | 0.905513 | -129.870633 | 0.0e+00 | -12.8688 | 1.56129e-68 | yes |
| 2020 | LR | -129.011127 | -0.219455 | -1.150003 | -128.080578 | 0.0e+00 | -12.9011 | 9.73823e-77 | yes |
| 2020 | PolyRidge | -127.711498 | -0.249958 | 0.399140 | -128.360596 | 2.8e-14 | -12.7711 | 4.57545e-72 | yes |
| 2021 | HGB | -128.928126 | 0.059808 | 0.744118 | -129.612436 | 0.0e+00 | -12.8928 | 6.9879e-54 | yes |
| 2021 | LR | -128.329361 | 0.305739 | 0.574578 | -128.598200 | 2.8e-14 | -12.8329 | 3.23089e-58 | yes |
| 2021 | PolyRidge | -128.563109 | 0.061584 | 0.279257 | -128.780782 | 0.0e+00 | -12.8563 | 3.07628e-56 | yes |
| 2022 | HGB | -135.103980 | 0.257549 | -1.781106 | -133.065326 | 0.0e+00 | -13.5104 | 2.10339e-50 | yes |
| 2022 | LR | -132.521314 | -0.191766 | -1.624345 | -131.088735 | 0.0e+00 | -13.2521 | 1.70363e-54 | yes |
| 2022 | PolyRidge | -133.063555 | 0.434561 | -0.855488 | -131.773506 | 0.0e+00 | -13.3064 | 2.91224e-53 | yes |
| 2023 | HGB | -122.722228 | 0.269896 | 3.501241 | -125.953573 | 1.4e-14 | -12.2722 | 3.148e-50 | yes |
| 2023 | LR | -124.504173 | 1.100319 | 1.669090 | -125.072944 | 1.4e-14 | -12.4504 | 1.42503e-57 | yes |
| 2023 | PolyRidge | -122.160560 | 0.543298 | 2.985427 | -124.602689 | 0.0e+00 | -12.2161 | 1.94352e-47 | yes |

#### DKASC

| Year | Model | A (W) | B (W) | C (W) | D (W) | resid. | A / cap (%) | p | sig. |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| 2018 | HGB | -493.841585 | 55.980525 | -3.062641 | -434.798419 | 0.0e+00 | -9.4065 | 3.2069e-17 | yes |
| 2018 | LR | -431.413705 | 78.001368 | -10.618538 | -342.793800 | 0.0e+00 | -8.2174 | 1.15842e-10 | yes |
| 2018 | PolyRidge | -437.195217 | 79.569052 | -5.106125 | -352.520040 | 5.7e-14 | -8.3275 | 5.29005e-12 | yes |
| 2019 | HGB | -377.837689 | 90.001020 | 2.878505 | -290.715174 | 5.7e-14 | -7.1969 | 1.66762e-11 | yes |
| 2019 | LR | -310.773767 | 92.382769 | 0.868362 | -219.259360 | 5.7e-14 | -5.9195 | 1.4595e-06 | yes |
| 2019 | PolyRidge | -332.600091 | 97.838877 | 3.589091 | -238.350304 | 2.8e-14 | -6.3352 | 1.06503e-07 | yes |
| 2020 | HGB | -476.537407 | 68.143432 | -10.358387 | -398.035589 | 0.0e+00 | -9.0769 | 1.00524e-06 | yes |
| 2020 | LR | -432.849613 | 70.396084 | -3.135021 | -359.318509 | 1.1e-13 | -8.2448 | 1.69393e-07 | yes |
| 2020 | PolyRidge | -435.821843 | 66.651758 | 4.393490 | -373.563575 | 1.7e-13 | -8.3014 | 3.44613e-07 | yes |
| 2021 | HGB | -554.700141 | 46.574174 | -41.347066 | -466.778901 | 5.7e-14 | -10.5657 | 3.20087e-07 | yes |
| 2021 | LR | -510.835111 | 49.880169 | -34.606148 | -426.348794 | 1.1e-13 | -9.7302 | 6.04704e-08 | yes |
| 2021 | PolyRidge | -541.217940 | 51.933868 | -44.633322 | -444.650750 | 5.7e-14 | -10.3089 | 1.24557e-07 | yes |
| 2022 | HGB | -541.534598 | 49.358806 | 47.659812 | -539.835604 | 0.0e+00 | -10.3149 | 2.58705e-09 | yes |
| 2022 | LR | -512.501944 | 71.842501 | 30.853857 | -471.513300 | 0.0e+00 | -9.7619 | 3.01718e-11 | yes |
| 2022 | PolyRidge | -531.841796 | 70.792004 | 32.181166 | -493.230958 | 5.7e-14 | -10.1303 | 2.61746e-09 | yes |

---

## 6. An expectation that turned out wrong

The pre-registered rule expected `C ≈ 0`, on the grounds that the
intersection is a uniform random subset of the clean arm's test year.
Measured (PVGIS full):

```
mean |C| = 1.738895 W      mean |B| = 1.201016 W
```

**Contrary to expectation, |C| is LARGER than |B|.** Within a year the three
models' C values share a sign (same draw); across years the sign changes.
This is not a bias but the per-year sampling shift of the intersection draw.
It is not negligible either: subtracting `C` in the decomposition is
therefore mandatory. Had the work proceeded on the assumption
"intersection RMSE ≈ full RMSE", the result would have been corrupted.

Recorded as deviation 2 in [S6](S6_on_kayit_sapmalari.md).
