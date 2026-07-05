# PseudoenzymeDB Explorer — v2 Changelog: Metabolite-Sensor Layer

**Artifact:** `pseudoenzyme_explorer_v2.html` (17.5 MB, self-contained)
**Built from:** `pseudoenzyme_explorer.html` (v1, 16.1 MB) + three analytical refinements
**Motivation:** Sharpen the database's ability to surface cofactor / redox / NAD sensors of
the IRBIT-AHCYL1 type — pseudoenzymes that keep a small-molecule pocket after losing catalysis.

---

## Move 1 — Family-specific death-motif re-scoring

**Problem.** The generic catalytic-column rule scored several textbook pseudoenzymes as *active*
because the M-CSA catalytic columns do not correspond to the field-standard "death motifs"
(kinase VAIK-K / HRD-D / DFG-D; phosphatase CX5R; GHKL; etc.). KSR1/2, CASK, PTPRN2 and VRK3
were being missed.

**Fix.** Added family-specific motif detection for the eukaryotic-protein-kinase fold and the
other catalytic classes, and let an absent death motif override the base call.

**Effect on the curated benchmark (43 gold-standard pseudoenzymes):**

| class | n | recall (base) | recall (v2) | recovered |
|---|---|---|---|---|
| **ALL** | 43 | 0.674 | **0.860** | **+8** |
| pseudokinase | 21 | 0.667 | **1.000** | +7 |
| pseudophosphatase | 7 | 0.714 | 0.857 | +1 |
| pseudoprotease/DUB | 6 | 0.500 | 0.500 | 0 |
| pseudo-GTPase | 5 | 0.800 | 0.800 | 0 |
| other | 4 | 0.750 | 0.750 | 0 |

Specificity held at 1.00 (no active enzyme flipped to pseudo). Database-wide, positives rose
**419 → 479 (+60)**; 92 proteins now carry a family death-motif-dead flag. All ten canonical
pseudokinase/pseudophosphatase controls (KSR1, KSR2, CASK, PTPRN2, VRK3, STRADA, PRAG1,
TRIB1/2/3) are now positive.

## Move 2 — `metabolite_relevance` for every candidate

**What.** A 0–1 score for how likely a pseudoenzyme still holds a *small-molecule cofactor*
pocket (as opposed to a protein-protein scaffold), weighting the retained pocket by cofactor
class: redox (NAD/NADP/FAD) and nucleotide (ATP/ADP/GTP) score highest, SAM and metal lower.

**Result.** Among the 479 positives, 30 score ≥0.45 and 55 more in 0.35–0.45.
The top of the ranking is dominated by nucleotide-fold pseudoenzymes (ASNSD1 0.71, HSPA14 0.64,
the MAP2K / MKNK / KIF5 families ~0.58–0.60). **IRBIT/AHCYL1 and its paralog AHCYL2 score 0.574
in the `redox-cofactor(NAD)` class** — the highest-scoring NAD candidates in the database.

## Move 3 — Nucleotide channel + cofactor-axis coverage flag

**What.** Two new axes tying each candidate's predicted cofactor to what the uploaded
PISA / PELSA proteomics screens can actually *measure*:
- `experimental_channel`: `measurable` (nucleotide/redox class the screens resolve) ·
  `nucleotide_predicted` (predicted but not resolved) · `blind_metal` (metal/Fe-S/heme,
  invisible to the screens) · `not_applicable` (no cofactor axis).
- `cofactor_concordance`: from `observed_concordant` (a predicted cofactor is experimentally
  seen binding) down to `no_prediction`.

**Result (479 positives).** Channel: 26 measurable · 187 nucleotide-predicted · 39 blind-metal ·
227 no-cofactor. Concordance: **12 observed_concordant**, 5 observed_other, 24 predicted-not-observed,
187 predicted-not-measurable, 251 no-prediction.

- **IRBIT/AHCYL1 is `observed_concordant`**: its predicted NAD cofactor is both PISA/PELSA-measurable
  *and* experimentally observed binding — the strongest metabolite-sensor evidence class, shared with
  AHCYL2, the CRY1/2 flavoproteins, and a handful of FAD/NAD dehydrogenase relics.
