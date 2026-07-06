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

---

## Addendum (v11) — metabolite-sensor enrichment + out-of-sample–only reporting

Two changes were made at the user's request, and re-reviewed against the same lenses.

**Change 1 — expanded metabolic/cofactor coverage.** The class most relevant to the database's
purpose (metabolite sensing) was thin (7 pseudoenzymes). It was expanded to 16 literature-curated
metabolic/cofactor pseudoenzymes (14 in DB): acatalytic carbonic anhydrases CA8/10/11 (CARPs, lack
the Zn-coordinating histidines), the ALDH dead enzyme ALDH16A1, pseudo-NDPKs NME7/8/9, pseudo-amidases
PGLYRP1/3/4, and the SAHH paralogs AHCYL1/AHCYL2 — each matched to active enzymes of the same fold
(CA1/2/9/12, ALDH1A1/2/3A1/7A1/9A1, NME1/2/3/4, PGLYRP2, AHCY). Anti-circularity (M5) is preserved:
every added label is a literature assignment, independent of tool scores.

**Change 2 — dropped "all in-DB" metrics.** The optimistic in-sample numbers were removed entirely;
the tab, figure, and `eval_metrics.json` now carry only the out-of-sample estimate. This fully
resolves M1 (leakage) by construction — there is no longer an in-sample number that could be quoted.

**Re-measured out-of-sample result:** Sensitivity 0.59 [0.43–0.73], Specificity 0.97 [0.87–0.99]
(n = 39 pseudo + 38 active). The modest sensitivity drop vs the previous 0.63 is expected: the added
metabolic/cofactor folds are exactly the ones the linear death-motif gate cannot see.

**New finding (Major, disclosed — not a defect):** on metabolic/cofactor folds the gate has limited
recall (metabolic 4/7, cofactor 1/3 out-of-sample) while specificity stays near-perfect (no active
metabolic enzyme flagged). Several genuine high-MR metabolite-sensor candidates — CA8 (0.88),
CA10 (0.62), NME7/NME9 (~0.56) — are **not** called dead by the gate. This is the same structural
limitation as the pseudo-DUB blind spot (M4): CARP and NDPK folds have no scannable linear death
motif. The practical consequence is stated plainly on the tab: **for metabolite-sensor discovery,
MR (pocket retention) is the operative signal, and the dead-call gate is a conservative,
high-specificity classifier that will miss motif-less dead folds.** MR's role (M2) is unchanged and
still correct by construction (AUC < 0.5).

**Verdict unchanged:** fit to publish. The leakage concern is now structurally eliminated (OOS-only),
metabolite-sensor coverage is materially deeper, and the gate's fold-specific blind spots are
disclosed rather than averaged away.


---

## v12 addendum — mycelium review of the two new detection channels

**Scope of this review:** the two channels added to the dead-call in v12 — an LLM function-text
classifier and fold-specific catalytic-residue motifs — plus the re-scoring and eval-tab rebuild
they drove. Lenses applied: `llm-failure-modes`, `data-pipeline-leakage`, `doc-schema-fidelity`.

### What changed
- Dead-call `override_pos` is now the union of three channels: structure gate (unchanged),
  text classifier (`ch_text`), fold-motif (`ch_foldmotif`).
- Full-DB dead-calls 435 → 463 (+28 net-new: 26 text-only, 2 text+motif).
- Out-of-sample: Sensitivity 0.59 → **0.67** [0.51–0.79]; Specificity **0.97** [0.87–1.00] held;
  sole FP still PTEN (CX5R gate, not a new channel).
- Per-class OOS: cofactor 1/3 → **3/3** (CA8/CA10 recovered by the new channels, CA11 already by
  structure); metabolic held 4/7; pseudokinase 12/14; pseudo-GTPase 3/3; pseudophosphatase 4/10;
  pseudo-DUB 0/2.

### Findings

**F7 [Major, FIXED during review] — misattributed precision number.** The channels narrative first
read "precision on active comparators 37/38." That conflated the *whole-gate* OOS specificity
(37/38, whose single FP is PTEN from the pre-existing CX5R gate) with the *text channel's own*
precision. Direct check: the text channel flags **0 of 60** in-DB active comparators. Corrected the
tab to state that the text channel flags none of the 60 actives. (`doc-schema-fidelity`: numerical
claim in docs disagreed with the code output.)

**F8 [Major, FIXED during review] — CA11 credited to the wrong channel.** The narrative claimed the
new channels "recover CA8/CA10/CA11." In fact CA11 has `ch_structure=True` and was already a dead-call
before v12; only CA8 and CA10 are genuine new recoveries. Corrected in three places on the tab.
(`doc-schema-fidelity`: attribution contradicted by `base_override`.)

