import pytest
from neumann1.functional_source import parse, execute, Data, SourceError
from neumann1.functional_examples import Sampler, encode, decode, concrete_call, entrypoints


def test_type_directed_witnesses_bind_original_goal_without_name_lookup():
    commands=parse(r'''
    Inductive Strange = z Unit | successor {Int,Strange};
    run=fix (\f:Strange -> Int. \v:Strange.
      match v with z _ -> 0 | successor {x,t} -> + x (f t) end);
    @Input offset:Int; main=\v:Strange. + offset (run v);
    ''')
    sampler=Sampler(commands,17)
    for depth in range(8):
        row=concrete_call(commands,sampler,depth)
        assert execute(commands,[decode(v) for v in row['arguments']],
                       {k:decode(v) for k,v in row['inputs'].items()},signed_bits=32)==row['original_output']


def test_mutual_recursive_datatypes_have_finite_minimum_and_valid_samples():
    commands=parse(r'''
    Inductive Tree = tip Int | branch Forest
      with Forest = empty Unit | join {Tree,Forest};
    main=\x:Tree. match x with tip n -> n | branch _ -> -1 end;
    ''')
    sampler=Sampler(commands,11)
    assert sampler.minimum(('name','Tree'))==Data('tip',0)
    for _ in range(20):
        assert type(concrete_call(commands,sampler,4)['original_output']) is int


def test_witness_serialization_preserves_bool_int_tuple_and_constructors():
    value=Data('b',(True,1,None,Data('a',(-7,False))))
    assert decode(encode(value))==value
    with pytest.raises(SourceError):decode({'constructor':'a','payload':0,'extra':1})


def test_no_finite_domain_or_function_input_is_reported_not_invented():
    commands=parse('Inductive Loop = loop Loop; main=0;')
    with pytest.raises(SourceError):Sampler(commands,1).minimum(('name','Loop'))
    commands=parse(r'main=\f:Int -> Int. f 0;')
    with pytest.raises(SourceError,match='Function-valued'):
        concrete_call(commands,Sampler(commands,1),3)


def test_same_seed_reproduces_structures_and_explicit_parameters():
    commands=parse(r'@Input x:Int; Inductive T = leaf Int | node {T,T}; main=\t:T. x;')
    left=Sampler(commands,55);right=Sampler(commands,55)
    assert [concrete_call(commands,left,4) for _ in range(10)]==[concrete_call(commands,right,4) for _ in range(10)]


def test_declared_start_and_default_final_binding_are_semantic_not_named():
    commands=parse(r'main=0; @Start chosen=\x:Int. + x 4; unrelated=9;')
    assert entrypoints(commands)==['chosen']
    row=concrete_call(commands,Sampler(commands,7),2)
    assert row['original_named_entrypoint']=='chosen'
    assert row['original_output']==row['arguments'][0]+4
    commands=parse(r'first=8; arbitrary=\x:Int. x;')
    assert entrypoints(commands)==['arbitrary']
    with pytest.raises(SourceError):concrete_call(commands,Sampler(commands,1),1,entrypoint='first')


def test_deep_shapes_exercise_recursion_instead_of_mostly_empty_inputs():
    commands=parse(r'''
    Inductive L=nil Unit | cons {Int,L};
    length=fix (\f:L->Int. \x:L. match x with nil _ -> 0 | cons {_,t} -> + 1 (f t) end);
    main=\x:L. length x;
    ''')
    row=concrete_call(commands,Sampler(commands,13,shape='deep'),16)
    assert row['original_output']==16


def test_spine_shapes_cover_long_branches_without_exponential_expansion():
    commands=parse(r'''
    Inductive T=leaf Unit | node {T,T};
    height=fix (\f:T->Int. \t:T. match t with leaf _ -> 0 | node {l,r} -> + 1 (f l) end);
    main=\x:T. height x;
    ''')
    row=concrete_call(commands,Sampler(commands,9,shape='spine'),32)
    assert row['original_output']==32
