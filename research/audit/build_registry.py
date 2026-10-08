"""Read-only, source-anchored historical inventory; no scientific execution.

Documentary KEEP/CI PASS never become a scientific PASS. Unknown case counts
and costs stay null. Exposed historic fresh sets are development-only now.
The registry includes missing version slots and distinct unmerged PR documents.
"""
from __future__ import annotations
import csv, hashlib, json, re, subprocess, sys
from pathlib import Path
from urllib.parse import unquote
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'research/audit'; WS=ROOT.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
FIELDS='experiment_id historical_question_namespace research_question hypothesis preregistration source_commit source_hash evidence_archive_hash experiment_family original_problem_lineage mathematical_goal designation number_of_independent_problems number_of_equivalent_views number_of_observations model_and_revision architecture representation discovery_method executor verifier strongest_comparator hardware_runtime accuracy_capability structural_recovery discovery_cost verification_cost execution_cost fallback_cost startup_cost amortization_assumptions total_cost unknown_cost_axes frozen_verdict posthoc_diagnosis unresolved_questions next_decision source_reference evidence_availability change_from_previous reusable_assets followup_usage_evidence record_kind'.split()
def git(*args): return subprocess.check_output(['git',*args],cwd=ROOT)
HEAD=git('rev-parse','HEAD').decode().strip()
FILES=git('ls-tree','-r','--name-only','HEAD').decode().splitlines()
def sha(b):return hashlib.sha256(b).hexdigest()
def nested_verdicts(o,prefix=''):
    found={}
    for k,v in o.items():
        path=prefix+k
        if isinstance(v,dict):found.update(nested_verdicts(v,path+'.'))
        elif not isinstance(v,list) and re.search(r'(^|_)(decision|verdict|status|keep|advance|gate)(_|$)',k,re.I):found[path]=v
    return found
def safe_document(p):
    p=Path(p).resolve()
    if p.suffix!='.md':raise ValueError('Inventory reads documentary sources only')
    return p.read_bytes()

def notion_document_candidates(directory):
    """Include linked engineering pages even when their title omits NEUMANN.

    Restrict new reads to version pages explicitly linked by already scoped
    NEUMANN documents. Never traverse arbitrary workspace links or sealed pages.
    """
    pages=list(Path(directory).glob('*.md'))
    selected=[p for p in pages if 'NEUMANN' in p.name.upper() or re.search(r'^(?:📐|🧩|🧪|🧱).*?(?:Schema|Pilot 50)',p.name)]
    linked=set()
    for p in selected:
        text=safe_document(p).decode('utf-8-sig')
        linked.update(re.findall(r'<page url="https://app\.notion\.com/p/([0-9a-f]{32})"[^>]*>v0\.0\.\d+',text))
        for target in re.findall(r'\[v0\.0\.\d+[^\]]*\]\(([^)]+)\)',text):
            match=re.search(r' -- ([0-9a-f]{32})\.md$',unquote(target))
            if match:linked.add(match.group(1))
    for p in pages:
        match=re.search(r' -- ([0-9a-f]{32})\.md$',p.name)
        if p not in selected and match and match.group(1) in linked and re.search(r'v0\.0\.\d+',p.name):
            if re.search(r'sealed|Decision\s*3|v0\.0\.(?:98|107)(?:\D|$)',p.name,re.I):
                continue
            selected.append(p)
    return selected
def sections(t):
    parts=re.split(r'(?m)^(#{1,3} .*)$',t)
    return [(parts[i].lstrip('# ').strip(),parts[i+1].strip()) for i in range(1,len(parts)-1,2)]
def selected(ss,pattern,limit=2400):
    return '\n\n'.join(title+'\n'+body for title,body in ss if re.search(pattern,title,re.I))[:limit] or None
def family(i):
    if i<=10:return 'controlled_semantic_IR'
    if i<=25:return 'runtime_plugin_engineering'
    if i<=31:return 'model_vs_solver_routing'
    if i<=49:return 'exact_linear_compression'
    if i<=57:return 'ordering_and_matrix_reuse'
    if i<=65:return 'LP_MIP_scenario_presolve'
    if i<=67:return 'power_grid_contingency_reuse'
    if i<=69:return 'exact_linear_complete_cost'
    if i<=75:return 'graph_quotient_and_elimination'
    if i<=80:return 'equal_authority_task_admission'
    if i<=104:return 'constructed_LP_support_discovery'
    return 'general_runtime_and_frontier_contract'

