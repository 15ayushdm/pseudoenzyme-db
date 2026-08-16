#!/usr/bin/env python3
"""Re-appliable feature layers for the PseudoenzymeDB explorer.

The explorer HTML is maintained by in-place patching (there is no live generator
for v3 -- prototype/make_explorer.py builds v1 only and writes to a dead path).
This script is the generator substitute: every custom feature added after the
base HTML is written lives here as a numbered LAYER, and running the script
brings any explorer file up to date with all of them.

    python3 explorer_features.py                     # patch the default file in place
    python3 explorer_features.py --file other.html   # patch a different file
    python3 explorer_features.py --check             # report status, change nothing
    python3 explorer_features.py --no-backup         # skip the .bak.html copy

Each layer is guarded by a marker string, so the script is idempotent: layers
already present are skipped, and a layer is only ever applied to a file that
does not have it. Every edit asserts it matched exactly once, so a layer fails
loudly rather than silently mispatching if the base HTML changes shape.

LAYERS
  1  EXPORT_LAYER v1  -- "Export CSV" buttons on the candidate, literature and
                         benchmark tables; serialise the current filter+sort.
  2  DEPM_COLUMN v1   -- "Metabolic" column (DepMap metabolic-coessentiality
                         score) on the main candidate table, plus the DepMap
                         panel in the protein detail modal, plus the matching
                         CSV columns.
"""
import argparse
import datetime as _dt
import os
import shutil
import sys

DEFAULT_FILE = "pseudoenzyme_explorer_v3.html"


class Patcher:
    """Applies replacements to a string, asserting each matches exactly once."""

    def __init__(self, text):
        self.text = text
        self.log = []

    def sub1(self, old, new, label):
        n = self.text.count(old)
        if n != 1:
            raise AssertionError(
                f"{label}: expected exactly 1 match in the HTML, found {n}. "
                "The base file has changed shape; update this layer."
            )
        self.text = self.text.replace(old, new, 1)
        self.log.append(label)


# ===========================================================================
# LAYER 1 -- CSV export
# ===========================================================================
EXPORT_MARKER = "EXPORT_LAYER v1"

