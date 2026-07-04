# Review — Human PseudoenzymeDB Explorer — 2026-07-04

**Method**: Applied the `arjunrajlaboratory/mycelium` `/mycelium:review` rubric manually
(the plugin's slash commands can't run inside Claude Science). Fetched the repo, extracted
the six reviewer-lens checklists (`skills/core/references/review/*.md`) and the Major/Minor
synthesis ladder (`synthesis.md`), and ran each lens against the explorer, the
metabolite-relevance methodology, the three scoring "moves," the two annotation guards, the
benchmark, and the changelog. Every load-bearing number below was recomputed from the shipped
records/CSVs — not read from prose.

**Scope**: working state of `index.html` (v7, 2670 records) + `metabolite_relevance.csv`,
`motif_calls.csv`, `benchmark_by_class_v2.csv`.
**Sub-agent lenses run**: 6/6.

---

## Key decisions in this analysis
- **MR = pocket_retention × struct_conf** — compound-agnostic product, bins high≥0.50 / medium≥0.25. *Verified exact* (max deviation 7.6e-5 over all 2670). See F4.
- **Death-motif gate (Move 1)** — proteins in the 4 ePK/PTP/CASP/RHB M-CSA buckets are re-called "dead" from field-standard motifs (VAIK-K / HRD-D / DFG for kinases, CX5R for phosphatases); "dead" promotes to `override_pos`. **This is the load-bearing decision and it has a specificity problem — see F1.**
- **Two display-level guards** — off-domain cofactor flag + literature symbol-collision flag; neither alters ranking. *Verified display-only.* See F6.
- **Benchmark recall 0.674→0.860** on 43 gold pseudoenzymes. *Verified exact.* Specificity claim — see F2.

---

## Findings

### F1 — [MAJOR] Death-motif gate flips active kinases to "dead" on a single missed VAIK-lysine
*Lens: bioinformatics + stats/causal (specificity)*

The gate calls an ePK "dead" whenever fewer than 3 of 3 motifs are detected
(`motif_intact < 3 → dead`, verified: 51 of 68 ePK "dead" calls have 2/3 motifs present).
**36 of those 68 rest on losing only the VAIK-lysine**, HRD and DFG both intact.

The VAIK-K detector has a high false-negative rate. Known **catalytically active** kinases
with a canonical lysine are scored `m_VAIK=False` and called dead: FGFR2 (aln 170), LCK (136),
MAP2K1/MEK1 (252), NTRK1 (142), PLK1 (348), STK11/LKB1 (294) — while the same-fold active
controls BRAF, EGFR, ABL1, SRC, CDK2, AURKA are correctly `m_VAIK=True`. The lysine is present
in FGFR2/LCK/etc.; the alignment fails to register that column.

**Consequence:** of the **60 proteins the gate newly promoted to `override_pos`, ~42 are
canonically active** (FGFR2/3/4, PDGFRA, NTRK1/2, MEK1/2, MAP3K5/ASK1, LCK, ITK, JAK3, PLK1,
STK11, CDK6, the four WNKs, MYLK, MKNK1/2, …). **16 land in the HIGH MR band (≥0.50):** MAP2K1,
MAP2K2, MKNK1, MKNK2, PDGFRA, NTRK1, NTRK2, DDR1, DDR2, MAP3K5, MAP3K15, MYLK, TSSK1B, STK32A/B/C.
These now render as "death-motif-dead" high-priority metabolite sensors, which they are not.

Two distinct sub-cases worth separating in any fix:
- **Detection failure** (FGFR2, LCK, NTRK1, PLK1, STK11, MEK1…): canonical VAIK-K present but
  not found → pure alignment/registration bug.
- **Genuine atypia, still active** (WNK1-4 — "With No lysine [K]", catalytic Lys relocated to
  β2; and the guanylyl/receptor-GC pseudokinase domains GUCY2C/D/F, NPR1/2): motif genuinely
  non-canonical but the protein is active or the "pseudo" call needs a domain-specific rule.

**Fix**: (a) require ≥2 lost motifs, or weight HRD/DFG loss above VAIK-K loss, before calling
"dead"; (b) add an active-enzyme control panel (BRAF, EGFR, FGFR2, MEK1, PLK1, LCK, CDK6, WNK1)
to the benchmark and report false-positive rate, not just recall; (c) special-case the WNK
family and receptor guanylyl cyclases. Until then, the "death-motif-dead" badge on ePK-bucket
proteins should be read as "atypical motif," not "confirmed pseudoenzyme."