- **62 high-relevance pseudoenzymes (MR ≥ 0.35) sit in an experimental blind spot** — their nucleotide
  or metal cofactor pocket is predicted but the current screens cannot resolve it. These are the
  priority targets for a bespoke binding assay (ASNSD1, the MAP2K/MKNK kin-dead cassette, KSR1/2,
  CASK, the KIF5 motors).

---

## Explorer UI changes

1. **New `Sensor` column** in the results table — a metabolite-relevance bar + dominant cofactor
   class, sortable (defaults high→low).
2. **New detail-panel section** *"Metabolite-sensor assessment"* on every protein card, showing all
   three moves: death-motif re-scoring verdict, the relevance score + bin + rank, and the
   experimental-channel / concordance / predicted-vs-observed-binder breakdown. High-relevance
   blind-spot candidates get an orange call-out.
3. **New filter toggle** *"metabolite-sensor candidates only"* — restricts to positives with
   MR ≥ 0.2 and sorts by relevance.
4. Subtitle and About panel updated to describe the sensor layer.

## New data columns (carried in the embedded JSON, 2670 rows)

`motif_dead`, `base_pos`, `override_pos`, `metabolite_relevance`, `metabolite_relevance_bin`,
`mr_top_class`, `mr_rank`, `sensor_priority`, `expected_cofactor`, `experimental_channel`,
`channel_note`, `cofactor_predicted`, `cofactor_observed`, `n_cof_observed`, `cofactor_concordance`.

## Validation

- Embedded JSON parses (2670 records, all move columns present).
- Render script passes esprima ES6 syntax check (0 errors) and **executes end-to-end in a QuickJS
  engine** — `mrCell`, `sensorPanel`, and `render()` run without throwing on real rows.
- AHCYL1 card verified to show `0.574 / NAD / Observed = predicted / PISA-PELSA-measurable`.
- Blind-spot flag fires on the 5 nucleotide pseudoenzymes in the sample and correctly skips the
  measurable AHCYL1; sensor-only filter returns exactly the eligible set.
- (Headless-Chrome render was attempted but Chrome aborts under this sandbox even on a trivial
  file; QuickJS execution substitutes as the runtime check.)

## Companion artifacts

- `motif_calls.csv` — per-protein death-motif calls (Move 1)
- `benchmark_by_class_v2.csv`, `benchmark_delta.png` — recall gain by class (Move 1)
- `metabolite_relevance.csv`, `family_mr_weights.csv` — relevance scores + class weights (Move 2)
- `cofactor_channel.csv`, `cofactor_channel.png` — channel + concordance table and coverage figure (Move 3)


---

## v2.1 update — Info/Methods rewrite + metabolite-relevance documentation (2026-07-02)

**What changed:** The About/Methods panel was rewritten so the three v2 refinements are
documented as one cohesive narrative rather than a single orientation note. No data or scores
changed — this is a documentation + transparency pass on the same 2670-record payload.

New in the About panel, after the nine base build steps:

- **"The metabolite-sensor layer (v2)"** section introducing why the layer exists (the
  question shifts from *"is it dead?"* to *"if dead, does it still hold a cofactor pocket we
  can see experimentally?"*).
- **v2·1 death-motif re-scoring** — the VAIK/HRD/DFG · CX5R · GHKL rules, 92 reclassified
  proteins, recall 0.67→0.86, specificity held 1.00.
- **v2·2 metabolite-relevance — explicit formula:**
  `metabolite-relevance = pocket-retention × cofactor-class weight × structural confidence`,
  each factor defined (pocket-retention = intact ligand-contact fraction; class weight =
  sensor-likeness of the predicted cofactor, NAD/redox 0.9–1.0 down to metal 0.20 / generic
  substrate 0.45; structural confidence = normalised active-site pLDDT). Worked example
  AHCYL1 = 0.82 × 1.00 × 0.70 = 0.574.
- **v2·3 experimental channel & concordance** — measurable / nucleotide-predicted /
  blind-metal tags, observed-concordant tier (12 positives, incl. AHCYL1/NAD), and the
  67 high-relevance positives in the assay blind spot.
- **α-ketoglutarate limitation** — explicitly documents that 2-oxoglutarate is absent from
  the cofactor-class table, so JmjC / Fe(II)-dioxygenase folds fall into the generic
  "substrate/ligand(other)" bin (weight 0.45). Worked through JARID2 (see below).

**JARID2 investigation (why it scores only 0.076):** two separable effects.
1. *Systematic class gap* — 2-OG/α-KG is not a recognised cofactor class, so even the
   catalytically **active** demethylases KDM4A–F are binned as generic substrate and score
   ~0.31. Adding a proper 2-OG redox-class weight (~0.85) would lift active KDM4A to ~0.60.
2. *Genuine pocket loss* — JARID2's Fe(II)-coordinating HxD…H facial triad is degraded
   (pocket-retention 0.18 vs 1.00 in active KDM4A). Even with a corrected α-KG weight it would
   reach only ~0.14. Its low score is therefore **mostly correct biology**: JARID2 has lost
   the cofactor pocket, not merely been mis-binned.

**Decision:** 2-OG/α-KG is flagged in-panel as a class to add in a future scoring pass. It
was **not** added now because (a) the affected genuine pseudoenzyme set is essentially just
JARID2, whose score is dominated by real pocket loss, and (b) the change would mostly inflate
scores of catalytically *active* KDMs, which are outside the pseudoenzyme scope. Documented
rather than silently patched.

**Validation:** JSON payload parses (2670 records, all move columns present); esprima
`parseScript` clean (ES5/ES6); QuickJS full-script execution OK — `mrCell`, `sensorPanel`,
`render()`, and the sensor-only toggle all run; AHCYL1 confirmed 0.574 / redox-cofactor(NAD)
/ measurable / observed_concordant; JARID2 confirmed 0.076.


---

## v2.2 update — metabolite-relevance made compound-agnostic (2026-07-02)

**Rationale (user call):** the cofactor-class weight was a value judgment the score
shouldn't make — a metal, phosphate, or nucleotide sensor is no less interesting than an
NAD sensor. The score should measure *whether a small-molecule pocket survives*, not *which*
compound it holds.

**Change:** dropped the cofactor-class-weight factor entirely. The formula is now two factors:

`metabolite-relevance = pocket-retention × structural confidence`

- The **compound class is now purely descriptive** (`mr_top_class`, shown as "sensed compound
  class") — still filterable, but it no longer up- or down-weights the number.
- `mr_class_weight` retained in the dataframe as `mr_class_weight_old` metadata only; not used
  in scoring or display.
- The old class weights lived in `family_mr_weights.csv`; that table is now historical.

**Why this is safe against macromolecular "ligands":** proteins whose top ligand is a
macromolecule (ubiquitin/peptide/phospho-substrate — USP17 family, RHBDF1/2, PTEN, PTPRN2)
all have `pocket_retention = 0.0`, so the pocket-retention factor already zeroes them. No
class penalty was doing that work; dropping it promotes nothing spurious. Verified: 0 of 21
macromolecular-ligand positives have a nonzero pocket.

**Re-binning:** the old bins were calibrated against a class-weighted score (typically <1);
removing the sub-1 weight shifts the distribution up, so thresholds were recalibrated to the
new score's meaning — **high ≥ 0.50, medium ≥ 0.25, low < 0.25**. Among the 479 positives:
66 high / 195 medium / 218 low. Display color thresholds in `mrCell`/`sensorPanel` updated to
match (.50 / .25).

**Effect on key candidates:**
- **AHCYL1 / AHCYL2** — unchanged at **0.574** (NAD was already weight 1.0). Still measurable /
  observed_concordant.
- **Metal sensors promoted to the top band:** CPE (carboxypeptidase E, zinc) 0.14 → **0.70**;
  PSMB3 0.13 → **0.67**. These now rank alongside the nucleotide/NAD candidates, as intended.
- **Active demethylases** KDM4A–F 0.31 → **0.70** (intact pockets, no longer penalised for a
  missing α-KG class label).
- **JARID2** 0.076 → **0.168** — still low, because the driver was always genuine pocket loss
  (pocket-retention 0.18), never the compound-type penalty. Now binned `low`.
- Recomputed for all 2670: `metabolite_relevance`, `metabolite_relevance_bin`, `mr_rank`
  (min-rank over all records), `sensor_priority` (= MR × positive flag).

**α-ketoglutarate note:** the earlier "class gap" limitation is largely moot — with an
agnostic score, 2-OG being unlisted as a descriptor no longer suppresses any number. It
remains a future *descriptor* addition (label only), not a scoring fix.

**Validation:** JSON parses (2670 records, all move columns); esprima `parseScript` clean;
QuickJS executes mrCell/sensorPanel/render()/sensor-toggle; AHCYL1 = 0.574 / high /
measurable / observed_concordant; CPE = 0.70 / high / metal; JARID2 = 0.168 / low — all
confirmed in the rebuilt artifact.


---

## Panel rewrite — unified Methods narrative

The About / Methods panel was consolidated from a "9 base steps + bolted-on v2 layer" structure
(with a redundant summary box and `vN·` sub-labels) into **one continuous 11-step pipeline**.
The three refinements (death-motif re-scoring, compound-agnostic metabolite-relevance, experimental
cofactor channel) are folded into their natural positions rather than quarantined as a "v2" section.
No data or scoring changed — write-up only.

---

## gnomAD constraint — dropped per-residue signal, kept gene-level

**Problem.** The panel claimed a per-residue signal: "a catalytic/binding residue depleted of
missense variation is under selection → still matters even when catalysis is lost." Direct test on
the data does **not** support this at single-codon resolution:

- **72.9%** of catalytic sites already carry ≥1 missense variant in gnomAD v4 — so "no variant seen"
  (the intuitive signal) almost never fires; a single codon is only ~1–2 expected variants even under
  no selection.
- **Retained** active-site residues are **not** measurably more variant-depleted than **lost**
  (substituted) ones: P(any variant) 0.709 vs 0.727 (2-proportion z = −1.5, n.s.); median max-AF of
  observed variants 2.6e-6 vs 3.4e-6. Same null within the dead pseudoenzymes (0.696 vs 0.719).
- What little site-level depletion exists just tracks **gene-level** constraint (observed-site median
  max-AF 1.4e-6 in constrained genes, oe<0.6, vs 4.7e-6 in relaxed genes, oe≥0.9) — i.e. the per-site
  badge was largely re-reporting the gene number.
- Coverage was thin anyway: only 631 / 2670 proteins had a reliable per-residue overlay.

**Change.**
- **Display:** removed the per-residue constraint block from the detail panel (`resChips` function +
  the `R=G.res` verdict/section renderer + the "N/M depleted of missense" markup). Gene-level chips
  (LOEUF, missense o/e↑, pLI) are unchanged. The Pfam domain diagram (`pepFig`) still uses catalytic
  /substrate residue **positions** for tick-marks — that's placement, not a constraint claim, so it stays.
- **Methods text (step 8):** rewritten to describe gene-level constraint only, explicitly noting it is a
  *supporting annotation, not a ranking axis* (positives sit at ~background gene-constraint: median
  LOEUF 0.89 vs 0.90), and stating why the per-residue version was dropped.

**Validation:** JSON parses (2670 records); esprima clean; QuickJS runs `gnomadPanel` (gene-level chips
present, per-residue markup absent), `render()`, `setMode('info')`, `pepFig` callable; `resChips` no
longer defined; AHCYL1 = 0.574 / high / measurable / observed_concordant — unchanged.

---

## Annotation-quality guards — off-domain cofactor peptides & gene-symbol collisions

**Motivation.** Reviewing the titin (TTN, Q8WZ42) record exposed two annotation
failure modes that scale with protein size and gene-symbol ambiguity, independent of
the metabolite-relevance score itself.

**Problem 1 — cofactor peptides outside the catalytic domain.** The PISA/PELSA
cofactor channel reports binding at *peptide* resolution. In a very large protein a
handful of peptides reach significance by chance, thousands of residues from the
scored catalytic domain. Titin (~34,000 aa) picked up FAD/FMN/NADPH/PQQ hits — all in
its Ig/Fn3 structural region (peptides ~7987–20418), none within the titin-kinase
domain (32179–32432). The channel had already self-flagged (`experimental_channel =
not_applicable`, `cofactor_concordance = no_prediction`), but the chips still displayed
as if they were cofactor-sensing evidence.

**Fix 1 (display-level).** Each cofactor's protected peptides are tested for overlap
with the scored catalytic-domain window (±50 aa). Two new per-record flags:
- `cof_offdomain` — cofactors whose peptides all fall outside the catalytic domain (430 records).
- `cof_all_offdomain` — the whole cofactor channel is off-domain, no in-domain support (83 records).

Rendering is two-tier:
- **Fully off-domain** (e.g. titin) → red banner: "every significant cofactor is protected
  outside the catalytic domain … treat this cofactor channel as uninformative."
- **Partially off-domain** (e.g. AHCYL1, where THF at 41–53 sits in the N-terminal
  regulatory extension but NAD/etc. bind in-domain) → quiet amber note; the in-domain
  cofactors keep the signal. Off-domain chips get a ⚑ marker + tooltip either way.
- The rate scales cleanly with length (frac with any off-domain: 0.31 <1kaa → 1.0 >5kaa),
  confirming it is a length artifact, not biology.

**Problem 2 — gene-symbol collisions in the literature screen.** The PubMed co-mention
screen keys on gene symbol. "TTN" is also the standard abbreviation for *total turnover
number* in biocatalysis, so titin's five "confirming" PMIDs were about Rieske
oxygenases, ω-transaminases, and CRISPR PAM selection — none about titin. This produced
a false `confirmed` (pseudoenzyme-support) literature status.

**Fix 2 (display-level).** A curated methods-acronym set (`TTN`=total turnover number,
`TON`, `TOF`, `PAM`) attaches a `lit_symbol_ambig` caveat that renders as an amber
warning in the literature box, telling the reader the symbol collides with an unrelated
technical term and that the hits need individual verification. Only symbols whose
acronym is unrelated to the gene's own identity are included — genuine enzyme acronyms
(CAT=catalase, CAD, ACE) are deliberately excluded. In the current DB, TTN is the only
record where this corrects a false `confirmed` status.

**Neither guard alters ranking.** metabolite_relevance stays = pocket_retention ×
struct_conf (verified max deviation 0.0001 across all 2670); no affected positive drew
concordant support from an off-domain peptide (`observed_concordant` count among
fully-off-domain positives = 0). Both are display-level caveats only.

**Validation:** JSON parses (2670 records, all three new flags present); esprima clean;
QuickJS renders the full `openD` detail panel — titin shows the red cofactor banner,
⚑ chips, and the literature symbol caveat; AHCYL1 shows the amber partial-note (no red
banner), its sensor breakdown intact, and no false literature caveat.


---

## v8 — mycelium review response: F1/F2/F3 fixes (2026-07-04)

Applied the `arjunrajlaboratory/mycelium` `/mycelium:review` rubric (six lenses, Major/Minor
ladder) to the whole tool. Three Major findings were raised and are now addressed. Full audit:
`MYCELIUM_REVIEW.md`.

### F1 — Death-motif gate flipped active kinases to "dead" on a single missed VAIK-lysine  *(Major → fixed)*

**Problem.** The Move-1 gate called a protein-kinase-fold domain dead whenever <3 of 3 motifs
(VAIK-K / HRD-D / DFG-D) were detected. The VAIK β3-lysine detector has a high false-negative
rate: **36 of 68 ePK "dead" calls rested on losing only VAIK, with HRD and DFG both intact.**
This promoted ~42 canonically **active** kinases to `override_pos` — FGFR2/3/4, PDGFRA, NTRK1/2,
MEK1/2 (MAP2K1/2, at MR 0.70 "high"), DDR1/2, LCK, ITK, JAK3, PLK1, STK11/LKB1, CDK6, the four
WNKs — as if they were metabolite-sensing pseudoenzymes.

**Fix.** Family-specific rule: an ePK domain is death-motif-dead only if the catalytic
**HRD-Asp or DFG-Asp** is substituted, **or ≥2 of 3 motifs** are lost. VAIK-lysine loss *alone*
is no longer death (weakest single-motif evidence, least reliable column). Death-motif-dead
count **92 → 38**; `override_pos` **479 → 435**. **36 ePK rescued** to active-fold. Each affected
record carries a `motif_gate_note` / `motif_gate_class` shown on the detail card ("Active-fold
(rescued): HRD-Asp and DFG-Asp both intact; only VAIK…" vs "Death call: Lost catalytic
residue(s)…"). Non-kinase buckets (PTP CX5R, CASP His/Cys, RHB) are untouched — PTPRN2 etc.
still correctly dead.

**Honest cost.** KSR1/KSR2 are genuine pseudokinases whose only lesion is VAIK-lysine loss, so
the stricter rule now misses them (they revert to base-pipeline status). VRK3/PRAG1 are called
`not_applicable` (alignment too weak). This is a real recall/precision trade — see F2.

### F2 — "Specificity held at 1.00" was measured on a blind comparator set  *(Major → fixed)*

**Problem.** The v6/v7 methods claimed specificity 1.00 through the recall lift, but the shipped
benchmark had **no specificity/false-positive column**. The 23 gold "active comparators" happened
to contain **none** of the kinases the VAIK bug mislabelled, so 1.00 was true-but-uninformative.

**Fix.** Rebuilt the benchmark (`benchmark_v3.csv` / `benchmark_v3.png`) with an **expanded
74-gene active-kinase panel** (drug targets + textbook actives) as an explicit negative set, and
report specificity alongside recall, old rule vs new:

| Panel | old rule | new rule |
|---|---|---|
| Gold recall (43 positives) | 0.81 | **0.77** |
| Gold-comparator specificity (22) | 1.00 | 1.00 |
| **Active-kinase-panel specificity (74)** | **0.51** | **0.88** |

The old gate's *true* specificity on active kinases was **0.51** (34/74 wrongly dead), not 1.00.
The new rule trades ~4 points of gold recall for **+37 points of active-kinase specificity**. The
methods paragraph in the tool now states this honestly and no longer claims 1.00.

**Residual (documented).** 9/74 active kinases still score dead under the new rule (MKNK1/2,
STK32A/B/C, TSSK1B, EIF2AK4, STYK1, KALRN) — all lost DFG-Asp; genuinely atypical activation
loops. Flagged for follow-up, not silently passed.

### F3 — `struct_conf` is a near-constant (0.70 for 91% of records)  *(Major → disclosed)*

**Problem.** MR is presented as a two-factor product `pocket_retention × struct_conf` with both
bars shown, but `struct_conf = 0.70` for **2435/2670 (91.2%)** — a default floor where no
per-model active-site confidence was measured. For those, MR is effectively 0.70 × pocket_retention
and the second axis adds no independent information.

**Fix.** Added `struct_conf_source` (`default` 2435 / `measured` 235). The sensor panel now marks
the structural-confidence row **"(default)"** with a tooltip when the floor is applied, so a flat
axis is not over-read as evidence. MR itself is unchanged (product still exact, max dev 7.6e-5);
this is disclosure, not a re-score. Methods section documents the 0.70 floor.

**Validation (v8).** JSON parses (2670 records; `motif_gate_note`, `motif_gate_class`,
`struct_conf_source` present); esprima clean; QuickJS `openD` render confirmed: FGFR2 & MEK1 show
the "Active-fold (rescued)" note + intact badge; PTPRN2 stays dead; KSR1 shows rescued (the
documented cost); every record shows the "(default)" flag where the 0.70 floor applies. MR =
pocket × conf integrity held (max dev 7.6e-5). Guards and rankings from v7 unaffected.


---

## v9 — struct_conf made a live axis for the whole table (2026-07-04)

**Follow-up to F3.** The v8 fix *disclosed* that `struct_conf = 0.70` for 2435/2670 (91%) records
but left the placeholder in place — so metabolite-relevance was still, for most proteins, just a
rescaled `pocket_retention` (within that group MR vs pocket Spearman = 1.000; the second factor
carried zero ranking information). A reader reasonably asked whether that made MR "pretty useless."
It largely did for 91% of the table. This release fixes the root cause instead of only flagging it.

**What changed.** Fetched the AlphaFold model for **every** protein (2659/2670 present; EBI AFDB
v4/v6) and set `struct_conf` from real per-model confidence, with an explicit source hierarchy:

| `struct_conf_source` | n | definition | panel tag |
|---|---|---|---|
| `measured` | 235 | original residue-specific active-site pLDDT (unchanged) | (active-site) |
| `domain_mean` | 2,424 | mean pLDDT over the catalytic/pocket domain range | (domain pLDDT) |
| `unavailable` | 11 | no AlphaFold model — giant-protein fragments (TTN, OBSCN, MDN1, DYNC1H1, RANBP2, USP34) + selenoproteins (TXNRD1/2/3, MSRB1, TG); keep 0.70 | (no model) |

The flat-0.70 share dropped from **91.2% → 0.4%**. The confidence axis is now live for 99.6% of
records. Normalization recovered exactly from the 235 measured pairs: `struct_conf =
clip((pLDDT − 50)/45, 0, 1)` (max dev 5e-5; pLDDT 50→0, 95→1.0, and the old 0.70 default = pLDDT 81.5).

**Why domain-mean and not residue-specific for the 2,424.** Catalytic-residue positions were only
ever mapped for the 235; the other 2,435 never had them (that is *why* struct_conf defaulted). The
domain-mean is the consistent measure computable for all. Caveat, measured directly: on the 235
where both exist, domain-mean correlates with the residue-specific value (Pearson 0.57, median
identical) but **overstates** confidence when the catalytic residue sits in a disordered loop inside
an otherwise-folded domain (e.g. small GTPases RHOBTB1/2, RAB40, REM1/2: residue pLDDT 44–57 vs
domain-mean 83–88). Domain-mean is therefore an upper bound on active-site confidence; the 235
residue-specific values are kept precisely because they are the stricter measure.

**Effect on scores.** MR recomputed = pocket_retention × struct_conf for all records (integrity now
exact, max dev 0.0). High-band positives **56 → 112** — well-folded retained
pockets that the placeholder had been suppressing. Notable: **AHCYL1 / AHCYL2 (IRBIT) 0.574 → 0.820**
(domain pLDDT 95–96 → struct_conf 1.0; MR now equals pocket_retention, the honest reading — pocket
retained *and* high structural confidence). Genuine pocket loss still zeroes MR regardless of
confidence (NNT stays 0.00). Known pseudokinases land sensibly in medium (KSR1 0.42, TRIB1/2/3, ILK).

**Bin movement:** 517/2670 records change bin; overall high 902→1325, medium 853→481, low 915→864.
The shift is upward because most real active-site domains fold above pLDDT 81.5, so the 0.70 floor
had been deflating them.

**Validation (v9).** 2670 records parse; three source tags render (AHCYL1 → "(domain pLDDT)",
ASNSD1 → "(active-site)", TTN → "(no model)"); esprima clean; QuickJS `openD` confirmed; MR =
pocket × conf exact (dev 0.0). F1 rescued-notes and F2 benchmark unaffected (struct_conf is
orthogonal to the death-motif gate). Per-protein pLDDT table saved as `active_site_plddt_v9.csv`.

---

## v10 — "Database evaluation" tab (independent benchmark + leakage correction)

**New fourth tab.** Added a *Database evaluation* mode that scores the tool against an
**independent, literature-curated reference set** of known pseudoenzymes across seven classes
(pseudokinase, pseudophosphatase, pseudo-GTPase, pseudoprotease, pseudo-DUB, metabolic, cofactor)
plus active comparators drawn from the *same folds* (BRAF for pseudokinases, PTPN1 for
pseudophosphatases, USP7 for pseudo-DUBs, etc.). Truth labels come from the Murphy / Eyers /
Ribeiro / Todd / Tonks / Manning pseudoenzyme reviews and are independent of any tool score.
Reference set: 139 proteins (86 pseudoenzymes + 53 active comparators); 120 present in the DB
(73 pseudo + 47 active).

**Train/test leakage found and corrected (mycelium review).** The death-motif gate was tuned on a
69-protein gold set; 43/73 in-DB pseudoenzymes and 22/47 active comparators overlap it by UniProt
accession. Reporting a single number over all 120 would report partly on training data and inflate
recall. The tab now **leads with out-of-sample metrics** on the 55 disjoint proteins and shows the
all-in-DB numbers second, labelled as including tuning-set members. An "in gold tuning set" column
and a "show only out-of-sample" filter make the split reproducible in the table.

**Headline metrics.**
- **Out-of-sample (n = 30 pseudo + 25 active, never in tuning set): Sensitivity 0.63 [0.46–0.78], Specificity 0.96 [0.81–0.99].**
- All in-DB (optimistic, includes tuning set): Sensitivity 0.71 [0.60–0.80], Specificity 0.98 [0.89–0.996].
- Per-class sensitivity: pseudoprotease 3/3, cofactor 2/2, pseudo-GTPase 7/8 (0.88), pseudokinase 28/35 (0.80), metabolic 2/3, pseudophosphatase 10/17 (0.59), **pseudo-DUB 0/5**.
- Sole false positive: PTEN (weak protein-phosphatase; flagged by the CX5R gate).

**MR is a pocket-retention score, not a deadness detector.** Panel (a) shows MR is *higher* in
active enzymes (median 0.48 vs 0.23; AUC pseudo>active = 0.35, below 0.5 by construction). The
dead-call gate is the classifier; MR ranks how much pocket a dead protein retains.

**Disclosed limitations.** The gate has no reach on pseudo-DUBs (no linear death motif on USP/OTU
folds — 0/5); 19 literature pseudoenzymes are out of DB scope; several classes rest on small n
(wide Wilson CIs shown). Full analysis in `EVAL_MYCELIUM_REVIEW.md`.

**New data files.** `data/eval_reference_set.csv` (139-protein reference set),
`data/eval_scored.csv` (per-protein scores + dead-call + in-gold flag),
`data/eval_metrics.json` (sens/spec + Wilson CIs + OOS block + overlap block).

---

## v11 — Metabolite-sensor–enriched evaluation (out-of-sample only)

**Motivation.** The database's primary use is surfacing **metabolite sensors**, so the evaluation
reference set was expanded to cover that class in depth, and — per request — the tab now reports
**only out-of-sample metrics** (the "all in-DB" optimistic numbers were removed).

**Expanded reference set.** Metabolic + cofactor pseudoenzymes grew from 7 to **14 in-DB proteins**,
each matched to active enzymes of the same fold:
- **Acatalytic carbonic anhydrases (CARPs):** CA8, CA10, CA11 (lack Zn-coordinating His) vs active CA1/CA2/CA9/CA12
- **ALDH "dead enzymes":** ALDH16A1 (lacks catalytic Cys) vs active ALDH1A1/2/3A1/7A1/9A1
- **Pseudo-NDPKs:** NME7/8/9 vs active NME1/2/3/4
- **Pseudo-amidases:** PGLYRP1/3/4 vs the sole active amidase PGLYRP2
- **SAHH paralogs (IRBIT prototype):** AHCYL1/AHCYL2 vs active AHCY; plus ASNSD1, GOT1L1
Reference set total: 161 proteins (95 pseudo + 66 active); 142 in DB.

**Out-of-sample metrics (only numbers reported).** Restricting to the 39+38 proteins whose
UniProt accession never entered the gold gate-tuning set:
- **Sensitivity 0.59 [0.43–0.73], Specificity 0.97 [0.86–0.99]** (n = 39 pseudo + 38 active).
- Per-class out-of-sample sensitivity: pseudokinase 11/14, pseudo-GTPase 3/3, pseudophosphatase 4/10, metabolic 4/7, cofactor 1/3, pseudo-DUB 0/2.
- Sole false positive: PTEN.

**Key finding for metabolite sensing.** Specificity on metabolic/cofactor folds is near-perfect
(no active metabolic enzyme is called dead), but the **linear death-motif gate does not reach several
genuine metabolite-sensor candidates** — CA8 (MR 0.88), CA10 (0.62), NME7/NME9 (~0.56) are missed
because CARP and NDPK folds have no scannable death motif. **MR, not the dead-call gate, is what
surfaces these** — reinforcing that MR is the metabolite-sensor discovery signal and the gate is a
conservative pseudoenzyme classifier.

**Tab changes.** Evaluation cards reduced to the two out-of-sample numbers; "show only out-of-sample"
table filter now defaults ON; per-class and coverage narrative recomputed on the out-of-sample split;
figure redrawn (metabolic/cofactor classes highlighted, all panels out-of-sample).
