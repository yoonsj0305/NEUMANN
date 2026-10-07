import pytest
from neumann1.functional_source import parse,SourceError
from neumann1.functional_types import check,TypeChecker,compatible


def test_recursive_types_and_lexical_shadowing():
    commands=parse(r'''
    Inductive T=leaf Int | node {T,T};
    x=true; f=fix (\f:T->Int. \x:T.
      match x with leaf x -> x | node {l,r} -> + (f l) (f r) end);
    main=\t:T. f t;
    ''')
    assert check(commands)['main']==('arrow',('name','T'),('name','Int'))


def test_compression_erasure_is_declared_and_preserves_type_shape():
    commands=parse(r'''
    Inductive L=nil Unit | cons {Int,L};
    f=fix (\f:L->Compress L. \x:L.
      match x with nil _ -> x | cons {h,t} -> cons {h,f t} end);
    main=\x:L. align (unlabel (label (f x)));
    ''')
    assert check(commands)['main']==('arrow',('name','L'),('name','L'))


@pytest.mark.parametrize('text',[
    'main=if true then 0 else missing;',
    'main=if true then 0 else false;',
    'main=\\x:Int. + x true;',
    'main=fix (\\f:Int->Int. \\x:Int. true);',
    'main={0,true}.3;',
    'Inductive T=a Int; Inductive U=b Int; main=\\x:T. match x with b y -> y end;',
    'Inductive T=a {Int,Int}; main=\\x:T. match x with a {y,y} -> y end;',
    'main=\\x:Missing. x;',
    'Alias=Alias; main=\\x:Alias. x;',
    'Inductive A=a Int; Inductive B=a Bool; main=0;',
])
def test_unreachable_wrong_branches_and_structural_type_errors_are_rejected(text):
    with pytest.raises(SourceError):check(parse(text))


def test_same_type_name_cannot_hide_a_changed_public_constructor_payload():
    original=parse('Inductive T=a Int | pair {T,T}; main=\\x:T. x;')
    changed=parse('Inductive T=a Bool | pair {T,T}; main=\\x:T. x;')
    left=TypeChecker(original);right=TypeChecker(changed)
    assert not compatible(left.check(original)['main'],right.check(changed)['main'],left,right)
    equivalent=parse('Inductive U=a Int | pair {U,U}; main=\\x:U. x;')
    other=TypeChecker(equivalent)
    assert compatible(left.check(original)['main'],other.check(equivalent)['main'],left,other)