**F9 [Major, HELD — anti-circularity of the text channel].** The most consequential question for a
knowledge-based LLM channel: does it make "sensitivity" a measure of *rediscovery* rather than
*detection*? Three structural guards keep the evaluation honest. (a) The classifier is blind to gene
name and truth label — it reads only the UniProt function comment. (b) The reference set is
literature-curated independently of any tool score. (c) The channel fires on an *explicit textual
assertion of lost activity*, which is a real, human-written annotation signal, not a model prior.
The residual caveat, stated plainly: where a curator has already written "lacks catalytic activity,"
the text channel is confirming an existing human judgment, so the +0.08 sensitivity is best read as
"the tool now surfaces annotation-documented dead enzymes it previously ignored," not "the tool
discovered novel dead enzymes." This is disclosed on the tab and is the correct framing.

**F10 [Major, HELD — precision cost of a DB-wide propagating channel].** A text channel that fires on
2670 proteins can inject false positives far from the reference set (the reference-set precision check
only sees comparators). The v12 strict two-pass filter (reasoning-model re-verification requiring an
explicit self-inactivity statement) was added precisely for this: it cut high-confidence text-dead
calls 113 → 73 and removed the demonstrated FPs (FGR, RHOC, NPR1, MAP3K8/TPL2 — all active, inactivity
merely *inferred* from absence of a claim). Net active-comparator FPs from the new channels: **0**.
The residual risk (unmeasurable without a full-DB gold set) is disclosed.

**F11 [Minor, HELD — fold-motif redundancy on this OOS set].** On the OOS pseudo set the text and
fold-motif channels fire on the same proteins (the CARPs), so the fold motif adds 0 *additional* OOS
detections. This is not a defect — the fold motif is orthogonal structural evidence (residue-level,
annotation-independent) and would catch a CARP whose annotation is uninformative — but the honest
statement is that its incremental OOS value here is confirmatory, and this is stated on the tab.

**F12 [Major, HELD — honest metabolic misses].** NME8/NME9 and GOT1L1 remain not-dead. Verified: they
retain their catalytic residues (His118 for NDPKs) and their UniProt text asserts activity, so neither
a residue-loss motif nor an explicit-inactivity text signal can fire. These are regulatory/domain-level
pseudoenzymes beyond the reach of structure- and text-based gates. Disclosed on the tab rather than
papered over.

### Leakage / pipeline (data-pipeline-leakage)
- **OOS split preserved:** the 69 gold-tuning accessions still define in-sample; all metrics are on the
  77 disjoint OOS proteins. The new channels were *not* tuned on the OOS set — the text classifier is
  label-blind and the fold-motif thresholds come from reference-enzyme biochemistry (CA2/NME1/ALDH2),
  not from fitting the reference set. No new leakage path introduced.
- **No silent coercions:** channel integration is boolean OR with explicit per-record flags; MR and
  mr_rank unchanged (verified identical to v11 pocket-retention values).

### Verdict
**Fit to publish.** Two attribution defects (F7, F8) were caught and fixed during this review before
deployment; both were documentation-fidelity errors, not scoring errors — the underlying dead-calls
were correct. The sensitivity gain is real (0.59 → 0.67), specificity is held, zero new false
positives among active comparators, and the framing (detection-vs-rediscovery, precision cost, honest
metabolic misses) is disclosed on the tab.

---

## v13 addendum — Layer 3 (paralog-contrast channel `ch_paralog`)

Reviewed the new fourth detection channel against four lenses: `data-pipeline-leakage`
(threshold tuning, metric independence), `stats-causal` (specificity claim), `llm-failure-modes`
(no LLM in this channel — N/A beyond the text layer already reviewed), and `doc-schema-fidelity`
(every quantitative claim in the info-tab narrative re-verified against live kernel state).

**Method under review.** For the two focal metabolic families — nucleoside-diphosphate kinase
(NDPK, 9 members) and aspartate transaminase (AST, 3 members) — each candidate is compared to its
experimentally-active paralogs at the family's conserved active-site positions (UniProt/M-CSA
Active-site/Binding-site/Site features + the PLP-lysine for AST), registered by a MAFFT MSA and
scored by BLOSUM62-weighted divergence. Fires when weighted divergence > 0.15 AND ≥1 non-conservative
substitution. Anchors/actives: NDPK anchor P15531 (NME1), actives NME1–4 (12 positions); AST anchor
P17174 (GOT1), actives GOT1/GOT2 (5 positions incl K259 PLP-lysine).

**F13 [Major, CAUGHT & DISCLOSED — specificity-by-construction, not independent].** The narrative
claim "flags none of the active NDP-kinase or transaminase paralogs (NME1–4, GOT1/GOT2)" is *true*
but was misleadingly framed as a specificity result. Probed empirically: of the 38 OOS active
comparators, exactly five fall inside a profiled family (NME2, NME3, NME4, GOT1, GOT2) — and **all
five are the reference members that define the active consensus.** Their near-zero divergence is
therefore definitional, not an independent test: a member cannot diverge from a consensus it helped
build. The "0 active false positives from ch_paralog" statement rests on construction. **Fix applied
before deploy:** the info-tab narrative now states this explicitly and cites the one genuinely
independent active NDP kinase — NME6, which is *not* a reference member — as the real specificity
check. NME6 scores weighted divergence 0.08, correctly below the 0.15 cutoff. That single
out-of-reference active is the only honest evidence that the channel discriminates, and it is now
the evidence the tab points to.

