# S6 — Record of deviations from pre-registration

Supplementary material. Compiled from `dokumanlar/varyant-test-taksonomisi.md`
§4, `dokumanlar/varyant-dm-yorum-kurali.md` and
`dokumanlar/dkasc-kalite-kurallari.md`. No number in this file was produced
for it.

---

## 0. What was pre-registered, and how

Three documents fix interpretation before measurement. Each states the day
it was written and what did not yet exist at that time:

| Document | Fixed before | Governs |
|---|---|---|
| `pv10/ozet.py` | the saturation grid was run | which summary tables and metrics Phase 4 reports |
| `dokumanlar/dkasc-kalite-kurallari.md` | any DKASC row was processed | the ten data-quality rules and five decisions |
| `dokumanlar/varyant-dm-yorum-kurali.md` | `arac/ablasyon_dm.py` was ever run, when no `ablasyon_belirsizlik_*` file existed | how each possible Phase 2 uncertainty result would be read |

The governing convention: **an interpretation rule may be changed after
results are seen, but it may not be hidden.** Every later edit is marked
`[added later — <date>]`, carries its reason, and the superseded text is
never deleted or struck.

Two deviations from pre-registration occurred. Both are reported here
without concealment.

---

## 1. Deviation 1 — test count: cell level instead of variant level

### What was pre-registered

The interpretation rule stated:

> Four variants tested (`contemporaneous`, `global scaling`,
> `shuffled split`, `worst case`); `clean` is the reference and `night` is
> degenerate. With three sources (PVGIS full, PVGIS reduced, DKASC) this is
> **4 × 3 = 12 DM tests**. At α = 0.05 the **expected number of chance
> significances is 0.60.** This number will appear in the table.

That wording assumed testing would be **aggregated at the variant level**.

### What was actually done

The implementation ran at **cell level** — one test per (test year × model)
— matching the granularity already used in Phase 3 (21 pairs) and Phase 4
(45 and 15).

| Source | Tests | Expected by chance (α = 0.05) |
|---|---|---|
| PVGIS full | 84 | 4.20 |
| PVGIS reduced | 84 | 4.20 |
| DKASC | 60 | 3.00 |
| **Total** | **228** | **11.40** |

### Consequence for the claims

No multiple-comparison correction was applied, as pre-registered.

The variant this matters most for is **global scaling**, whose significant
cells total **19 of 57** (7/21 PVGIS full + 8/21 PVGIS reduced + 4/15
DKASC). That is above the 11.40 expected across all 228 tests, and above the
2.85 expected across its own 57 cells — but the claim does not rest on
significance. It rests on **effect size**: the largest absolute effect across
all three sources is **0.1239 % of installed capacity** (DKASC 2019, Hist
Gradient Boosting, 6.506344 W against 5250 W), which is under a quarter of
the pre-registered practical-significance threshold of 0.5 % of capacity.

The deviation therefore changes the chance-expectation arithmetic that is
printed alongside the result; it does not change what the result is used to
argue. Reporting at cell level is also the more conservative presentation,
since it exposes how few cells carry the effect.

---

## 2. Deviation 2 — the `C ≈ 0` expectation was wrong

### What was pre-registered

Reading rule §3.3b, written before any DM or bootstrap number existed,
expected the clean arm's population term `C` to be negligible:

> The intersection is a uniform random subset of the clean arm's test year
> (the shuffled arm draws uniformly from the pool), so the **C term should
> be of the order of sampling noise, ≈ 0**; the population effect should
> live in **B**. If |C| does not come out small, the intersection is not
> behaving like a random subset, and **that is itself a finding and will be
> investigated.**

### What was measured

PVGIS full:

```
mean |C| = 1.738895 W      mean |B| = 1.201016 W
```

**|C| is larger than |B|, contrary to the expectation.**

### Investigation, as the rule required

Within a given year the three models' `C` values share a sign — they are
the same draw. Across years the sign changes. This is therefore **not a
bias** but the per-year sampling shift of the intersection draw.

It is not negligible either. The decomposition's subtraction of `C` is
consequently **mandatory**: had the analysis proceeded on the convenient
assumption that intersection RMSE ≈ full-set RMSE, the result would have
been corrupted.

