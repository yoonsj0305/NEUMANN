import pickle
import numpy as np
import pytest
from neumann1.pickle_metadata import read,array,MetadataError,Call,Symbol


@pytest.mark.parametrize('protocol',[4,5])
@pytest.mark.parametrize('dtype',['int16','int64','float32','float64','complex128','bool'])
@pytest.mark.parametrize('order',['C','F'])
def test_inert_numpy_metadata_and_bytes_match_without_unpickling(protocol,dtype,order):
    values=np.arange(12).reshape(3,4).astype(dtype,order=order)
    value,symbols=read(pickle.dumps(values,protocol=protocol))
    raw=array(value)
    restored=np.frombuffer(raw.raw,dtype=raw.dtype).reshape(raw.shape,order=raw.order)
    assert np.array_equal(restored,values)
    assert raw.metadata()['shape']==[3,4]


def test_scalar_and_endian_layout_are_explicit():
    source=np.array([1,255,-9],dtype='>i8')
    raw=array(read(pickle.dumps(source,protocol=4))[0])
    assert raw.dtype=='>i8'
    assert np.array_equal(np.frombuffer(raw.raw,dtype=raw.dtype),source)
    raw=array(read(pickle.dumps(np.float64(3.125),protocol=4))[0])
    assert raw.shape==()
    assert np.frombuffer(raw.raw,dtype=raw.dtype)[0]==3.125


def test_reduce_and_build_never_execute_payload_callables():
    class Executable:
        def __reduce__(self):return eval,('1/0',)
    value,symbols=read(pickle.dumps(Executable(),protocol=4))
    assert isinstance(value,Call)
    assert value.symbol==Symbol('builtins','eval')
    with pytest.raises(MetadataError):array(value)


def test_object_and_structured_arrays_are_not_silently_numeric():
    for value in [np.array([{'x':1}],dtype=object),np.array([(1,2)],dtype=[('a','i4'),('b','i4')])]:
        inert,_=read(pickle.dumps(value,protocol=4))
        with pytest.raises(MetadataError):array(inert)


def test_nested_plain_metadata_memo_aliases_and_raw_bytes_are_preserved():
    shared=[(0,1),(1,2)]
    value={'format':'ab,bc->ac','paths':(shared,shared),'bytes':b'\x00\xff','flag':True}
    decoded,_=read(pickle.dumps(value,protocol=4))
    assert decoded==value
    assert decoded['paths'][0]is decoded['paths'][1]


def test_declared_byte_and_opcode_budgets_fail_closed():
    raw=pickle.dumps(list(range(20)),protocol=4)
    with pytest.raises(MetadataError):read(raw,max_bytes=4)
    with pytest.raises(MetadataError):read(raw,max_ops=3)
