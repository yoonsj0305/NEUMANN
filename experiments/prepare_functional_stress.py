from pathlib import Path
import hashlib,json


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    repo=Path(__file__).resolve().parents[1];work=repo.parents[1]
    target=work/'Continuation/FUNCTIONAL_STRESS_PREPARATION';target.mkdir()
    sources=['neumann1/functional_source.py','neumann1/functional_examples.py','neumann1/functional_types.py',
             'experiments/functional_stress.py']
    contract={'study':'OPENED_FUNCTIONAL_SOURCE_STRESS_V1',
              'purpose':'Independent concrete counterexamples and interface checks; not universal proof or G0.',
              'source_pins':{n:sha(repo/n) for n in sources},
              'source_intake_manifest_sha256':sha(work/'Continuation/SUFU_SOURCE_FIRST/manifest.json'),
              'native_registration_sha256':'74559c0c2188d79d5932ef42459301d82e47f1e7a63da838cb60c33900bcb633',
              'eligibility':'All 290 native outcomes retained; only upstream-bounded successes get transform comparison',
              'exposure':'Full public source/cache opened and original preflight run; only sum optimized program previewed',
              'phases':[
                  {'name':'small','count':8,'shape':'random','depths':[0,1,2,3,4],'numbers':[-2,-1,0,1,2]},
                  {'name':'large_values','count':24,'shape':'random','depths':[1,2,4,8],'numbers':[-1000,-17,-1,0,1,17,1000]},
                  {'name':'deep','count':24,'shape':'deep','depths':[1,2,4,8],'numbers':[-17,-1,0,1,17]},
                  {'name':'long_spines','count':16,'shape':'spine','depths':[8,16,24,32],'numbers':[-17,-1,0,1,17]}],
              'max_nodes_per_argument':256,'node_work_per_call':200000,
              'integer_semantics':'Mathematical integer evaluator; reject out-of-signed32 intermediates; no C++ overflow theorem',
              'all_generation_and_evaluation_failures_preserved':True,'no_retuning_first_results':True,
              'typechecking_does_not_prove_termination_or_equivalence':True,
              'large_inputs_may_exceed_upstream_sample_scope':True,'fresh_eligible':0,
              'G0_passed':False,'G1_admitted':False,'G2_admitted':False,'learning_performed':False}
    raw=(json.dumps(contract,indent=2)+'\n').encode();(target/'registration.json').write_bytes(raw)
    for name in sources:
        destination=target/'pinned'/name;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes((repo/name).read_bytes())
    freeze={'registration_sha256':hashlib.sha256(raw).hexdigest(),'source_pins':contract['source_pins'],'execution_started':False}
    (target/'freeze.json').write_text(json.dumps(freeze,indent=2)+'\n')
    print(json.dumps(freeze,indent=2))


if __name__=='__main__':main()
