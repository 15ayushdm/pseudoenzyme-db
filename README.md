# Human PseudoenzymeDB Explorer

A self-contained, interactive explorer for **catalytically dead pseudoenzymes that retain a small-molecule pocket** — the IRBIT / AHCYL1 "metabolite-sensor" pattern (a dead enzyme that still binds its cofactor).

**Live tool:** https://15ayushdm.github.io/pseudoenzyme-db/

The explorer scores **2,670 human proteins across 919 catalytic families** and ranks candidates by whether they have (a) lost catalysis and (b) kept a pocket that could still sense a metabolite, cofactor, or metal.

## What's in this repo

| File | Description |
|------|-------------|
| `index.html` | The explorer — a single self-contained HTML file (all data embedded; no server needed). This is what the live Pages site serves. Open it locally or use the link above. |
| `explorer_features.py` | Re-appliable feature layers for `index.html` (see below). |
| `EXPLORER_V2_CHANGELOG.md` | Full build log and rationale for every analytical step and revision. |
| `data/metabolite_relevance.csv` | Per-protein metabolite-relevance scores and bins. |
| `data/motif_calls.csv` | Family-specific death-motif calls (VAIK/HRD/DFG, CX5R, GHKL). |
| `data/benchmark_by_class_v2.csv` | Recall/specificity benchmark on 43 gold-standard pseudoenzymes. |
| `data/cofactor_channel.csv` | Experimental cofactor channel (PISA/PELSA) and concordance tiers. |

## How the pipeline works (summary)

1. **Catalytic-residue detection** — per-family M-CSA catalytic/substrate/cofactor residues tested for intactness against every matching human protein.
2. **Family-specific death motifs** — explicit kinase/phosphatase/GHKL signatures override the generic call (recall 0.67 → 0.86 on gold-standard pseudoenzymes).
3. **Structural confirmation** — AlphaFold active-site geometry + pLDDT.
4. **Domain architecture** (Pfam/InterPro) — only whole-protein pseudoenzymes are called.
5. **Extended catalytic templates** from UniProt active-site annotations.
6. **Metabolite-relevance** = pocket-retention × structural confidence — compound-agnostic (a metal or nucleotide sensor scores like an NAD sensor).
7. **Experimental cofactor binding** — PISA & PELSA proteome-wide screens; concordance with the predicted cofactor (this is how AHCYL1/NAD was confirmed).
8. **Population constraint** — gene-level gnomAD v4 (LOEUF, pLI, missense o/e) as context.
9. **Functional genomics** — DepMap co-essentiality.
10. **Literature validation** — PubMed + UniProt screen.
11. **Expression** — Human Protein Atlas tissue/cell-type context.

Full detail is in the tool's **About** panel and in `EXPLORER_V2_CHANGELOG.md`.

## Exporting what you see

Every table has an **⤓ Export CSV** button next to the result count. The download reflects the view
you are currently looking at — search string, toggles, chips and sort order — and the filter is
recorded in the filename, e.g.
`pseudoenzymedb_candidates_search-nad_sensor-only_sort-metabolite-relevance-desc_2026-08-16.csv`.

The export contains the **full filtered set**, not just the 500 rows the page draws, and reads values
from the underlying data (full numeric precision, no markup). Secondary buttons widen the column set:
`all fields` on the candidate table (83 columns — motif gate, pocket retention, structural
confidence, experimental channel, DepMap breakdown), and `+ rationales & claims` on the literature
table (adds every PMID-backed claim and the reference list). Files are UTF-8 with a BOM so Excel
opens accented ligand names correctly.

## Rebuilding the explorer

`index.html` has no upstream generator — it is maintained by patching. All post-base features live in
`explorer_features.py` as numbered, marker-guarded layers:

```bash
python3 explorer_features.py --file index.html --check   # which layers are present
python3 explorer_features.py --file index.html           # apply any that are missing
```

Re-running is a no-op, and every edit asserts it matched exactly once, so a layer fails loudly rather
than mispatching if the base HTML changes shape. Run it after regenerating the base file.

## Note on file size

`index.html` is ~22 MB because the complete scored dataset — including the 478-protein literature
review with its claims and references — is embedded directly in the page. This is intentional, so the
tool runs entirely offline with no backend.
