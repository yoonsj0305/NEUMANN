"""Non-executing pickle opcode reader for inspected benchmark metadata.

GLOBAL/REDUCE/BUILD remain inert records. No pickle.load, imports from payload,
callable lookup, object constructors, or __setstate__ calls are performed.
Unknown executable symbols cannot become numeric arrays.
"""
from dataclasses import dataclass
import hashlib,math,pickletools,re


class MetadataError(ValueError):pass


@dataclass(frozen=True)
class Symbol:
    module:str
    name:str


@dataclass
class Call:
    symbol:object
    arguments:object
    state:object=None


@dataclass(frozen=True)
class NumericArray:
    shape:tuple
    dtype:str
    order:str
    raw:bytes

    def metadata(self):
        return {'shape':list(self.shape),'dtype':self.dtype,'order':self.order,
                'bytes':len(self.raw),'data_sha256':hashlib.sha256(self.raw).hexdigest()}


def read(raw,max_bytes=128*1024*1024,max_ops=2_000_000,max_memo=500_000):
    if type(raw)is not bytes or len(raw)>max_bytes:raise MetadataError('Pickle byte budget')
    stack=[];memo={};mark=object();globals_seen=set();stopped=False
    def marked():
        try:index=len(stack)-1-stack[::-1].index(mark)
        except ValueError as error:raise MetadataError('Missing MARK')from error
        items=stack[index+1:];del stack[index:];return items
    for count,(op,arg,pos) in enumerate(pickletools.genops(raw)):
        if count>=max_ops:raise MetadataError('Opcode budget')
        name=op.name
        if name in {'PROTO','FRAME'}:continue
        if name=='MARK':stack.append(mark)
        elif name=='STOP':
            if len(stack)!=1 or stack[0]is mark:raise MetadataError('Invalid final stack')
            stopped=True;break
        elif name=='NONE':stack.append(None)
        elif name=='NEWTRUE':stack.append(True)
        elif name=='NEWFALSE':stack.append(False)
        elif name in {'INT','BININT','BININT1','BININT2','LONG','LONG1','LONG4','FLOAT','BINFLOAT',
                      'STRING','BINSTRING','SHORT_BINSTRING','UNICODE','BINUNICODE','SHORT_BINUNICODE',
                      'BINUNICODE8','BINBYTES','SHORT_BINBYTES','BINBYTES8','BYTEARRAY8'}:
            stack.append(arg)
        elif name=='EMPTY_LIST':stack.append([])
        elif name=='EMPTY_DICT':stack.append({})
        elif name=='EMPTY_TUPLE':stack.append(())
        elif name=='LIST':stack.append(marked())
        elif name=='TUPLE':stack.append(tuple(marked()))
        elif name in {'TUPLE1','TUPLE2','TUPLE3'}:
            n=int(name[-1]);items=stack[-n:];del stack[-n:];stack.append(tuple(items))
        elif name=='APPEND':
            value=stack.pop()
            if type(stack[-1])is not list:raise MetadataError('APPEND target')
            stack[-1].append(value)
        elif name=='APPENDS':
            items=marked()
            if type(stack[-1])is not list:raise MetadataError('APPENDS target')
            stack[-1].extend(items)
        elif name=='DICT':
            items=marked()
            if len(items)%2:raise MetadataError('DICT arity')
            stack.append(dict(zip(items[::2],items[1::2])))
        elif name=='SETITEM':
            value=stack.pop();key=stack.pop()
            if type(stack[-1])is not dict:raise MetadataError('SETITEM target')
            stack[-1][key]=value
        elif name=='SETITEMS':
            items=marked()
            if type(stack[-1])is not dict or len(items)%2:raise MetadataError('SETITEMS target')
            stack[-1].update(zip(items[::2],items[1::2]))
        elif name in {'PUT','BINPUT','LONG_BINPUT','MEMOIZE'}:
            index=len(memo)if name=='MEMOIZE'else int(arg)
            if index<0 or index>max_memo or len(memo)>=max_memo:raise MetadataError('Memo budget')
            memo[index]=stack[-1]
        elif name in {'GET','BINGET','LONG_BINGET'}:
            if int(arg)not in memo:raise MetadataError('Unknown memo reference')
            stack.append(memo[int(arg)])
        elif name=='GLOBAL':
            module,item=arg.split(' ',1);globals_seen.add((module,item));stack.append(Symbol(module,item))
        elif name=='STACK_GLOBAL':
            item=stack.pop();module=stack.pop()
            if type(item)is not str or type(module)is not str:raise MetadataError('Invalid global names')
            globals_seen.add((module,item));stack.append(Symbol(module,item))
        elif name=='REDUCE':
            arguments=stack.pop();symbol=stack.pop()
            if type(arguments)is not tuple:raise MetadataError('REDUCE arguments must be a tuple')
            stack.append(Call(symbol,arguments))
        elif name=='BUILD':
            state=stack.pop()
            if not isinstance(stack[-1],Call):raise MetadataError('BUILD target remains an inert call only')
            stack[-1].state=state
        elif name=='NEWOBJ':
            arguments=stack.pop();symbol=stack.pop();stack.append(Call(('NEWOBJ',symbol),arguments))
        elif name=='NEWOBJ_EX':
            kwargs=stack.pop();arguments=stack.pop();symbol=stack.pop();stack.append(Call(('NEWOBJ_EX',symbol),(arguments,kwargs)))
        elif name=='POP':stack.pop()
        elif name=='POP_MARK':marked()
        elif name=='DUP':stack.append(stack[-1])
        else:raise MetadataError(f'Unsupported inert opcode {name}')
        if len(stack)>max_ops:raise MetadataError('Stack budget')
    if not stopped:raise MetadataError('Missing STOP')
    return stack[0],sorted(globals_seen)