OVERRIDES={
'v0.0.1':{'research_question':'Explicit Structure Former -> typed IR -> deterministic routing/solving -> original checker/cost trace', 'source_reference':'Local Notion Engineering Track Core v0.0.1; original Git run unavailable', 'accuracy_capability':'Notion reports6 tests; assignment32->27 toy primitive counts, shortest23->23. Not wall/FLOPs/new discovery.'},
'v0.0.5':{'frozen_verdict':'ENGINEERING_ONLY','accuracy_capability':'README reports 14 tests PASS / 0 FAIL; coarse family prediction only.'},
'v0.0.76':{'frozen_verdict':'POST_HEAD_EQUIVALENCE_ONLY_NOT_Q4_PASS','number_of_independent_problems':486,'number_of_observations':39852},
'v0.0.97':{'frozen_verdict':'ADMIT_FRESH_Q34_HOLDOUT','number_of_independent_problems':16,'number_of_observations':576,'designation':'historical_opened_training_screen; current DEVELOPMENT_ONLY'},
'v0.0.98':{'frozen_verdict':'Q34_FRESH_HOLDOUT_FAIL_NO_Q5','evidence_availability':'RESULT_DOCUMENT_ONLY; sealed payload deliberately NOT_READ'},
'v0.0.99':{'frozen_verdict':'ADMIT_QUOTIENT_POINT_REFIT_ON_OPENED_DEV','number_of_independent_problems':48,'number_of_equivalent_views':144,'designation':'opened_v088_training; development_only'},
'v0.0.100':{'frozen_verdict':'STOP_QUOTIENT_REFIT_NO_FRESH_HOLDOUT','number_of_independent_problems':16,'number_of_equivalent_views':32,'number_of_observations':768,'model_and_revision':'pointwise MLP 8-16-16-1; 433 scalars; seeds 100001/100002','evidence_availability':'first archive retained; coefficient arrays absent; D0 does not recheck original witness'},
'v0.0.101':{'frozen_verdict':'ADMIT_NEW_FRESH_Q34_HOLDOUT_FOR_FROZEN_SUPPORT_SYSTEM','number_of_independent_problems':16,'number_of_equivalent_views':32,'number_of_observations':768,'model_and_revision':'two frozen v100 QUOTIENT checkpoints; no fitting'},
'v0.0.102':{'frozen_verdict':'Q34_EXPAND4_FRESH_HOLDOUT_PASS_ADVANCE_Q5','number_of_independent_problems':24,'number_of_equivalent_views':48,'number_of_observations':768,'accuracy_capability':'48/48 original-valid views per checkpoint; 8/48 expanded; no fallback','structural_recovery':{'100001':0.821688,'100002':0.822772},'discovery_cost':{'burden_s100001':0.021855,'burden_s100002':0.021960},'total_cost':{'amortized_candidate_direct_s100001':0.238921,'amortized_candidate_direct_s100002':0.237998},'amortization_assumptions':'10000 queries; registered ms boundary; external lifecycle costs not assumed complete','designation':'historical fresh confirmation; now opened DEVELOPMENT_ONLY','model_and_revision':'v100 QUOTIENT 433-scalar MLP; checkpoints c19ad47a4fd310ba469308529ff87134c6ea5de3066ad5750c4af54d658457ea / 20d012c6536cdb4041f6620307b5dbb1c1f3ab56f9438cbff971123a657c3ab5','representation':'observable analytic quotient features -> learned top2m ranking -> original restricted LP -> verifier-triggered top4m -> charged full fallback','discovery_method':'weighted BCE training on opened v088 reference-basis labels; no new representation generation'},
'v0.0.103':{'frozen_verdict':'Q5_SCALING_CAPABILITY_OR_ACCOUNTING_UNREACHED','number_of_independent_problems':48,'number_of_equivalent_views':96,'number_of_observations':1536,'accuracy_capability':'1504/1536 original accepted; 32 timed/warm Direct failures; both candidates accepted throughout','total_cost':'48 cells:26 PASS,18 COST_GATE_FAIL,4 capability-unreached; see derived full envelope','amortization_assumptions':'Q=10000; cold/authority preflight/setup retained; stationary break-even is posthoc estimate','designation':'historical fresh scaling; now DEVELOPMENT_ONLY','source_reference':'docs/experiments/v0.0.103.md; results/q5_first_evaluation/report.json; LP_SUCCESS_ENVELOPE.csv'},
'v0.0.104':{'frozen_verdict':'ASSIGNMENT: STOP_FAMILY_NO_ORACLE_HEADROOM; BP: ADMIT_FROZEN_CHECKPOINT_TRANSFER_NOT_LEARNING','number_of_independent_problems':32,'number_of_observations':448,'discovery_method':'free optimal support AND free original optimal dual; zero model forwards','strongest_comparator':'HiGHS native/IPM; assignment includes SciPy JV; L1 specialist coverage unresolved','designation':'opened Oracle diagnostic; never deployable learned inference'},
'v0.0.105':{'frozen_verdict':'ENGINEERING_ONLY','historical_question_namespace':'north_star_2026_10_02; legacy annex retained'},
'v0.0.106':{'frozen_verdict':'ENGINEERING_ONLY','historical_question_namespace':'north_star_2026_10_02'},
'M106':{'frozen_verdict':'STOP_FROZEN_TRANSFER_NO_REFIT','number_of_independent_problems':16,'number_of_observations':256,'accuracy_capability':'256/256 final original-valid; candidates fallback in120/128 calls','posthoc_diagnosis':'All 224 original-rejected available restricted witnesses fail only dual feasibility. 19 first-timed candidate attempts across13 paths/7 inputs have optimal primal but rejected dual; existing native dual certifies all19 offline. Not cost of obtaining that dual.','representation':'same v100 QUOTIENT rankings, top2m/top4m, unchanged executor','model_and_revision':'unchanged two frozen v100 checkpoints','strongest_comparator':'per-source fastest NATIVE/IPM; strongest L1 specialist not established','total_cost':'Every registered level fails transfer conjunction; candidate startup ~6.5s vs native ~1.09s; see original per-case costs','amortization_assumptions':'Q=10000 original; no new performance measurement'},
'Runtime-0.1':{'frozen_verdict':'NOT_EVALUATED','number_of_independent_problems':3,'number_of_observations':15,'designation':'opened repair controls; no capability threshold'},
'Runtime-0.2-Decision1':{'frozen_verdict':'FAIL','designation':'opened CPU interface/cost diagnostic; General Gate NOT_EVALUATED'},
'Decision2':{'frozen_verdict':'FAIL','number_of_independent_problems':12,'number_of_observations':36,'accuracy_capability':'DIRECT/TOOL/NEUMANN all0/12; 72 calls; zero tool/structural execution','model_and_revision':'google/gemma-4-E2B-it@3e22461f65e89153144f8adb70e3b8c2cc9845a7','posthoc_diagnosis':'All72 calls exhaust256 tokens in thought channel; no final action interface. Free-generative controller failure; not structural impossibility.'},
'Decision3':{'frozen_verdict':'NOT_EVALUATED','designation':'SEALED_DESIGN_ONLY; payload not read/hash/execute'},
'P1':{'frozen_verdict':'FAIL','posthoc_diagnosis':'Verbalizer prior collapse.'},
'P1.1':{'frozen_verdict':'FAIL','posthoc_diagnosis':'Subset permutation interaction.'},
'P1.2-dev':{'frozen_verdict':'PASS','designation':'opened development diagnostic; full-S4 stability not semantic competence'},
'P1.2-validation':{'frozen_verdict':'FAIL','accuracy_capability':'10/12 compatible; planning2/4'},
'P1.3':{'frozen_verdict':'PASS','designation':'ENGINEERING_ONLY; deterministic typed contract dispatch; zero neural forwards'},
'P1.4':{'frozen_verdict':'FAIL','number_of_independent_problems':12,'number_of_observations':12,'accuracy_capability':'raw semantic5/8; arithmetic2/4; CSP3/4; mixedfallback4/4'},
'P1.5':{'frozen_verdict':'FAIL','number_of_independent_problems':8,'number_of_observations':8,'accuracy_capability':'arithmetic4/4; CSP0/4; original ZIP/report/task receipts confirm. Earlier audit3/4 transcription corrected; FAIL unchanged.'},
'P1.6':{'frozen_verdict':'FAIL','number_of_independent_problems':8,'number_of_observations':8,'accuracy_capability':'raw accepted1/8; arithmetic0/4; CSP1/4'},
'P1.7':{'frozen_verdict':'FAIL'},'P1.8':{'frozen_verdict':'FAIL'},
'P1.9':{'frozen_verdict':'FAIL','number_of_independent_problems':8,'accuracy_capability':'accepted1/8'},
'P1.10':{'frozen_verdict':'INCOMPLETE','posthoc_diagnosis':'KeyboardInterrupt; no score inference for uncompleted items'},
'P1.11':{'frozen_verdict':'NOT_EVALUATED','posthoc_diagnosis':'Model parameter-count identity gate; no accepted performance evaluation'},
'P1.11.1':{'frozen_verdict':'FAIL','number_of_independent_problems':12,'number_of_observations':12,'accuracy_capability':'accepted3/12; raw top6/12; 12 forwards; wall~9.14s'},
'P1.12':{'frozen_verdict':'FAIL','number_of_independent_problems':12,'accuracy_capability':'accepted7/12; tiny cross-encoder not sufficient'},
'P1.13':{'frozen_verdict':'FAIL','number_of_independent_problems':12,'number_of_observations':24,'accuracy_capability':'paired incumbent3/12 vs NLI5/12; floor9/12 unmet; four paired wins/two losses','model_and_revision':'MiniLM MS MARCO22713601 vs nli-deberta-v3-base184424451; training/size/objective confounded'},
'Guarded':{'frozen_verdict':'ENGINEERING_PASS; NO_MEANINGFUL_HEADROOM','accuracy_capability':'126 exact identities;585 exact outputs; fixture3->1 states; 152 related tests','total_cost':'Native/free cold1 .9673; cold64 1.0222; warm .9884; same2add6mul compiled code'},
'Structural-Experience':{'frozen_verdict':'ENGINEERING_ONLY','number_of_observations':335,'number_of_independent_problems':None,'posthoc_diagnosis':'181 grouped paths,32 public projections,31 native procedures,13 topology groups; zero fresh-eligible; not335 independent learning problems'},
'BP-Certificate-Economics':{'frozen_verdict':'ENGINEERING_PASS; NO_REGISTERED_TENFOLD_HEADROOM; HOLD_LEARNING',
    'historical_question_namespace':'v2_opened_causal_diagnostic; no legacy verdict replacement',
    'experiment_family':'basis_pursuit_certificate_economics','number_of_independent_problems':16,'number_of_observations':576,
    'designation':'OPENED_DEVELOPMENT; Oracle C/D/E; B free retained-ranking LOWER BOUND; no fresh/training activation',
    'original_problem_lineage':'Same16 sources and per-source gzip/decoded identities from original M106 sources.json; no generated substitute or new independent problem',
    'accuracy_capability':'576/576 final original-valid within5s; optimizer-free independent replay PASS',
    'model_and_revision':'B exact retained rankings of BOTH frozen v100 checkpoints; no new forwards or fitting',
    'architecture':'CPU classical numerical diagnostic; no learned representation generator',
    'representation':'C fixed2m/4m vs D sparse least-squares+paid original dual vs E free optimal dual',
    'discovery_method':'Free retained optimum support in C/D/E; SPGL1 comparator receives only original signed-pair grammar',
    'executor':'existing Highs native, original adaptive support, SciPy least-squares and HiGHS full dual feasibility',
    'verifier':'unchanged lp_certificate_v081 original atol/rtol1e-8; no solver-based replay',
    'strongest_comparator':'min verified native primal simplex/IPM/explicit dual LP/SPGL1+SAME certificate repair; native simplex fastest16/16',
    'hardware_runtime':'Windows11 Intel64 Family6 Model165,12logical CPUs,1numerical thread; Py3.12.14 NumPy2.4.6 SciPy1.17.1 Highspy1.15.1 SPGL1 0.0.3',
    'verification_cost':'D full dual feasibility needed11/16 originals (44/64requests); timed stage median104.757ms; acquisition is not checker cost',
    'discovery_cost':'C/D/E structure supplied free as Oracle diagnostic; B retained model ranking free as lower bound. Actual neural discovery cost UNKNOWN.',
    'startup_cost':'Actual common diagnostic startup in first/report.json; private dependency installation1792.03ms; not independently optimized route deployment',
    'execution_cost':'16 paired source medians per route in BP_CERTIFICATE_DIAGNOSTIC_ANALYSIS.csv; stage receipts in576 first observations; unlike resources not summed',
    'fallback_cost':'B60/64 eachseed,C64/64,SPGL1 8/64 full native fallbacks; all charged',
    'amortization_assumptions':'Q1/Q10000; actual shared diagnostic startup and private dependency setup; historical fit/lifecycle investment UNKNOWN',
    'total_cost':{'native_over_B_s100001':.6943281366599783,'native_over_B_s100002':.6978407570099845,'native_over_C':.725449070858969,'native_over_D':.48373610935097194,'native_over_E':4.091272386287689,'tenfold_originals_per_candidate':'0/16','full_lifecycle_cost':'UNKNOWN'},
    'evidence_archive_hash':'088f4bb94f807fbdc102c60426db966d4320aecbdf32f3923f8d338499dbb756',
    'posthoc_diagnosis':'For this adapter, paid full-goal dual acquisition erases free-support advantage. Minimum-norm certified5/16 have1.91-3.52x local advantage. Free dual Oracle still no registered10x. No universal cheap-certificate impossibility.',
    'next_decision':'HOLD_LEARNING; no Phase3/G1/G2; preserve one first diagnostic, no threshold/pipeline rescue',
    'evidence_availability':'Exact local first event chain,576compressed observations,report/contract hashes and independent replay retained'},
 'G0-Probabilistic-Native':{
    'record_kind':'OPENED_NATIVE_SCIENTIFIC_DIAGNOSTIC',
    'historical_question_namespace':'v2_G0_A_existing_candidate; no global Q closure',
    'source_commit':'LOCAL_UNCOMMITTED_RUNNER; base fb23dca002bbd50c96e0c766369269a0b7fcc7a6; runtime runner SHA102c647cb82b1b498dc667c8befb35375bb680cec36349b45873e6a83c3cb303',
    'frozen_verdict':'INCOMPLETE; NO_REGISTERED_FAMILY_PASS; HOLD_LEARNING',
    'experiment_family':'goal_dependent_probabilistic_sufficient_state',
    'research_question':'Does a free exact quotient leave tenfold acquisition/execution headroom against the tested strong native portfolio under equal reuse rights?',
    'preregistration':'Continuation/G0_PROBABILISTIC_2026-10-08/probabilistic-native.preregister.json; SHA9694bd5031d6a08e265d112922eeb67c3e3bd72ea51bf4c4beaf2082bea05a1c',
    'original_problem_lineage':'QVBS c7324a311475ba1a3f40e36a324e32f91e766540;13 public parameter/goal requests,9families,11unique JANI files; formats/repeats not independent',
    'designation':'OPENED_DEVELOPMENT; exact public reference only in parent; no training/fresh redesignation',
    'number_of_independent_problems':None,'number_of_observations':375,
    'model_and_revision':'No neural model; Stormpy1.14.0 official wheel source d22615ca859f1518015c065414dd0a36c4615484',
    'architecture':'Existing exact native model checking and strong bisimulation; no learned generator',
    'representation':'Goal-bound exact quotient from native compiler, not answer cache',
    'discovery_method':'Classical strong bisimulation supplied free only for explicit optimistic floors',
    'executor':'SparseExact/default+topological, rational bisimulation, DD-to-sparse/bisim paths; original PRISM/JANI where supported',
    'verifier':'Exact Fraction comparison with parent-only public references, including original max over all initial states; no new arbitrary quotient proof checker',
    'strongest_comparator':'Fastest fully original-valid tested Storm path; native analytic methods missing in original screen, later source-bound controls for Coupon/EGL/Crowds/Herman15',
    'hardware_runtime':'Free Kaggle CPU4 Linuxx86_64 Py3.13.15;1worker,1numerical thread,75s/job,8GiB virtual address cap',
    'accuracy_capability':'125attempted jobs:101FINISHED/9PROCESS_FAILED/15TIMEOUT.375receipts:361PASS/14NOT_VERIFIED/0wrong exact outputs;87fully verified four-repeat paths. Missing timeout requests not denominator successes.',
    'structural_recovery':'State reduction up to2815.8x(EGL),not a cost ratio or learned recovery measure',
    'discovery_cost':'Native quotient build measured per stage; free arm excludes acquisition as diagnostic lower bound',
    'verification_cost':'Parent reference audit .089257994s; diagnostic audit cost, not deployable independent representation proof',
    'execution_cost':'Per-stage worker perf_counter_ns; same compiled quotient actually resolved by both arms; compiled ratios approximately1',
    'fallback_cost':'No rescue reruns; nineSIGSEGV/15timeouts and partial receipts preserved. Unfinished stage costs UNKNOWN.',
    'startup_cost':'Measured worker process/import startup charged to cold floors; parent subprocess.wait quantizes job wall and is not used for internal latency',
    'amortization_assumptions':'Cold1,three resident fresh requests,onewarmup+threecompiled solves eacharm; no answer cache or lifecycle amortization result',
    'total_cost':'Parent1809.169080598s. Cold Native/free max4.741x. Verified two-bin optimistic resident BRP4.3636x,Crowds9.67849x. Coupon22.5505x/EGL53.0885x singleton floors do not satisfy family rule or complete-cost superiority.',
    'unknown_cost_axes':'energy;FLOPs;money;Oracle delivery;independent source/quotient proof acquisition;full lifecycle investment;unfinished timeout stages',
    'evidence_archive_hash':'63e04646c8070b8df8fbe51ef7793a37f8dc873aae23e02488525e63be25bbc1',
    'posthoc_diagnosis':'No registered family potential flag.14DD-to-sparse unknown-label errors;9returncode-11 rootsUNKNOWN; native manifest exact row projection verified but full-container hash not asserted at runtime. Analytic controls qualify strongest-comparator coverage.',
    'next_decision':'HOLD_LEARNING; preserve incomplete first; noG1/G2; do not treat provided quotient or compilation reuse as learned discovery',
    'evidence_availability':'First ZIP1022entries/all1021manifestedfiles independently hash-verified; zero-solver analysis in G0_PROBABILISTIC_NATIVE_ANALYSIS.json/csv'},
 'Probabilistic-Analytic-Controls':{
    'record_kind':'SOURCE_BOUND_ENGINEERING_CONTROL','source_commit':'LOCAL_UNCOMMITTED; no scientific timing run',
    'historical_question_namespace':'G0_A strongest-comparator qualification, not a third G0 candidate',
    'frozen_verdict':'ENGINEERING_PASS; PERFORMANCE_NOT_MEASURED',
    'experiment_family':'existing_classical_probability_controls',
    'designation':'SAME_OPENED_SOURCES; manual/published proof trust; no learned inference or fresh evaluation',
    'original_problem_lineage':'Same Coupon,EGL,Crowds5/10,Herman15 source requests as G0-Probabilistic-Native;5outputs from4families,not new tasks',
    'number_of_independent_problems':None,'number_of_observations':None,
    'accuracy_capability':'Five exact original outputs agree;10positive/negative engineering tests PASS .023s suite wall,not performance measurements',
    'architecture':'Fraction arithmetic with manually reviewed original program/property/goal/parameter source pins',
    'representation':'Coupon inclusion-exclusion/count DP;EGL order event;Crowds geometric single-path+binomial/count DP;published Herman maximal expectation',
    'discovery_method':'Manual derivation and published theorem reuse; no learned perspective discovery',
    'executor':'Exact native classical arithmetic; no neural model or state enumeration',
    'verifier':'Source/property SHA binding; independent arithmetic formulations when supplied; retained Native output agreement. Machine-formal proof NOT_EXECUTED.',
    'strongest_comparator':'Adds applicable goal-specific analytic native controls omitted from the original Storm portfolio',
    'discovery_cost':None,'verification_cost':None,'execution_cost':None,'fallback_cost':None,'startup_cost':None,'total_cost':None,
    'unknown_cost_axes':'All operational/lifecycle performance axes;test suite wall is not benchmark latency',
    'posthoc_diagnosis':'Coupon22.55x/EGL53.09x/Crowdslarge16.21x Storm-only free floors are not evidence of residual learned discovery gaps. Herman15 native timeout does not imply native incapability.',
    'next_decision':'HOLD_LEARNING; preserve original screen; no formal-proof or performance claim; no more singleton rescue benchmarks'},
}
STUDIES={
'M106':'bp_frozen_transfer_m106.md','Runtime-0.1':'general_runtime_repair_v1061.md','Runtime-0.2-Decision1':'general_runtime_compact_v1062.md',
'Decision2':'decision2_first_actual_result_2026-10-03.md','Decision3':'decision3_sealed_gate.md',
'P1':'control_plane_p1_first_result_2026-10-03.md','P1.1':'control_plane_p11_first_result_2026-10-04.md',
'P1.2-dev':'control_plane_p12_first_result_2026-10-04.md','P1.2-validation':'control_plane_p12_validation_first_result_2026-10-04.md',
'P1.3':'control_plane_p13.md','P1.4':'control_plane_p14_first_result_2026-10-04.md','P1.5':'control_plane_p15_first_result_2026-10-04.md','P1.6':'control_plane_p16_first_result_2026-10-04.md',
'P1.7':'control_plane_p17_first_result_2026-10-05.md','P1.8':'control_plane_p18_first_result_2026-10-05.md','P1.9':'control_plane_p19_first_result_2026-10-05.md',
'P1.10':'control_plane_p110_first_interrupted_2026-10-05.md','P1.11':'control_plane_p111_first_nonevaluated_2026-10-05.md','P1.11.1':'control_plane_p1111_first_fail_2026-10-05.md',
'P1.12':'control_plane_p112_development_2026-10-06.md','P1.13':'control_plane_p113_paired_2026-10-06.md',
'G0-Graph-SPD':'g0_first_2026-10-06.md','G0-Composed':'g0_composition_2026-10-06.md',
'Polynomial-Representation':'representation_generation_2026-10-07.md','Inductive-Complete-Cost':'inductive_complete_cost_2026-10-07.md',
'Recursive-Summary':'recursive_summary_engineering_2026-10-07.md','Compressed-Recursive-Cost':'compressed_recursive_cost_2026-10-07.md',
'Symbolic-Decoder-OCaml':'symbolic_decoder_source_binding_2026-10-07.md','Full-Synduce':'full_synduce_baseline_2026-10-07.md',
'SuFu-Official-Tensors':'sufu_and_official_tensors_2026-10-07.md','Perspective-Transfer':'perspective_transfer_headroom_2026-10-07.md',
'Structural-Experience':'structural_experience_2026-10-07.md','Structural-Mechanism':'structural_mechanism_screen_2026-10-06.md',
'REUSE-R0':'reacomp_reuse_2026-10-06.md','CODE-C0':'code_gate_c0_2026-10-06.md','Guarded':'guarded_perspective_2026-10-08.md',
'Candidate-Compression':'candidate_compression_2026-10-06.md','AM1-local':'am1_local_execution.md',
'BP-Certificate-Economics':'bp_certificate_diagnostic_2026-10-08.md',
'G0-Probabilistic-Native':'g0_probabilistic_native_2026-10-08.md',
'Probabilistic-Analytic-Controls':'probabilistic_analytic_controls_2026-10-08.md',
}
def make_row(eid,p,b,origin):
    t=b.decode('utf-8-sig');ss=sections(t)
    row={k:None for k in FIELDS}
    row.update(experiment_id=eid,source_commit=origin,source_hash=sha(b),record_kind='HISTORICAL_STUDY_DOCUMENT',
               historical_question_namespace='legacy_pre_v105' if eid.startswith('v0.0.') and float(eid.split('.')[-1])<=104 else 'north_star_2026_10_02',
               research_question=selected(ss,r'question|hypothesis|scope|objective|goal',1800) or t.splitlines()[0],
               hypothesis=selected(ss,r'hypothesis|question|why|motivation',2200),
               mathematical_goal=selected(ss,r'goal|task|scope',1000),
               accuracy_capability=selected(ss,r'first.*result|first.*audit|frozen.*result|retained.*outcome|result',3800),
               frozen_verdict=selected(ss,r'^decision$|frozen verdict|final decision|retained first outcome',1800) or 'UNKNOWN: inspect source result/contract separately',
               posthoc_diagnosis=selected(ss,r'interpret|finding|diagnos|boundary|negative|causal',3000),
               unresolved_questions=selected(ss,r'next|pending|boundary|limitation',1500),
               next_decision=selected(ss,r'next|decision',2000),
               change_from_previous=selected(ss,r'why|question|hypothesis|changes|implementation|reuse',1600),
               designation='historical designation see source; opened documentary material; no fresh/training activation',
               unknown_cost_axes='FLOPs;energy;money;unreported discovery/verification/startup/investment; never zero',
               evidence_availability='DOCUMENT_CHECKED; related archives indexed separately; not all original executions independently replayed',
               source_reference=p)
    assets=sorted(set(re.findall(r'(?:neumann1|experiments|tests)/[\w/.-]+\.py',t)))
    row['reusable_assets']=assets or None
    row['followup_usage_evidence']='Source references only; no universal code-use attribution asserted'
    refs=[]
    for m in re.finditer(r'(?:docs/experiments/)?results/[\w/.-]+\.(?:json(?:\.gz)?|zip|md)',t):
        path=m.group(0);path=path if path.startswith('docs/') else 'docs/experiments/'+path
        refs.append(path)
    row['preregistration']=sorted(set(re.findall(r'[\w/.-]*(?:preregister|preregistration|trigger)[\w/.-]*\.(?:md|json)',t))) or None
    row.update(OVERRIDES.get(eid,{}))
    known_execution_heads={'v0.0.99':'b9299e382d516b6d26669d1134f763f20a3367d4',
        'v0.0.100':'8e14341a614d8810380def5e2c302352c6ca47e3',
        'v0.0.101':'e6fb888c1ef216085832ea723bbac4ad8953ca22',
        'v0.0.102':'46af13c3d7d9b1a87f0a0db8511f5972511beb16',
        'v0.0.103':'99e59fe9ceec4102d023ce0f9eb2e510017062c4',
        'v0.0.104':'17d83a4dd22faf8a5799b68a82c8ef2456d414fa',
        'M106':'5db505265f10e204526221f1cd7d318acdb47973',
        'Decision2':'716e71834fe5b585e7369e7c1394919c61b3d9e9'}
    if eid in known_execution_heads:row['source_commit']=known_execution_heads[eid]
    known_archives={'v0.0.100':'3f46a6b8672471dbcf68ca7c073df8d92572e710770a8b9a04dc8d920aad0082',
        'v0.0.101':'e468b676e72dc3b8922fdc0fc044a4400fdbba3728362c8ead8af02e4018971f',
        'v0.0.102':'a73c21e149852013b7db19c0380ddaa36d5c2d6582051008a22942e7309cf47a',
        'v0.0.103':'1f7a3ad5a1038e42234b734b0b00f185c0be4a5a1d11a3d3d6e96ace92d546e3',
        'v0.0.104':'97884fa0c0093e3e6b96931fc9fd359a34a07c67eb0b87d2bd5a5a51f644697a',
        'M106':'fd0f069bb43c8f4f471578de35a6f70af2c418b46b701260f12cd1d27bebd6b8',
        'Decision2':'468893d7be2ac5587edee3b7f87ad4310919f8c883800df8e1f8d41150556355',
        'P1.13':'265c4bc939ce0cade72b97a29f79f40b9f8afef3b56cd49a440aa873d88c4f2a'}
    row['evidence_archive_hash']=known_archives.get(eid,row.get('evidence_archive_hash'))
    return row,{'id':eid,'source':p,'document_sha256':sha(b),'source_git_origin':origin,
                'related_artifact_references':sorted(set(refs)),
                'scientific_execution_heads_mentioned':sorted(set(re.findall(r'\b[0-9a-f]{40}\b',t))),
                'archive_identities_mentioned':sorted(set(re.findall(r'\b[0-9a-f]{64}\b',t))),
                'exposure':'document opened; sealed payload excluded','source_sections':ss}

