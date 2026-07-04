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