EXPORT_JS = r"""
<script>
/* ==================== EXPORT_LAYER v1 -- table -> CSV ====================
   Serialises whatever the user is currently looking at: active search string,
   active toggles / chips, active sort order. Values come from the underlying
   data objects (full numeric precision, no HTML), so the export is not capped
   at the 500 rows the DOM renders. */
(function(){
 const BOM='\ufeff';
 function flat(v){
  if(v===null||v===undefined)return '';
  if(Array.isArray(v))return v.map(flat).join('; ');
  if(typeof v==='object')return JSON.stringify(v);
  return String(v)}
 function cell(v){
  let t=flat(v).replace(/\r?\n/g,' ').replace(/[ \t]+/g,' ').trim();
  if(/^[=+@]/.test(t))t="'"+t;                       /* spreadsheet formula guard */
  return /[",]/.test(t)?'"'+t.replace(/"/g,'""')+'"':t}
 function csv(cols,rows){
  const head=cols.map(c=>cell(c.h)).join(',');
  const body=rows.map(r=>cols.map(c=>{let v;try{v=c.f(r)}catch(e){v=''}return cell(v)}).join(','));
  return BOM+[head].concat(body).join('\r\n')+'\r\n'}
 function dl(name,text){
  const b=new Blob([text],{type:'text/csv;charset=utf-8'}),u=URL.createObjectURL(b),
        a=document.createElement('a');
  a.href=u;a.download=name;document.body.appendChild(a);a.click();
  setTimeout(function(){URL.revokeObjectURL(u);a.remove()},500)}
 const slug=t=>(t||'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'').slice(0,40);
 const stamp=()=>new Date().toISOString().slice(0,10);
 function fname(base,parts){
  const p=(parts||[]).filter(Boolean).map(slug).filter(Boolean);
  return ['pseudoenzymedb',base].concat(p).join('_')+'_'+stamp()+'.csv'}
 function flash(btn,n){
  if(!btn)return;const old=btn.innerHTML,w=btn.offsetWidth;
  btn.style.minWidth=w+'px';btn.classList.add('done');
  btn.innerHTML='\u2713 '+n+' row'+(n===1?'':'s');
  setTimeout(function(){btn.innerHTML=old;btn.classList.remove('done');btn.style.minWidth=''},1800)}
 function go(btn,base,parts,cols,rows){
  if(!rows||!rows.length){flash(btn,0);return}
  dl(fname(base,parts),csv(cols,rows));flash(btn,rows.length)}

 /* ---------------- candidate table (Pseudoenzyme candidate / Ligand tabs) --- */
 const LITLAB={confirmed:'pseudoenzyme support',novel:'weak/novel',
   uncharacterized:'uncharacterised',likely_active:'likely active'};
 const rev=x=>REVIEW[x.target_acc]||null;
 const dep=x=>(typeof DEPM!=='undefined'&&DEPM[x.target_acc])||null;
 const CAND_COLS=[
  {h:'gene',f:x=>x.gene},
  {h:'uniprot',f:x=>x.target_acc},
  {h:'protein_name',f:x=>(x.name||'').replace(/\s*\(EC [^)]*\)/g,'').trim()},
  {h:'home_family',f:x=>x.home_family_name},
  {h:'ec',f:x=>x.ec},
  {h:'confidence',f:x=>x.rescope?'Active + pseudo-domain':tinfo(x.integrated_tier)[2]},
  {h:'integrated_tier',f:x=>x.integrated_tier},
  {h:'catalytic_intact_fraction',f:x=>x.catalytic_intact_fraction},
  {h:'substrate_intact_fraction',f:x=>x.substrate_intact_fraction},
  {h:'cofactor_intact_fraction',f:x=>x.ligand_intact_fraction},
  {h:'metabolite_relevance',f:x=>x.metabolite_relevance},
  {h:'metabolite_relevance_bin',f:x=>x.metabolite_relevance_bin},
  {h:'sensed_compound_class',f:x=>x.mr_top_class},
  {h:'gnomad_missense_z',f:x=>x.mis_z},
  {h:'gnomad_loeuf',f:x=>x.loeuf},
  {h:'cofactor_exp_measurable',f:x=>x.cof_meas?1:0},
  {h:'cofactor_exp_n_significant',f:x=>x.cof_sig},
  {h:'cofactor_exp_n_matching_predicted',f:x=>x.cof_match},
  {h:'metabolic_coessentiality',f:x=>{const d=dep(x);return d?d.ds:''}},
  {h:'coessential_frac_metabolic',f:x=>{const d=dep(x);return d?d.fm:''}},
  {h:'coessentiality_informative',f:x=>{const d=dep(x);return d?(d.inf?1:0):''}},
  {h:'literature_status',f:x=>x.lit?(LITLAB[x.lit.s]||x.lit.s):''},
  {h:'literature_n_pubs',f:x=>x.lit?x.lit.npub:''},
  {h:'literature_note',f:x=>x.lit?x.lit.n:''},
  {h:'literature_pmids',f:x=>x.lit&&x.lit.pmids?x.lit.pmids.join(' '):''},
  {h:'review_catalytic_verdict',f:x=>{const r=rev(x);return r?RV_LAB[r.cv]:''}},
  {h:'review_evidence_tier',f:x=>{const r=rev(x);return r?r.ct:''}},
  {h:'review_sensor_biology',f:x=>{const r=rev(x);return r?rvp(r.sv):''}},
  {h:'uniprot_pseudo_annotation',f:x=>x.uniprot_pseudo_annotation}];

 /* wide export: every field that is scalar in EVERY row, preferred order first */
 const CAND_PREF=['gene','target_acc','name','syn','ec','home_family','home_family_name',
  'integrated_tier','rank','base_status','rescope','catalytic_intact_fraction',
  'substrate_intact_fraction','ligand_intact_fraction','n_domains','n_active','n_degenerate',
  'n_conserved','n_ambiguous','motif_dead','motif_gate_class','motif_gate_note','base_pos',
  'override_pos','struct_flag','constellation_rmsd','active_site_plddt','struct_conf',
  'struct_conf_source','pocket_retention','metabolite_relevance','metabolite_relevance_bin',
  'mr_rank','mr_top_class','experimental_channel','cofactor_concordance','expected_cofactor',
  'n_cof_observed','cof_meas','cof_sig','cof_match','cof_score','mis_z','mis_con','loeuf',
  'lit_score','existing_activity_evidence','uniprot_pseudo_annotation','func'];
 let _candAll=null;
 function candAllCols(){
  if(_candAll)return _candAll;
  const bad=new Set(['rv_sort','dm_sort']),keys=new Set();
  ROWS.forEach(function(r){for(const k in r)keys.add(k)});
  ROWS.forEach(function(r){for(const k in r){const v=r[k];
    if(v!==null&&typeof v==='object')bad.add(k)}});
  const scal=Array.from(keys).filter(k=>!bad.has(k));
  const ordered=CAND_PREF.filter(k=>scal.indexOf(k)>=0)
    .concat(scal.filter(k=>CAND_PREF.indexOf(k)<0).sort());
  _candAll=ordered.map(k=>({h:k,f:(function(kk){return x=>x[kk]})(k)})).concat([
   {h:'confidence_label',f:x=>x.rescope?'Active + pseudo-domain':tinfo(x.integrated_tier)[2]},
   {h:'ligands',f:x=>(x.ligands||[]).map(l=>l.n+' ['+l.r+(l.v===false?', via homology':'')+']').join('; ')},
   {h:'cofactor_predicted',f:x=>(x.cofactor_predicted||[]).join('; ')},
   {h:'cofactor_observed',f:x=>(x.cofactor_observed||[]).join('; ')},
   {h:'literature_status',f:x=>x.lit?(LITLAB[x.lit.s]||x.lit.s):''},
   {h:'literature_n_pubs',f:x=>x.lit?x.lit.npub:''},
   {h:'literature_note',f:x=>x.lit?x.lit.n:''},
   {h:'literature_pmids',f:x=>x.lit&&x.lit.pmids?x.lit.pmids.join(' '):''},
   {h:'review_catalytic_verdict',f:x=>{const r=rev(x);return r?RV_LAB[r.cv]:''}},
   {h:'review_evidence_tier',f:x=>{const r=rev(x);return r?r.ct:''}},
   {h:'review_sensor_biology',f:x=>{const r=rev(x);return r?rvp(r.sv):''}},
   {h:'review_sensor_priority',f:x=>{const r=rev(x);return r?r.sc:''}},
   {h:'review_n_refs',f:x=>{const r=rev(x);return r?r.nr:''}},
   {h:'depmap_composite_score',f:x=>{const d=dep(x);return d?d.ds:''}},
   {h:'depmap_frac_coessential_metabolic',f:x=>{const d=dep(x);return d?d.fm:''}},
   {h:'depmap_frac_nucleotide_cofactor',f:x=>{const d=dep(x);return d?d.fn:''}},
   {h:'depmap_q_metabolic',f:x=>{const d=dep(x);return d?d.q:''}},
   {h:'depmap_q_nucleotide',f:x=>{const d=dep(x);return d?d.qn:''}},
   {h:'depmap_top_coessential_r',f:x=>{const d=dep(x);return d?d.tr:''}},
   {h:'depmap_profile_informative',f:x=>{const d=dep(x);return d?(d.inf?1:0):''}},
   {h:'depmap_top_screen',f:x=>{const d=dep(x);return d?d.tn:''}},
   {h:'depmap_top_screen_z',f:x=>{const d=dep(x);return d?d.tnz:''}},
   {h:'depmap_n_screen_hits',f:x=>{const d=dep(x);return d?d.nh:''}},
   {h:'depmap_top_coessential',f:x=>(x.coess||[]).slice(0,10).map(c=>c[0]+' ('+c[1].toFixed(2)+')').join('; ')}]);
  return _candAll}
 function candTags(){
  return [mode==='ligand'?'ligand-mode':'',q?'search-'+q:'',
    inclact?'incl-active':'',sensoronly?'sensor-only':'',
    revfilt?'reviewed-inactive':'',revfp?'lit-refuted':'',
    'sort-'+sortK+(sortAsc?'-asc':'-desc')]}

 /* ------------------------------- literature-prioritization table ---------- */
 const LIT_COLS=[
  {h:'gene',f:z=>z.g},
  {h:'uniprot',f:z=>z.a},
  {h:'novel_sensor_priority',f:z=>z.nv},
  {h:'novel_sensor_top_metabolite',f:z=>z.nvm},
  {h:'catalytic_status',f:z=>RV_LAB[z.cv]||z.cv},
  {h:'catalytic_evidence_tier',f:z=>z.ct},
  {h:'sensor_biology',f:z=>rvp(z.sv)},
  {h:'sensor_evidence_tier',f:z=>z.st},
  {h:'transduction',f:z=>rvp(z.mech)},
  {h:'site_dependence',f:z=>rvp(z.sd)},
  {h:'functional_relevance',f:z=>rvp(z.rv)},
  {h:'kg_edges',f:z=>z.ne},
  {h:'metabolic_coessentiality',f:z=>z.dm},
  {h:'coessential_frac_metabolic',f:z=>z.dmf},
  {h:'coessentiality_informative',f:z=>z.dmi},
  {h:'established_sensor_score',f:z=>z.sc},
  {h:'n_refs',f:z=>z.nr},
  {h:'n_claims',f:z=>z.nc},
  {h:'flag_sensor_pseudoenzyme',f:z=>z.sp?1:0},
  {h:'flag_untested_opportunity',f:z=>z.opp?1:0},
  {h:'review_round',f:z=>z.coh===1?'tier-1':'expansion'}];
 const LIT_COLS_FULL=LIT_COLS.concat([
  {h:'catalytic_rationale',f:z=>z.cr},
  {h:'sensor_rationale',f:z=>z.sr},
  {h:'transduction_output',f:z=>z.down},
  {h:'site_dependence_note',f:z=>z.sdn},
  {h:'retained_binding_ligands',f:z=>(z.lig||[]).map(l=>l.n+(l.a?' ('+l.a+')':'')).join('; ')},
  {h:'claims',f:z=>(z.cl||[]).map(c=>'['+c.t+'; evidence '+c.e+'; PMID '+(c.p||[]).join('/')+'] '+c.x).join(' || ')},
  {h:'reference_pmids',f:z=>(z.rf||[]).map(f=>f.p).join(' ')},
  {h:'reference_titles',f:z=>(z.rf||[]).map(f=>f.t+' ('+f.j+' '+f.y+')').join(' || ')}]);
 function litTags(){
  const chip=document.querySelector('#litchips .lchip.on');
  return [chip?'chip-'+chip.textContent:'',litq?'search-'+litq:'',
    'sort-'+litSK+(litAsc?'-asc':'-desc')]}

 /* --------------------------------------- database-evaluation benchmark ---- */
 const EVAL_COLS=[
  {h:'gene',f:r=>r.g},{h:'uniprot',f:r=>r.u},
  {h:'truth',f:r=>r.t==='pseudo'?'pseudoenzyme':'active'},
  {h:'class',f:r=>r.c},
  {h:'dead_call',f:r=>r.indb?(r.dead===true?'dead':(r.dead===false?'not dead':'')):''},
  {h:'metabolite_relevance',f:r=>r.mr},{h:'mr_bin',f:r=>r.bin},
  {h:'struct_conf_source',f:r=>r.scs},{h:'truth_evidence',f:r=>r.ev},
  {h:'held_out',f:r=>r.hold?1:0},{h:'in_database',f:r=>r.indb?1:0},
  {h:'used_in_development',f:r=>(r.indb&&!r.hold)?1:0},
  {h:'call_correct',f:r=>{if(!r.indb||r.dead===null||r.dead===undefined)return '';
    return ((r.t==='pseudo')===(r.dead===true))?1:0}}];

 /* ------------------------------------------------------------- wiring ---- */
 function bind(id,fn){const b=document.getElementById(id);if(b)b.onclick=function(){fn(b)}}
 bind('expcand',   b=>go(b,'candidates',candTags(),CAND_COLS,_EXP.cand));
 bind('expcandall',b=>go(b,'candidates-allfields',candTags(),candAllCols(),_EXP.cand));
 bind('explit',    b=>go(b,'literature-review',litTags(),LIT_COLS,_EXP.lit));
 bind('explitall', b=>go(b,'literature-review-full',litTags(),LIT_COLS_FULL,_EXP.lit));
 bind('expeval',   b=>go(b,'benchmark',
   [(document.getElementById('evoos')||{}).checked?'held-out-only':'full-benchmark',
    'sort-'+_evsort.k+(_evsort.dir>0?'-asc':'-desc')],EVAL_COLS,_EXP.eval));
})();
</script>
</body></html>"""


