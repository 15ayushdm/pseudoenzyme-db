# Mycelium self-review — "Database evaluation" tab

Review of the new evaluation tab and its underlying pipeline, run against the
mycelium review lenses (`skills/core/references/review/*`). Lenses weighted for
this artifact: **data-pipeline-leakage** (circularity is the central risk of
"evaluate a tuned classifier"), **stats-causal** (are the CIs and the ROC
honest?), **doc-schema-fidelity** (does the tab say what the numbers mean?).
Severity ladder: Major = would change a reader's conclusion; Minor = would not.

---

## M1 [MAJOR — found and fixed] Train/test leakage between the death-motif gate and the "independent" benchmark

**Finding.** The dead-call gate (VAIK-K / HRD-D / DFG-D loss for kinases, CX5R
for phosphatases, the GHKL score cut, etc.) was **tuned** on a 69-protein gold
development set (46 pseudoenzymes + 23 active comparators) — that is where the
KSR1/2 recall-vs-specificity trade-off and the ePK motif thresholds were set.
The new evaluation reference set was compiled independently from the literature,
**but it structurally overlaps that tuning set**: 43 of 73 in-DB pseudoenzymes
and 22 of 47 active comparators share a UniProt accession with the gold set.
Reporting a single sensitivity/specificity over all 120 in-DB proteins therefore
reports partly on the gate's own training data and **inflates recall**.

Note the overlap was initially undercounted at the symbol level (26) because the
gold sheet stores genes as `SYMBOL (alias)`; matching on **accession** is
authoritative and gives 43/22.

**Fix (applied).** Split the reference set into the gold-overlap subset and a
disjoint **out-of-sample** subset (30 pseudo + 25 active, accessions never in the
tuning set) and recomputed metrics on the disjoint subset. The tab, the figure,
and `eval_metrics.json` now **lead with the out-of-sample numbers** and present
the all-in-DB numbers second, explicitly labelled as including tuning-set
members. An "in gold tuning set" column and a "show only out-of-sample" filter
were added to the table so a reader can see and reproduce the split.

**Effect on the headline.**
- Out-of-sample: **Sensitivity 0.63 [0.46–0.78], Specificity 0.96 [0.81–0.99]** (n = 30 + 25).
- All in-DB (optimistic): Sensitivity 0.71 [0.60–0.80], Specificity 0.98 [0.89–0.996] (n = 73 + 47).

The ~0.08 sensitivity gap is the leakage. Specificity is essentially unchanged,
which is expected — the specificity failure mode (one FP: PTEN) is not a
tuning artifact. This is the primary outcome of the review and it materially
changes what the tab claims.

---

## M2 [OK — verified honest] MR ROC direction is correct, not a bug

MR separates the classes with **AUC(pseudo > active) = 0.35**, i.e. below 0.5.
A naive reader could call this "worse than random" and treat it as a failure.
It is neither. **MR = pocket_retention × struct_conf is a pocket-retention
score, and active enzymes retain their pockets** — so MR is *systematically
higher in the active comparators* (median 0.48 vs 0.23 for pseudoenzymes,
Mann–Whitney p = 0.004). MR is not, and was never claimed to be, a deadness
detector; the **dead-call gate** is the classifier, and MR is the downstream
"does the dead protein still have a pocket worth chasing" score. The tab states
this explicitly and panel (a) is titled to make the direction unmistakable. No
change required — flagging it so the sub-0.5 AUC is not later "fixed" by
flipping a sign.

---

## M3 [MINOR — disclosed] Coverage is uneven across classes

Per-class sensitivity rests on small n in several classes: pseudoprotease 3/3,
cofactor 2/2, metabolic 2/3, pseudo-GTPase 7/8. These Wilson CIs are wide and
shown as such (panel b), but a reader skimming "pseudoprotease 1.00" should see
the n. The table and figure both print `called_dead / n` next to every class.
Additionally, 19 literature pseudoenzymes in the reference set are **out of
scope** (not in the 2670-protein DB — e.g. CENPM, SELENOO, several
rhomboid/derlin proteases), so the evaluation speaks to DB coverage, not to the
full pseudoenzyme complement. Disclosed in the tab narrative.

---

## M4 [MAJOR — disclosed limitation, not fixed] The gate has zero reach on pseudo-DUBs

Out-of-sample and overall, the gate calls **0 / 5 pseudo-DUBs** dead
(USP39, USP50, USP53, USP54, OTULINL, USPL1). This is a real, structural blind
spot: the death signal for USP/OTU folds is not a single linear sequence motif
(no VAIK/HRD/DFG analogue), so a motif-scanning gate cannot see it. This is not
a tuning artifact and is not fixable by threshold adjustment — it needs a
fold-specific catalytic-residue check. Reported honestly in the tab as a named
gap rather than averaged away; it is the main driver of the FN count and pulls
overall sensitivity down. Flagged as future work.

---

## M5 [OK] Anti-circularity of the reference set itself

The reference set is literature-curated (Murphy, Eyers, Ribeiro, Todd, Tonks,
Manning pseudoenzyme reviews) and its truth labels are **independent of any tool
score** — no protein was labelled pseudoenzyme *because* the tool called it dead.
Active comparators are active members of the *same folds* (BRAF for the
pseudokinases, PTPN1 for the pseudophosphatases, USP7 for the pseudo-DUBs, …),
which is the correct negative set: it tests whether the gate distinguishes dead
from active *within* a fold, not whether it distinguishes a kinase from a
globin. This is the design crux and it holds. (The residual leakage in M1 is a
*tuning*-set overlap, a separate axis from label independence.)

---

## M6 [MINOR] One false positive is defensible

PTEN is labelled "active" (it is a functional lipid phosphatase and tumour
suppressor) but is called dead by the CX5R protein-phosphatase gate because its
*protein*-phosphatase activity is weak and its catalytic pocket reads as
degraded on the protein-phosphatase criterion. This is a labelling-granularity
edge case, not a gate error, and it is the sole FP. Left as-is and noted in the
tab.

---

## Verdict

The tab is **fit to publish with the leakage correction applied**. The one
change that alters a reader's conclusion (M1) has been made: the artifact now
leads with the unbiased out-of-sample estimate and discloses the optimistic
in-sample estimate alongside it, with the split reproducible in the table. The
remaining Major (M4, pseudo-DUB blind spot) is a disclosed scope limitation, not
a correctness defect. MR's sub-0.5 AUC (M2) is correct by construction and
documented so it is not "fixed" later. Small-n classes and out-of-scope proteins
(M3) are shown with their denominators and CIs.

Headline to carry forward: **out-of-sample Sensitivity 0.63 [0.46–0.78],
Specificity 0.96 [0.81–0.99]** on 55 disjoint proteins.