def dtype(value):
    if not isinstance(value,Call)or value.symbol!=Symbol('numpy','dtype')or not value.arguments:
        raise MetadataError('Expected inert numpy dtype record')
    code=value.arguments[0]
    aliases={'float64':'f8','float32':'f4','int64':'i8','int32':'i4','int16':'i2','int8':'i1',
             'uint64':'u8','uint32':'u4','uint16':'u2','uint8':'u1','complex128':'c16','complex64':'c8','bool':'b1'}
    code=aliases.get(code,code)
    if type(code)is not str or not re.fullmatch(r'[biufc](?:1|2|4|8|16)',code):raise MetadataError('Non-numeric or structured dtype')
    width=int(code[1:])
    if (code[0]=='b'and width!=1)or(code[0]=='f'and width not in {4,8})or(code[0]=='c'and width not in {8,16})or(code[0]in {'i','u'}and width not in {1,2,4,8}):raise MetadataError('Unsupported numeric dtype width')
    endian='|'
    if value.state is not None:
        if type(value.state)is not tuple or len(value.state)<2 or value.state[1]not in {'<','>','|','='}:raise MetadataError('Unsupported dtype state')
        if len(value.state)>3 and any(v is not None for v in value.state[2:4]):raise MetadataError('Structured dtype state')
        endian=value.state[1]
    return endian+code,width


def array(value):
    if not isinstance(value,Call)or not isinstance(value.symbol,Symbol):raise MetadataError('Expected inert array record')
    symbol=value.symbol
    if symbol.name=='_reconstruct'and symbol.module in {'numpy.core.multiarray','numpy._core.multiarray'}:
        if value.arguments!=(Symbol('numpy','ndarray'),(0,),b'b'):raise MetadataError('Unsupported ndarray constructor arguments')
        state=value.state
        if type(state)is not tuple or len(state)!=5 or state[0]!=1:raise MetadataError('Unsupported ndarray state')
        _,shape,t,is_fortran,raw=state
        if type(is_fortran)is not bool:raise MetadataError('Invalid array layout flag')
        order='F'if is_fortran else'C'
    elif symbol.name=='_frombuffer'and symbol.module in {'numpy.core.numeric','numpy._core.numeric'}:
        if len(value.arguments)!=4:raise MetadataError('Unsupported frombuffer state')
        raw,t,shape,order=value.arguments
    elif symbol.name=='scalar'and symbol.module in {'numpy.core.multiarray','numpy._core.multiarray'}:
        if len(value.arguments)!=2:raise MetadataError('Unsupported scalar state')
        t,raw=value.arguments;shape=();order='C'
    else:raise MetadataError(f'Unrecognized inert numeric symbol {symbol!r}')
    if type(shape)is not tuple or len(shape)>128 or any(type(v)is not int or not 0<=v<=1_000_000 for v in shape):raise MetadataError('Invalid numeric shape')
    if order not in {'C','F'}or type(raw)not in {bytes,bytearray}:raise MetadataError('Invalid numeric layout/data')
    code,width=dtype(t)
    if math.prod(shape)*width!=len(raw):raise MetadataError('Array byte size differs from shape/dtype')
    return NumericArray(shape,code,order,bytes(raw))