def layer_export(p):
    """CSV export buttons on the candidate, literature and benchmark tables."""
    p.sub1(
        ".count{color:#6b7280;font-size:13px;margin:10px 0 14px}",
        ".count{color:#6b7280;font-size:13px;margin:10px 0 14px}\n"
        ".countrow{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}\n"
        ".countrow .count{margin:10px 0 14px;flex:1;min-width:180px}\n"
        ".expwrap{display:flex;align-items:center;gap:6px;white-space:nowrap}\n"
        ".expbtn{font:inherit;font-size:12px;font-weight:550;color:#1f6bb5;background:#fff;"
        "border:1px solid #c3d8ee;border-radius:7px;padding:5px 11px;cursor:pointer;line-height:1.3}\n"
        ".expbtn:hover{background:#eff6ff;border-color:#2563eb}\n"
        ".expbtn.alt{color:#6b7280;border-color:#e3e6ea;font-weight:500}\n"
        ".expbtn.alt:hover{background:#f8fafc;border-color:#c9ced6;color:#374151}\n"
        ".expbtn.done{color:#166534;border-color:#bbf7d0;background:#f0fdf4}",
        "export/css",
    )
    p.sub1(
        '<div class="count" id="count"></div>\n<table><thead><tr>',
        '<div class="countrow"><div class="count" id="count"></div>'
        '<span class="expwrap">'
        '<button class="expbtn" id="expcand" title="Download the table exactly as filtered and sorted right now '
        '(all matching rows, not only the first 500 displayed) as a CSV.">&#10515; Export CSV</button>'
        '<button class="expbtn alt" id="expcandall" title="Same rows, but every scalar field in the database '
        '(structure, motif, pocket, cofactor, constraint, DepMap and literature fields), not just the on-screen columns.">'
        'all fields</button></span></div>\n<table><thead><tr>',
        "export/candidate-buttons",
    )
    p.sub1(
        '<div class="count" id="litcount"></div>',
        '<div class="countrow"><div class="count" id="litcount"></div>'
        '<span class="expwrap">'
        '<button class="expbtn" id="explit" title="Download the reviewed-protein table as filtered '
        '(search box + chip) and sorted right now, as a CSV.">&#10515; Export CSV</button>'
        '<button class="expbtn alt" id="explitall" title="Same rows plus the full review text: catalytic and sensor '
        'rationales, transduction/output notes, every PMID-backed claim, and the reference list.">'
        '+ rationales &amp; claims</button></span></div>',
        "export/lit-buttons",
    )
    p.sub1(
        '<table class="evaltbl"><thead><tr>',
        '<div class="countrow" style="margin-top:8px"><div class="count" id="evcount"></div>'
        '<span class="expwrap"><button class="expbtn" id="expeval" '
        'title="Download the benchmark table as currently filtered and sorted, as a CSV.">'
        "&#10515; Export CSV</button></span></div>\n"
        '<table class="evaltbl"><thead><tr>',
        "export/eval-button",
    )
    p.sub1(
        "let revfilt=false, revfp=false;",
        "let revfilt=false, revfp=false;\n"
        "const _EXP={cand:[],lit:[],eval:[]};  /* " + EXPORT_MARKER + " capture slot */",
        "export/capture-slot",
    )
    p.sub1(
        " const need=(mode!=='candidate'&&!q);",
        " _EXP.cand=r;\n const need=(mode!=='candidate'&&!q);",
        "export/capture-candidates",
    )
    p.sub1(
        " document.getElementById('litcount').textContent=r.length+\" of \"+LITROWS.length+\" reviewed proteins\";",
        " _EXP.lit=r;\n"
        " document.getElementById('litcount').textContent=r.length+\" of \"+LITROWS.length+\" reviewed proteins\";",
        "export/capture-literature",
    )
    p.sub1(
        "  let h='';\n  for(const r of rows){",
        "  _EXP.eval=rows;\n"
        "  var _ec=document.getElementById('evcount');\n"
        "  if(_ec)_ec.textContent=rows.length+' of '+EVAL_ROWS.length+' benchmark proteins';\n"
        "  let h='';\n  for(const r of rows){",
        "export/capture-eval",
    )
    p.sub1("</body></html>", EXPORT_JS, "export/script")