def build():
    rows=[];nodes=[];missing=[]
    def add(eid,p,b=None,origin=HEAD):
        if b is None:b=safe_document(ROOT/p)
        r,n=make_row(eid,p,b,origin);rows.append(r);nodes.append(n)
    for i in range(1,107):
        p=f'docs/experiments/v0.0.{i}.md';eid=f'v0.0.{i}'
        if (ROOT/p).exists():add(eid,p);rows[-1]['experiment_family']=family(i)
        elif i==5:
            add(eid,'git:603b252:README.md',git('show','603b252:README.md'),git('rev-parse','603b252').decode().strip())
        elif i==39:
            ref='origin/research/v0.0.39-coupled-block-replication-clean'
            add(eid,'git:'+ref+':'+p,git('show',ref+':'+p),git('rev-parse',ref).decode().strip())
            rows[-1]['frozen_verdict']='NOT_VERIFIED: unmerged preregistration, no first result in inspected branch'
        else:
            r={k:None for k in FIELDS};r.update(experiment_id=eid,record_kind='MISSING_VERSION_SLOT',
                historical_question_namespace='early_engineering',frozen_verdict='UNKNOWN',evidence_availability='EXTERNAL_EVIDENCE_REQUIRED',
                source_reference='No separate Git experiment doc or first execution recovered',unknown_cost_axes='all')
            r.update(OVERRIDES.get(eid,{}))
            rows.append(r);missing.append({'id':eid,'reason':'Separate Git experiment/run not recovered; v1 Notion report separately linked; no result inferred from successor.'})
    add('v0.0.38.1','docs/experiments/v0.0.38.1.md')
    for eid,name in STUDIES.items(): add(eid,'docs/research/'+name)
    # Available NEUMANN-only Notion snapshots; filenames are selected before content read.
    notion=notion_document_candidates(WS/'Notion/pages')
    for p in notion:
        eid='Notion-'+p.stem.split(' -- ')[0]
        # Distinct duplicate/superseded Notion pages must retain distinct identity.
        if re.search(r'v0\.0\.\d+',p.name) and 'NEUMANN' not in p.name.upper():
            eid+='-'+p.stem.split(' -- ')[-1]
        add(eid,str(p),safe_document(p),'NOTION_LOCAL_SNAPSHOT_NOT_LIVE_REVISION')
        version=re.search(r'v0\.0\.(\d+)',p.name)
        if version and 'NEUMANN' not in p.name.upper():
            rows[-1]['record_kind']='NOTION_DOCUMENTARY_ENGINEERING_REPORT'
            rows[-1]['frozen_verdict']='DOCUMENTARY_REPORTED_DECISION_ONLY; first raw execution not recovered'
            rows[-1]['evidence_availability']='DEDICATED_NOTION_REPORT_RECOVERED; not an independent raw replay'
            version_id='v0.0.'+version.group(1)
            nodes[-1]['reports_experiment_id']=version_id
            for row in rows:
                if row['experiment_id']==version_id and row['record_kind']=='MISSING_VERSION_SLOT':
                    row['source_reference']=str(p)
                    row['evidence_availability']='DEDICATED_NOTION_REPORT_RECOVERED; Git/raw first execution still unavailable'
            for entry in missing:
                if entry['id']==version_id:
                    entry['reason']='Dedicated Notion report recovered and linked; separate Git first run/raw archive not recovered. Documentary results are not independent replay.'
        else:
            rows[-1]['record_kind']='RESEARCH_CHARTER_OR_ANNOTATION_DOCUMENT'
            rows[-1]['frozen_verdict']='ENGINEERING_ONLY / DESIGN_DOCUMENT; execution authority not inferred'
    for eid in ['v0.1','v0.2','v0.3','v0.4','v0.5','v0.5.1']:
        r={k:None for k in FIELDS};r.update(experiment_id='Initial-'+eid,record_kind='MISSING_ORIGINAL_RESEARCH_REVISION',
            research_question='Structural recurrence/compute-aware discovery/memory/noise/transfer charter lineage',
            source_reference='Notion main snapshot reports v0.5.1 frozen and errata; separate original revisions not recovered',
            frozen_verdict='EXTERNAL_EVIDENCE_REQUIRED',evidence_availability='EXTERNAL_EVIDENCE_REQUIRED',unknown_cost_axes='all')
        rows.append(r);missing.append({'id':'Initial-'+eid,'reason':'Only current/snapshot narrative; separate original research document/run unavailable.'})
    # Read all open-PR documentary deltas from exact fetched heads, without checkout/merge.
    state=json.loads((OUT/'REPOSITORY_STATE_FIRST.json').read_text(encoding='utf-8'))
    branches=[]
    for pr in state['open_prs']:
        ref=pr['head']; paths=git('ls-tree','-r','--name-only',ref).decode().splitlines();delta=[]
        for p in paths:
            if not re.fullmatch(r'docs/experiments/v0\.0\.\d+(?:\.\d+)?\.md',p):continue
            b=git('show',ref+':'+p)
            current=git('show','HEAD:'+p) if p in FILES else None
            if current==b:continue
            eid=f'PR{pr["number"]}-'+Path(p).stem
            add(eid,'git:'+ref+':'+p,b,ref);rows[-1]['record_kind']='UNMERGED_DOCUMENT_VARIANT'
            delta.append({'path':p,'sha256':sha(b),'same_as_current':False})
        ancestor=subprocess.run(['git','merge-base','--is-ancestor',ref,'HEAD'],cwd=ROOT,capture_output=True).returncode==0
        branches.append({'pr':pr['number'],'head':ref,'ancestor_of_current':ancestor,'document_variants':delta})
    # Opened top-level first result events, including invalid/corrective attempts.
    # Sealed data and large nested raw workloads are not traversed by this inventory.
    events=[]
    explicit_reports=[ROOT/'docs/experiments/results'/name/'report.json' for name in
        ['v106_general_boot2','v106_general_development_first','v1061_general_repair_first',
         'v1062_general_compact_first','m106_bp_transfer_first','v104_transfer_admission_first','q5_first_evaluation']]
    explicit_reports += [ROOT/'docs/research/decision2_first_actual_evidence/report.json']
    explicit_reports += sorted((ROOT/'docs/experiments/results/structural_evidence_2026_10_07').glob('*.json'))
    for p in sorted(set((ROOT/'docs/experiments/results').glob('*.json'))|set(explicit_reports)):
        if not p.is_file():continue
        if re.search(r'v0?98|decision3|v107|sealed|holdout',p.name,re.I):continue
        b=p.read_bytes()
        if len(b)>8*1024*1024:continue
        try:o=json.loads(b)
        except (ValueError,UnicodeError):continue
        if not isinstance(o,dict):continue
        scalar={k:v for k,v in o.items() if not isinstance(v,(dict,list))}
        verdicts=nested_verdicts(o)
        events.append({'path':str(p.relative_to(ROOT)),'sha256':sha(b),'bytes':len(b),
                       'top_level_metadata':scalar,'root_keys':list(o),'verdict_fields':verdicts})
        if p.name!='report.json' and not re.search(r'first|audit|contaminated|invalid|corrective|screen|diagnostic|parity|summary|notice|repair|failure',p.name):continue
        eid='EvidenceEvent-'+(p.parent.name+'-'+p.stem if p.name=='report.json' else p.stem)
        r={k:None for k in FIELDS};r.update(experiment_id=eid,record_kind='RETAINED_RESULT_EVENT',
            source_commit=o.get('frozen_head') or o.get('source_commit'),source_hash=sha(b),evidence_archive_hash=sha(b),
            source_reference=str(p.relative_to(ROOT)),frozen_verdict=verdicts or 'UNKNOWN_ROOT; inspect nested evaluator',
            designation='opened archived result metadata; not fresh/training activation',
            evidence_availability='raw JSON bytes checked; no new execution',unknown_cost_axes='unreported axes remain UNKNOWN')
        rows.append(r)
        match=re.fullmatch(r'v(\d{3})_first_audit',p.stem)
        if match and verdicts:
            parent=next((x for x in rows if x['experiment_id']==f'v0.0.{int(match[1])}'),None)
            if parent and parent['experiment_id'] not in OVERRIDES:
                parent['frozen_verdict']=verdicts
                parent['evidence_archive_hash']=sha(b)
                parent['evidence_availability']='first JSON bytes and documentary result inspected; independent replay scope see linked historical audit'
    # Indexed prior original archive identities and missing P1 bundles from earlier D0.
    d0p=ROOT/'experiments/legacy_reuse_ledger.json'
    d0=json.loads(d0p.read_text(encoding='utf-8'))
    ledger=json.loads((ROOT/'docs/experiments/experiment_decision_ledger.json').read_text(encoding='utf-8'))
    for eid in ['P1.2-validation','P1.3','P1.4','P1.5','P1.6','P1.7','P1.8','P1.9','P1.10','P1.11','P1.11.1']:
        missing.append({'id':eid,'reason':'D0 reports original raw ZIP not locally retained; documentary first outcome retained.'})
    p1_recovery = None
    recovery_path = OUT/'P1_RECOVERY_ANALYSIS.json'
    if recovery_path.is_file():
        from research.audit.analyze_recovered_p1 import analyze as audit_p1_recovery
        p1_recovery = audit_p1_recovery()
        recovered = p1_recovery['P1.7']
        p17 = next(row for row in rows if row['experiment_id']=='P1.7')
        p17['evidence_archive_hash'] = recovered['archive_sha256']
        p17['evidence_availability'] = 'Original first ZIP recovered from retained notebook embedded download; all35members CRC/hash checked. Original semantic replay failed and remains failed.'
        p17['source_reference'] += '; '+recovered['source']+'; research/audit/P1_RECOVERY_ANALYSIS.json'
        missing = [entry for entry in missing if entry['id']!='P1.7']
        for study, recovered in {**p1_recovery['early_archives'], 'P1.3': p1_recovery['P1.3']}.items():
            row = next(item for item in rows if item['experiment_id']==study)
            row['evidence_archive_hash'] = recovered['archive_sha256']
            recovery_source = 'original workflow archived stdout' if study=='P1.3' else 'retained embedded notebook output'
            row['evidence_availability'] = ('Original first ZIP recovered from '+recovery_source+'; all'+str(recovered['archive_members'])+
                'members CRC/closed-membership/hash checked. Original replay exit '+str(recovered['original_replay_exit_code'])+' retained; current existing model-free replay also passed. Hash verification alone is not semantic replay.')
            row['source_reference'] += '; '+recovered['source']+'; research/audit/P1_RECOVERY_ANALYSIS.json'
            missing = [entry for entry in missing if entry['id']!=study]
        for entry in missing:
            if entry['id'] in p1_recovery['printed_outputs']:
                entry['reason'] += ' Retained notebook printed diagnostic recovered; raw ZIP still unavailable. See P1_RECOVERY_ANALYSIS.json.'
    missing += [{'id':'v0.0.39-first-result','reason':'Preregistration recovered from unmerged branch; successful CI alone is not a recovered scientific result/first archive.'},
                {'id':'v100-v101-coefficients','reason':'First archives contain metadata/ranking/witness but not original coefficient arrays; no regenerated surrogate accepted as original.'},
                {'id':'v087-first-confounded','reason':'Original confounded archive lost; corrective execution distinct.'},
                {'id':'OCaml5-first-26-views','reason':'Original archive lost; OCaml4.14 recovery is a distinct run.'},
                {'id':'Decision3-v098-v107-sealed','reason':'Deliberate protected non-access; not missing evidence to reconstruct/open.'},
                {'id':'Formal-CPOG-checker','reason':'Pinned Lean build timed out; only C prototype ran.'}]
    counting=WS/'Continuation/G0_NATIVE_READINESS_2026-10-08'
    extras=[('Native-Readiness','ENGINEERING_ONLY; formal checker INCOMPLETE',112,15),
            ('Counting-Native-First','INCOMPLETE',17,172),('Polar-Readiness','INCOMPLETE',None,None)]
    for eid,verdict,problems,obs in extras:
        r={k:None for k in FIELDS};r.update(experiment_id=eid,record_kind='LOCAL_FIRST_EVIDENCE',source_commit=HEAD,
            frozen_verdict=verdict,evidence_availability='original local files and SHA receipts retained',source_reference=str(counting),
            designation='OPENED_DEVELOPMENT / comparator readiness; zero neural inference',
            number_of_independent_problems=problems if eid=='Counting-Native-First' else None,
            number_of_observations=obs,unknown_cost_axes='energy;FLOPs;peak_memory;full investment;resident warm runtime')
        if eid=='Counting-Native-First':r.update(evidence_archive_hash='004d8ed4e7ced5b62af6e629686c859e398fd2a3e2962b9d5b0c33b4b0148e61',
            accuracy_capability='12/17 prototype-certified;5 certificate-generation timeouts;102/102 exact native repetitions;36/36 completed checks agree',
            total_cost='completed-subset native/free geomean.4392931;max4.0204;0/12>=10. No complete17-case ratio.',
            posthoc_diagnosis='Unconditional upstream debug output (up to347691801bytes/log), harness completion quantization; limited cold prototype evidence, not universal no-headroom.',
            next_decision='HOLD unchanged pipeline learning; retain INCOMPLETE')
        if eid=='Native-Readiness':r['evidence_archive_hash']='4359b0e585b5b07d7c3b55524b075aac7cab546f4c96b5983529a768a8c52f3e'
        rows.append(r)
    assert len({r['experiment_id'] for r in rows})==len(rows)
    with (OUT/'EXPERIMENT_REGISTRY.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader()
        for r in rows:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in r.items()})
    lineage={'schema':'neumann.historical-evidence-lineage.v2','audit_head':HEAD,'global_questions_closed':[],
             'registry_rows_not_independent_experiments':len(rows),'read_scope':'documentary sources, exact open PR docs, explicitly opened LP first evidence; no sealed payloads',
             'nodes':[{k:v for k,v in n.items() if k!='source_sections'} for n in nodes],
             'open_branch_ancestry':branches,'opened_result_events':events,'d0_retained_index':d0,'earlier_decision_ledger':ledger,
             'additional_repository_receipts':['OPEN_PR_CI_FIRST.json','PR174_OVERLAP.json'],
             'recovered_notebook_evidence':p1_recovery,
             'edges':[{'from':'v0.0.88','to':'v0.0.100','type':'48 opened training problems; basis-label supervision'},
                      {'from':'v0.0.99','to':'v0.0.100','type':'analytic quotient observable features'},
                      {'from':'v0.0.100','to':'v0.0.101','type':'two exact frozen checkpoints; no refit'},
                      {'from':'v0.0.101','to':'v0.0.102','type':'registered2m->4m executor; fresh24 bases'},
                      {'from':'v0.0.102','to':'v0.0.103','type':'unchanged models;48 new base seeds+equivalent surfaces'},
                      {'from':'v0.0.104','to':'M106','type':'admission from free support+dual ceiling; different inputs; no paired-cost subtraction'},
                      {'from':'v0.0.100','to':'M106','type':'unchanged features/models/cardinality/executor'},
                      {'from':'M106','to':'BP-Certificate-Economics','type':'same16 opened originals and retained frozen rankings; independent causal contract; no new task or fresh redesignation'},
                      {'from':'G0-Probabilistic-Native','to':'Probabilistic-Analytic-Controls','type':'same5 opened original requests; strongest native qualification; no new independent data or learned discovery'},
                      {'from':'Decision2','to':'P1','type':'controller failure pivot; not invalidation of LP success'}],
             'count_semantics':'Seeds/checkpoints/repeats/equivalent views are not independent originals; do not sum across reused studies.',
             'hash_semantics':'source_hash is documentary/raw-event bytes, not assumed runtime code. source_commit defaults to document locator HEAD unless independently known execution head. archive hash kind is specified by source path (JSON/gzip/ZIP). Full result event nesting is preserved, not remapped to a new PASS.',
             'missing':missing}
    (OUT/'EVIDENCE_LINEAGE.json').write_text(json.dumps(lineage,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    appendix=['# 全 연구 문서 근거 발췌 / Historical documentary inventory\n',
              '원본 문서의 가설·결과·진단·다음 결정 발췌다. 실행 원본을 대신하지 않는다. 동일 문서/입력의 여러 기록을 독립 실험으로 합산하지 않는다.\n']
    for r,n in zip(rows[:len(nodes)],nodes):
        # Nodes can diverge from missing registry slots; use node id explicitly.
        appendix += [f'## {n["id"]}\n',f'Source: {n["source"]}\nSHA256: {n["document_sha256"]}\n']
        for title,body in n['source_sections']:
            if re.search(r'question|hypothesis|result|audit|verdict|decision|interpret|finding|next|retention|mechanism',title,re.I):
                appendix.append(f'### {title}\n\n{body[:4000]}\n')
    (OUT/'HISTORICAL_SOURCE_REVIEW.md').write_text('\n'.join(appendix),encoding='utf-8')
    (OUT/'MISSING_EVIDENCE.md').write_text('# Missing evidence / intentional exclusions\n\n'
       +'각 항목은 원본 미확보·부분 보존·의도적 봉인을 구별한다. 원본 없음은 실패 판정이 아니다. Notion inventory는 로컬 snapshot이다. 2026-10-08에 읽기 전용으로 별도 확인한 5개 page와 범위는 NOTION_SUPPLEMENT_VERIFICATION.json에 기록했다. 모든 Notion 페이지의 최신 상태나 원본 실행 복구를 주장하지 않는다.\n\n'
       +'\n'.join(f'- **{m["id"]}**: {m["reason"]}' for m in missing)+'\n',encoding='utf-8')
    print(json.dumps({'registry_rows':len(rows),'document_nodes':len(nodes),'missing_entries':len(missing),'open_prs':len(branches),'unmerged_document_variants':sum(len(x['document_variants']) for x in branches)},ensure_ascii=False))

if __name__=='__main__':build()