### F2 — [MAJOR] "Specificity held at 1.00" is not substantiated by the shipped benchmark
*Lens: documentation/schema fidelity + fabricated-output*

The changelog and methodology state specificity stayed at 1.00 through the Move-1 recall lift.
The shipped `benchmark_by_class_v2.csv` contains only `n, hits_base, hits_over, recall_base,
recall_over, delta` — **there is no specificity, false-positive, or active-control column.** The
1.00 figure has no reproducible source in the artifacts, and F1 shows the true active-kinase
false-positive rate is substantially above zero. Per the rubric's "numerical claims with no
matching executed output" rule this is Major.

**Fix**: either add the active-negative control set to the benchmark CSV and recompute
specificity honestly, or strike the "specificity 1.00" claim from the changelog and methods.

### F3 — [MAJOR→borderline] `struct_conf` is a near-constant (0.70 for 91% of records)
*Lens: stats/causal + smuggled-default*

MR is sold as a two-factor product `pocket_retention × struct_conf`, and the new sensor panel
shows both bars. But `struct_conf = 0.70 exactly for 2435/2670 (91.2%)`; only 7.5% exceed 0.70.
For the vast majority of proteins the "structural confidence" axis contributes a fixed 0.70
multiplier — MR is effectively `0.70 × pocket_retention` with a thin tail of exceptions. That is
defensible *if* 0.70 is a deliberate floor/default for "AlphaFold model, unremarkable pLDDT," but
as presented (a live second dimension) it overstates how much independent information the second
factor adds. This is the rubric's "smuggled default on a load-bearing knob."

**Fix**: document what 0.70 means and why it's the modal value; consider showing "struct_conf =
0.70 (default)" in the panel so users don't over-read a flat axis as evidence.

### F4 — [OK] MR reconstruction is exact
Recomputed `pocket_retention × struct_conf` for all 2670 records vs stored `metabolite_relevance`:
max deviation **7.6e-5** (4-dp rounding). Bin thresholds (high≥0.50/medium≥0.25) reproduce with
**0 mismatches**. Positive-band counts (66 high / 195 medium / 218 low over 479 positives) verified.

### F5 — [MINOR] `home_family_name` is misleading for reassigned kinases
*Lens: doc/schema fidelity*
Promoted kinases carry family labels like "mitogen-activated protein kinase kinase" for WNK1-4,
CDK6, GUCY2C and "protein kinase C" for JAK3, PLK1 — these are M-CSA nearest-family assignments,
not the protein's real subfamily. Cosmetic in the DB but confusing on the detail card. Consider a
"(nearest M-CSA family)" qualifier.

### F6 — [OK] Both annotation guards are display-only, as claimed
Verified: off-domain cofactor flag set on 430 records (83 fully off-domain), lit symbol-collision
flag on exactly 1 (TTN). Zero fully-off-domain positives draw `observed_concordant` support, so
the red banner never contradicts a ranking input. Guards do not touch MR. This part is clean and
is a genuine improvement.

---

## What was checked and is fine
- **Statistics/causal**: MR arithmetic, bins, positive-band tallies — exact (F4).
- **Data pipeline/leakage**: no train/test split to contaminate (this is annotation, not a fitted
  model); pocket_retention/struct_conf injected from the authoritative CSV with verified product.
- **Bioinformatics (identifier layer)**: the TTN acronym-collision guard and off-domain-peptide
  guard directly address the field's silent failure modes; well-targeted (F6).
- **LLM antipatterns**: guards don't silently coerce; no try/except fallbacks in the scoring;
  the giant-protein artifact is auto-caught, not hard-patched.
- **Doc fidelity**: changelog matches the guard implementation.

---

## Questions for the analyst
1. **Is the death-motif gate meant to be high-recall or high-precision?** As built it is
   recall-first and admits ~42 active kinases. If the DB's purpose is hypothesis generation that's
   arguably acceptable *if disclosed* — but the "death-motif-dead" badge currently asserts precision.
2. **What is `struct_conf = 0.70`?** A default floor, or a real per-protein score that happens to
   cluster? The answer decides whether F3 is Major or Minor.
3. **Where did "specificity 1.00" come from?** If there's an active-control computation, ship it in
   the benchmark CSV; if not, the claim should come out.

---

*Top priority: F1 + F2 together. The death-motif gate is the scientific engine of Move 1, and
right now it promotes more active kinases than genuine pseudokinases in the ePK bucket while the
one artifact that could catch that (specificity on active controls) isn't computed. Everything
else is documentation hygiene or is already clean.*