# ===========================================================================
# LAYER 2 -- metabolic-coessentiality column on the main table
# ===========================================================================
DEPM_MARKER = "DEPM_COLUMN v1"

DEPM_TITLE = (
    "DepMap metabolic-regulation score (0-11): coessential wiring with KEGG-metabolic genes "
    "(hypergeometric, FDR-corrected) plus responsiveness across 22 nutrient / metabolic-stress "
    "CRISPR screens. Independent of the structural and literature axes. "
    "3+ = metabolically wired. &quot;flat&quot; marks a profile below the 0.25 informativeness gate, "
    "where 0 means untested on this axis rather than negative. "
    "&mdash; = outside the 478-protein reviewed set or no DepMap data; these sort last "
    "whichever way you sort."
)

DEPM_JS = r"""/* ==================== DEPM_COLUMN v1 -- metabolic coessentiality ==========
   Surfaces the DepMap metabolic-regulation score (built for the Literature
   prioritization tab) as a sortable column on the main candidate table, and
   adds the existing DepMap breakdown panel to the protein detail modal.
   Semantics preserved from the literature tab: a flat coessentiality profile
   (inf=0) scores 0 and is UNTESTED on this axis, not negative; a protein with
   no DEPM entry at all renders as an em-dash and sorts last.
   Defined in this block (not appended at end of file) because render() runs
   at load time in this same block, and function declarations do not hoist
   across <script> boundaries. */
function dmCell(x){
 const d=(typeof DEPM!=='undefined')?DEPM[x.target_acc]:null;
 if(!d||d.ds===null||d.ds===undefined)
  return '<span class=mut title="Not in the 478-protein reviewed set, or no DepMap coessentiality / screen data for this gene.">\u2014</span>';
 const v=d.ds, c=v>=3?'#0f766e':v>=1?'#5aa0d6':'#cbd5e1';
 return '<span class=bar><i style="width:'+(Math.min(v/11,1)*100)+'%;background:'+c+'"></i></span>'+v.toFixed(1)
  +(d.inf?'':'<br><span class=acc style="font-size:10px" title="Flat coessentiality profile \u2014 below the 0.25 informativeness gate, so this axis is untested rather than negative.">flat</span>')}
"""


