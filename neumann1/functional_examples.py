"""Type-directed concrete witnesses for opened pure functional programs.

No task names or solution outputs influence input generation. These are bounded
development witnesses, not fresh tests, universal proofs, or type inference.
"""
import random
from neumann1.functional_source import (Data, Closure, Recursive, Constructor,
                                        Evaluator, SourceError, WorkLimit)


def encode(value):
    if isinstance(value, Data):
        return {'constructor': value.constructor, 'payload': encode(value.payload)}
    if type(value) is tuple:
        return [encode(v) for v in value]
    if value is None or type(value) in {bool,int}:
        return value
    raise SourceError('Non-first-order witness value')


def decode(value, depth=0):
    if depth > 100:
        raise WorkLimit('Witness depth budget')
    if type(value) is dict and set(value) == {'constructor','payload'}:
        if type(value['constructor']) is not str:
            raise SourceError('Invalid witness constructor')
        return Data(value['constructor'], decode(value['payload'], depth+1))
    if type(value) is list:
        return tuple(decode(v, depth+1) for v in value)
    if value is None or type(value) in {bool,int}:
        return value
    raise SourceError('Invalid witness schema')


def nodes(value):
    if isinstance(value, Data):
        return 1 + nodes(value.payload)
    if type(value) is tuple:
        return 1 + sum(nodes(v) for v in value)
    return 1


class Sampler:
    def __init__(self, commands, seed, numbers=(-2,-1,0,1,2), max_nodes=256, shape='random'):
        self.adts = {c[1]: c[2] for c in commands if c[0] == 'inductive'}
        self.aliases = {c[1]: c[2] for c in commands if c[0] == 'alias'}
        self.random = random.Random(seed)
        self.numbers = tuple(numbers)
        self.max_nodes = max_nodes
        if shape not in {'random','deep','spine'}:
            raise SourceError('Unknown structural sampling mode')
        self.shape = shape
        self.cache = {}
        if not self.numbers or any(type(v) is not int for v in self.numbers):
            raise SourceError('Invalid primitive input domain')

    def minimum(self, declared, seen=frozenset()):
        key = (declared, seen)
        if key in self.cache:
            return self.cache[key]
        kind = declared[0]
        if kind == 'compress':
            value = self.minimum(declared[1], seen)
        elif kind == 'tuple':
            value = tuple(self.minimum(t, seen) for t in declared[1:])
        elif kind == 'arrow':
            raise SourceError('Function-valued input requires a separate contract')
        elif kind == 'name':
            name = declared[1]
            if name == 'Int': value = 0
            elif name == 'Bool': value = False
            elif name == 'Unit': value = None
            elif name in seen:
                raise SourceError('No finite value along this constructor path')
            elif name in self.aliases:
                value = self.minimum(self.aliases[name], seen | {name})
            elif name in self.adts:
                candidates = []
                for constructor, payload_type in self.adts[name]:
                    try:
                        candidates.append(Data(constructor, self.minimum(payload_type, seen | {name})))
                    except SourceError:
                        pass
                if not candidates:
                    raise SourceError(f'No finite inhabitant for {name!r}')
                value = min(candidates, key=nodes)
            else:
                raise SourceError(f'Unknown input type {name!r}')
        else:
            raise SourceError(f'Unsupported input type {declared!r}')
        self.cache[key] = value
        return value

    def make(self, declared, depth, fuel=None, alias_seen=frozenset()):
        fuel = [self.max_nodes] if fuel is None else fuel
        fuel[0] -= 1
        if fuel[0] < 1 or depth < 0:
            return self.minimum(declared)
        kind = declared[0]
        if kind == 'compress':
            return self.make(declared[1], depth, fuel, alias_seen)
        if kind == 'tuple':
            values=[];expanded=False
            for t in declared[1:]:
                nested_depth=depth
                if self.shape=='spine' and self.contains_inductive(t):
                    nested_depth=0 if expanded else depth
                    expanded=True
                values.append(self.make(t,nested_depth,fuel,alias_seen))
            return tuple(values)
        if kind != 'name':
            return self.minimum(declared)
        name = declared[1]
        if name == 'Int': return self.random.choice(self.numbers)
        if name == 'Bool': return bool(self.random.randrange(2))
        if name == 'Unit': return None
        if name in self.aliases:
            if name in alias_seen:
                raise SourceError('Recursive type alias')
            return self.make(self.aliases[name], depth, fuel, alias_seen | {name})
        if name not in self.adts:
            raise SourceError(f'Unknown input type {name!r}')
        if depth == 0:
            return self.minimum(declared)
        if self.shape in {'deep','spine'}:
            ranked = []
            for constructor, payload_type in self.adts[name]:
                try:ranked.append((nodes(self.minimum(payload_type)), constructor, payload_type))
                except SourceError:pass
            if not ranked:raise SourceError('No finite constructor payload')
            score = max(r[0] for r in ranked)
            _, constructor, payload_type = self.random.choice([r for r in ranked if r[0]==score])
        else:
            constructor, payload_type = self.random.choice(self.adts[name])
        value = Data(constructor, self.make(payload_type, depth-1, fuel))
        if nodes(value) > self.max_nodes:
            raise WorkLimit('Generated witness node budget')
        return value

    def contains_inductive(self,declared,seen=frozenset()):
        if declared[0]=='name':
            name=declared[1]
            if name in self.adts:return True
            if name in self.aliases and name not in seen:return self.contains_inductive(self.aliases[name],seen|{name})
            return False
        return any(self.contains_inductive(t,seen) for t in declared[1:])

    def sample(self,declared,depth):
        value=self.make(declared,depth)
        if nodes(value)>self.max_nodes:raise WorkLimit('Complete witness node budget')
        return value


def entrypoints(commands):
    explicit = [c[1] for c in commands if c[0] == 'bind' and 'Start' in c[3]]
    if explicit:
        return explicit
    runtime = [c for c in commands if c[0] != 'config']
    if not runtime or runtime[-1][0] != 'bind':
        raise SourceError('No declared/default term entrypoint')
    return [runtime[-1][1]]


def concrete_call(commands, sampler, depth, budget=200_000, entrypoint=None):
    inputs = {c[1]: sampler.sample(c[2], depth) for c in commands if c[0] == 'input'}
    evaluator = Evaluator(budget=budget, signed_bits=32)
    env = evaluator.load(commands, inputs)
    entrypoint = entrypoints(commands)[0] if entrypoint is None else entrypoint
    if entrypoint not in entrypoints(commands) or entrypoint not in env:
        raise SourceError('Entrypoint is not declared by the original program')
    function = env[entrypoint]
    arguments = []
    while isinstance(function, (Closure, Recursive, Constructor)):
        while isinstance(function, Recursive):
            function = function.value
        if not isinstance(function, Closure):
            raise SourceError('Constructor-valued main entrypoint')
        if len(arguments) >= 8:
            raise WorkLimit('Entrypoint arity budget')
        value = sampler.sample(function.declared, depth)
        arguments.append(value)
        function = evaluator.apply(function, value)
    return {'inputs': {k: encode(v) for k,v in inputs.items()},
            'arguments': [encode(v) for v in arguments], 'original_output': encode(function),
            'steps_consumed': budget-evaluator.remaining,
            'domain': 'Declared ADTs; bounded generated mathematical values; signed32 arithmetic checks',
            'original_named_entrypoint': entrypoint, 'fresh_eligible': False}