### Consequence for the claims

None of the reported quantities change — the decomposition already carried
the `C` term, because the identity `A + B − C = D` was specified as exact
algebra rather than as an approximation. What changes is that the expected
*simplification* (reporting `B` alone as "the population term") was not
available. The paper reports `A`, `B`, `C` and `D` separately for all three
sources, which is what §3.3b required in the first place.

The pre-registration was wrong about the measurement and right about the
procedure. Recording that distinction is the point of this entry.

---

## 3. A separate, non-pre-registration deviation: wind (rule 4)

Listed here for completeness because [S1](S1_oznitelikler.md) and
[S3](S3_dkasc_kalite_kurallari.md) both point at it. It is **not** one of
the two deviations above: it departs from a *frozen project rule*, not from
an interpretation pre-registration.

Project rule 4 requires feature definitions to stay identical to the earlier
single-year study. The DKASC replication breaks that identity:

- `WS10m` and its lags are in the core feature set, but in DKASC
  `Wind_Speed` is **entirely empty in all 72 months of six years**.
- `Wind_Direction` is populated but its unit and sign cannot be validated
  (range −6.9796 to 11 596.1650; the convention changes twice).
- Other years were downloaded specifically to check whether the channel is
  populated anywhere: 2017–2022, absent in all six.

The replication is therefore **a wind-free variant of the PVGIS setup, not a
byte-for-byte copy**, and is reported as such. The feature count drops from
29 to 21.

Two mitigations are in place:

1. The deviation is encoded as a **declared value** (a shorter tuple passed
   to `oznitelik_uret`) rather than a code branch, so it is a reportable
   parameter instead of a side effect of the code path.
2. A **matched control** — PVGIS data run with the DKASC feature set,
   reported throughout as *PVGIS reduced* — separates the feature-set
   contribution from the data contribution. For the contemporaneous
   variant it attributes 0.0227 of the 0.1617 difference to the feature set
   and 0.1390 to the data.

### Open item

The pre-registered commitment was that **wind's permutation importance
would be measured on the PVGIS side** so a reader can see the magnitude of
the deviation. **This measurement has not yet been run.** It is recorded as
outstanding, not as complete.

---

## 4. Related records that are *not* deviations

For the avoidance of doubt, these are documented late additions or
corrections that happened **before** the measurement they govern, and so do
not constitute deviations from pre-registration:

| Record | Why it is not a deviation |
|---|---|
| Reading rule §3.3b (population masking) | Added 8 Aug 2026, but before `arac/ablasyon_dm.py` was run and before any `ablasyon_belirsizlik_*` file existed |
| DKASC rules 9 and 10 | Added after the first eight, but before any DKASC row was processed or any model trained |
| Rule 10's two corrections | Corrections to an un-run rule, each with its reason recorded; the superseded text remains |
| Rule 6 diagnosis | The firing pattern was measured and found to disagree with the rule's stated intent, and **the rule was deliberately not changed** — relaxing a pre-registered threshold because it caused downstream trouble is the post-hoc behaviour this study criticises |
| Variant comment fix (`worst case`) | The code always carried four interventions; a stale comment described three. The code was right, the comment was incomplete; corrected and recorded |
| Class B gate failure on DKASC | A gate caught a real defect in the *diagnostic's* population definition before anything was reported; fixed, re-run, gate passed 15/15 |

### Two phase notes that carry no pre-registration claim

`faz-notlari/faz-2.md` and `faz-notlari/faz-3.md` were compiled
**retrospectively** on 8 August 2026 from code, git log and tag messages.
Both say so in their title and header. Phases 1+2+3 are three commits, all
pushed within sixteen minutes on 30 July 2026, and `sonuclar/ablasyon.csv`
and `siralama_*.csv` share a commit with the code that produced them — so
there is **no file-level evidence** that the setup was fixed before results
were seen. `faz-notlari/faz-4.md` and `faz-notlari/dkasc-replikasyon.md`
were written in their own phases' sessions and **do** carry a
pre-registration claim.

The pre-registration discipline on the DKASC arm is a direct response to
that gap.