def layer_depm(p):
    """Metabolic-coessentiality column on the candidate table + detail panel."""
    # --- header cell, placed after "Cofactor (exp)" so the experimental /
    #     functional-genomics evidence columns sit together
    p.sub1(
        '<th data-k="lit_score" title="Literature status:',
        '<th data-k="dm_sort" title="' + DEPM_TITLE + '">Metabolic</th>\n'
        '<th data-k="lit_score" title="Literature status:',
        "depm/header",
    )
    # --- body cell
    p.sub1(
        " <td>${conCell(x)}</td><td>${cofCell(x)}</td><td>${litCell(x)}</td>",
        " <td>${conCell(x)}</td><td>${cofCell(x)}</td><td>${dmCell(x)}</td><td>${litCell(x)}</td>",
        "depm/body-cell",
    )
    # --- sort key, computed per render alongside rv_sort
    p.sub1(
        " ROWS.forEach(x=>{const _r=REVIEW[x.target_acc];x.rv_sort=_r?RV_ORD[_r.cv]||0:-1});",
        " ROWS.forEach(x=>{const _r=REVIEW[x.target_acc];x.rv_sort=_r?RV_ORD[_r.cv]||0:-1;\n"
        "  const _d=(typeof DEPM!=='undefined')?DEPM[x.target_acc]:null;\n"
        "  x.dm_sort=(_d&&_d.ds!==null&&_d.ds!==undefined)?_d.ds:null});",
        "depm/sort-key",
    )
    # --- register as numeric so nulls become -Infinity, not empty strings
    p.sub1(
        "'lit_score','metabolite_relevance','mr_rank','rv_sort'].includes(sortK);",
        "'lit_score','metabolite_relevance','mr_rank','rv_sort','dm_sort'].includes(sortK);",
        "depm/numeric-sort",
    )
    # --- ...and then override that for dm_sort so missing data sorts last in
    #     BOTH directions. The table's default numeric rule maps null to
    #     -Infinity, which puts nulls last descending but FIRST ascending. That
    #     is tolerable on columns with a few gaps, but 151 of the 471
    #     default-view rows have no DepMap entry, so ascending would open with
    #     151 em-dashes and bury every real low score. "No entry" here means
    #     outside the 478-protein reviewed set -- genuinely absent, not low --
    #     so it should never outrank a measured value. This deliberately
    #     diverges from the other numeric columns; the divergence is the point.
    p.sub1(
        " r.sort((a,b)=>{let x=a[sortK],y=b[sortK];",
        " r.sort((a,b)=>{\n"
        "  if(sortK==='dm_sort'){const _an=a.dm_sort==null,_bn=b.dm_sort==null;\n"
        "   if(_an!==_bn)return _an?1:-1}\n"
        "  let x=a[sortK],y=b[sortK];",
        "depm/nulls-last-both-directions",
    )
    # --- first click on the header sorts high-to-low, like the other scores
    p.sub1(
        "sortAsc=!(k.includes('frac')||['mis_z','cof_score','cof_sig','cof_match','lit_score','metabolite_relevance','rv_sort'].includes(k))",
        "sortAsc=!(k.includes('frac')||['mis_z','cof_score','cof_sig','cof_match','lit_score','metabolite_relevance','rv_sort','dm_sort'].includes(k))",
        "depm/sort-direction",
    )
    # --- table now has 13 columns
    p.sub1(
        "  : '<tr><td colspan=12 class=empty>No matches.</td></tr>';",
        "  : '<tr><td colspan=13 class=empty>No matches.</td></tr>';",
        "depm/colspan-empty",
    )
    p.sub1(
        "document.getElementById('tb').innerHTML+=`<tr><td colspan=12 class=mut",
        "document.getElementById('tb').innerHTML+=`<tr><td colspan=13 class=mut",
        "depm/colspan-overflow",
    )
    # --- surface the existing DepMap breakdown in the protein detail modal,
    #     so clicking a row explains the number in the new column
    p.sub1(
        " <div class=sec><h3>Top coessential genes",
        " ${(typeof depPanel==='function')?depPanel(x.target_acc):''}\n"
        " <div class=sec><h3>Top coessential genes",
        "depm/detail-panel",
    )
    # --- dmCell must live in the same <script> block as the other cell
    #     renderers: render() is called at load time from that block, and a
    #     function declared in a later block would not yet exist.
    p.sub1(
        "function litCell(x){if(!x.lit)return '<span class=mut>\u2014</span>';",
        DEPM_JS + "function litCell(x){if(!x.lit)return '<span class=mut>\u2014</span>';",
        "depm/cell-renderer",
    )