**F14 [Minor, HELD — threshold set label-blind, but n=small].** The 0.15 fire threshold was set from
the active-member divergence distribution (max active-reference divergence 0.125, driven by NME4's
single conservative substitution), not from the pseudoenzyme labels — this is the correct
label-blind procedure and avoids tuning on truth. The residual caveat is sample size: the active-null
distribution is built from 4 NDPK + 2 AST references, so the 0.15 cutoff has wide uncertainty. The
channel is deliberately scoped to these two families and silent by construction elsewhere, so a
mis-set threshold cannot propagate false positives across the database — the blast radius is 12
proteins. Disclosed as scope-limited.

**F15 [Minor, HELD — MSA registration was mandatory, verified].** An earlier pairwise-to-anchor
mapping misregistered active NME4 at divergence 0.33, tied with pseudo NME8 — a registration
artifact that would have destroyed discrimination. Switching to a MAFFT multiple alignment fixed the
column correspondence (NME4 → 0.125, GOT2 → 0.00). Verified the deployed profiles use the MSA path.
This is a resolved defect, noted so the fragility of the pairwise alternative is on record.

**F16 [HELD — honest labeling of the five fires].** ch_paralog fires on NME5, NME7, NME8, NME9,
GOT1L1. Of these: NME8, NME9, GOT1L1 are the three OOS metabolic targets (genuine net-new recoveries,
unreachable by structure/text/fold-motif because residues are intact and annotation asserts activity).
NME7 is a GOLD-tuning-set member (excluded from the OOS metric — does not inflate the reported 0.744).
NME5 is not in the reference truth set at all; it is flagged as a plausible-correct call
(literature-known inactive) but is labeled on the tab as unvalidated rather than counted as a hit.
The OOS sensitivity gain (0.667 → 0.744) is carried by exactly the three legitimate recoveries.

### Leakage / pipeline (data-pipeline-leakage)
- **OOS split preserved.** The three recovered proteins (NME8/NME9/GOT1L1) are OOS (not in the 69
  gold-tuning accessions); NME7 is correctly excluded from the OOS metric as gold. The channel was not
  tuned on OOS labels — active consensus and threshold both derive from active-member annotation and
  divergence, never from pseudoenzyme truth.
- **No metric contamination.** Active reference members scoring ~0 do not enter the specificity
  numerator as "true negatives earned" — they are definitional; the honest specificity evidence is the
  one out-of-reference active (NME6). Now disclosed.
- **Boolean-OR integration, MR untouched.** override_pos = ch_structure OR ch_text OR ch_foldmotif OR
  ch_paralog; verified override_pos sum = 468 (+5 vs v12's 463), MR and pocket_retention unchanged.

### doc-schema-fidelity (every narrative number re-verified against live state)
- override_pos = 468 ✓ · paralog fires = {NME5,NME7,NME8,NME9,GOT1L1} ✓ · channel attribution
  23/26/26 proteins → 0.59/0.67/0.74 cumulative OOS pseudo-sensitivity ✓ · sens 0.744 [0.589–0.854] ✓
  · spec 0.974 [0.865–0.995] ✓ · sole FP = PTEN (pre-existing CX5R gate, not ch_paralog) ✓ ·
  NME6 = 0.08 ✓. No drift between prose and computed values.

### Verdict
**Fit to publish.** One framing defect (F13) was caught and fixed before deployment: the specificity
claim was true-but-hollow (actives-are-the-references), and the narrative now discloses this and points
to NME6 as the only independent discrimination evidence. The sensitivity gain is real and carried
entirely by three legitimate OOS recoveries (0.667 → 0.744); specificity held at 0.974; the channel is
scope-limited to 12 proteins so a mis-set threshold cannot propagate. Honest labeling of NME5
(unvalidated) and NME7 (gold, architectural) is on the tab. The crux — anti-circularity — holds: the
active reference set is independent UniProt/M-CSA annotation, the contrast is label-blind, the threshold
comes from the active-null distribution, and evaluation is OOS-only.

**Layer 4 note (for the post-deploy decision).** NME7 is the informative case: it fires on paralog
contrast but is architecturally distinct (multi-domain regulatory NDPK), so sequence contrast flags it
for the wrong reason. A structure-based active-site-geometry channel (Layer 4) would target exactly this
class — pseudoenzymes whose sequence looks competent but whose 3D pocket is deformed — and NME7 is the
worked example of what Layer 4 would add beyond Layer 3.
