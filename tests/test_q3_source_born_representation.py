"""Q3 source-born representation tests; only executable meaning, no toy win count.

External original 00576224 is an explicitly source-observed DEVELOPMENT item,
not an untouched first original. Original gold is pinned and checked by the
separate freeze-first Actions job; this fixture does not claim universal Q3.
"""
from neumann1.source_born_representation_inventor import (
    SourceBornRepresentationInventor)


def test_raw_source_can_invent_2d_address_program_and_new_shape():
    # This is a bytecode regression, not independent scientific evidence.
    # Source-inferred law: repeat an input tile while reversing alternating
    # vertical tiles; neither operation name is supplied as a learner hint.
    def oracle(inp):
        h,w=len(inp),len(inp[0])
        return tuple(
            tuple(inp[r%h][(w-1-c%w) if (r//h)%2 else c%w]
                  for c in range(3*w))
            for r in range(3*h))
    inputs=(
        ((1,2),(3,4)),
        ((7,9),(4,3)),
        ((4,1,2),(6,7,8)),
        ((9,6,4),(2,5,8)),
    )
    engine=SourceBornRepresentationInventor(max_ms=5000)
    result=engine.invent(
        tuple((x,oracle(x)) for x in inputs[:2]),
        independent_source_checks=tuple(
            (x,oracle(x)) for x in inputs[2:]))
    assert result.status=="SOURCE_VERIFIED_NEW_PROGRAM",result
    assert result.programs
    method=result.programs[0]
    assert method.ast[0]=="learned_generic_index_algebra"
    x=((1,4,7,2),(9,5,3,8),(6,7,2,1))
    assert method.apply(x)==oracle(x)
    next_source=(
        (((6,5),(3,1)),oracle(((6,5),(3,1)))),
        (((8,9),(2,4)),oracle(((8,9),(2,4)))),
    )
    reuse=engine.invent(
        (next_source[0],),
        independent_source_checks=(next_source[1],))
    assert reuse.status=="SOURCE_VERIFIED_REUSED_INVENTED_MACRO",reuse


def test_same_meta_algebra_works_on_1d_strings():
    oracle=lambda x:x*3
    samples=("ab","cd","wx","zz","foobar")
    learner=SourceBornRepresentationInventor(max_ms=2500)
    discovery=learner.invent(
        tuple((x,oracle(x)) for x in samples[:2]),
        independent_source_checks=tuple((x,oracle(x)) for x in samples[2:4]))
    assert discovery.programs
    assert discovery.apply(samples[-1])==oracle(samples[-1])


def test_no_program_is_invented_for_new_unavailable_source_values():
    learner=SourceBornRepresentationInventor(max_ms=500)
    # Index-address programs only FETCH original values; they cannot invent
    # the unseen output color 5 and must decline rather than hallucinate.
    r=learner.invent(
        ((((0,1),(1,0)),((5,5),(5,5))),),
        independent_source_checks=(
            (((0,3),(3,0)),((5,5),(5,5))),))
    assert not r.programs
    assert r.status.startswith("ABSTAIN")


def test_no_training_program_or_task_label_is_needed():
    learner=SourceBornRepresentationInventor(max_ms=1200)
    src=((1,2,3),)
    res=learner.invent(
        ((src,src),),
        independent_source_checks=((((4,5,6),),((4,5,6),)),))
    assert res.programs
    assert "input" not in vars(learner)  # no task/domain routing state