LAYERS = [
    (1, EXPORT_MARKER, "CSV export buttons (candidate / literature / benchmark tables)", layer_export),
    (2, DEPM_MARKER, "Metabolic-coessentiality column on the main candidate table", layer_depm),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", default=DEFAULT_FILE, help=f"explorer HTML to patch (default: {DEFAULT_FILE})")
    ap.add_argument("--check", action="store_true", help="report which layers are present; change nothing")
    ap.add_argument("--no-backup", action="store_true", help="do not write a .bak.html copy first")
    args = ap.parse_args()

    if not os.path.exists(args.file):
        sys.exit(f"no such file: {args.file}")
    text = open(args.file, encoding="utf-8").read()

    todo = [L for L in LAYERS if L[1] not in text]
    for num, marker, desc, _ in LAYERS:
        state = "present" if marker not in [t[1] for t in todo] else "MISSING"
        print(f"  layer {num}  [{state:>7}]  {desc}")
    if args.check:
        return
    if not todo:
        print("\nall layers already applied; nothing to do")
        return

    if not args.no_backup:
        stamp = _dt.datetime.now().strftime("%Y%m%d")
        bak = args.file.replace(".html", f"_preFeatures_{stamp}.bak.html")
        if not os.path.exists(bak):
            shutil.copy2(args.file, bak)
            print(f"\nbackup -> {bak}")

    p = Patcher(text)
    print()
    for num, marker, desc, fn in todo:
        fn(p)
        print(f"  applied layer {num}: {desc}")
        for step in p.log:
            print(f"      - {step}")
        p.log = []

    open(args.file, "w", encoding="utf-8").write(p.text)
    print(f"\nwrote {args.file}  ({os.path.getsize(args.file):,} bytes)")


if __name__ == "__main__":
    main()
