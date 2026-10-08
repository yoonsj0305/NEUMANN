"""Independent evaluator for a declared pure functional source language.

This is counterexample infrastructure, not a compiler, universal equivalence
proof, or learned perspective mechanism. Types/marks are retained as metadata;
execution erases Compress/label/unlabel/align. Integers are mathematical, with
an optional signed range check. Imports, effects and unknown syntax fail closed.
"""
from dataclasses import dataclass
import re


class SourceError(ValueError):
    pass


class WorkLimit(SourceError):
    pass


@dataclass(frozen=True)
class Data:
    constructor: str
    payload: object


@dataclass(frozen=True)
class Closure:
    name: str
    declared: tuple
    body: tuple
    env: dict


@dataclass
class Recursive:
    value: object = None


@dataclass(frozen=True)
class Constructor:
    name: str


RESERVED = {'if','then','else','let','letrec','in','match','with','end',
            'fix','lambda','label','unlabel','align','not','and','or',
            'Inductive','Config','import','Compress'}
IDENT = re.compile(r"[A-Za-z_][A-Za-z_0-9']*\Z")
TOKEN = re.compile(r'\s+|->|<=|>=|==|-?\d+|[A-Za-z_][A-Za-z_0-9\x27]*|"(?:[^"\\]|\\.)*"|[\\@{}(),.;:=+*/<>|\-]')


def tokens(text):
    if len(text) > 200_000:
        raise WorkLimit('Source byte budget')
    clean = []
    i = 0
    while i < len(text):
        if text.startswith('/*', i):
            depth = 1
            i += 2
            while depth:
                if i >= len(text):
                    raise SourceError('Unclosed comment')
                if text.startswith('/*', i):
                    depth += 1
                    i += 2
                elif text.startswith('*/', i):
                    depth -= 1
                    i += 2
                else:
                    i += 1
            clean.append(' ')
        elif text[i] == '"':
            match = TOKEN.match(text, i)
            if not match:
                raise SourceError('Unclosed string')
            clean.append(match.group())
            i = match.end()
        else:
            clean.append(text[i])
            i += 1
    value = ''.join(clean)
    output = []
    i = 0
    while i < len(value):
        match = TOKEN.match(value, i)
        if not match:
            raise SourceError(f'Unknown character at {i}: {value[i:i+20]!r}')
        token = match.group()
        if not token.isspace():
            output.append(token)
        i = match.end()
    if len(output) > 30_000:
        raise WorkLimit('Token budget')
    return output + ['<EOF>']


class Parser:
    def __init__(self, text):
        self.tokens = tokens(text)
        self.index = 0
        self.depth = 0

    def peek(self):
        return self.tokens[self.index]

    def take(self, expected=None):
        value = self.peek()
        if expected is not None and value != expected:
            raise SourceError(f'Expected {expected!r}, got {value!r} at token {self.index}')
        if value == '<EOF>':
            raise SourceError('Unexpected EOF')
        self.index += 1
        return value

    def name(self):
        value = self.take()
        if not IDENT.fullmatch(value) or value in RESERVED:
            raise SourceError(f'Invalid identifier {value!r}')
        return value

    def datatype(self):
        left = self.atomic_type()
        if self.peek() == '->':
            self.take()
            return ('arrow', left, self.datatype())
        return left

    def atomic_type(self):
        value = self.peek()
        if value == '(':
            self.take()
            result = self.datatype()
            self.take(')')
            return result
        if value == '{':
            self.take()
            fields = [self.datatype()]
            while self.peek() == ',':
                self.take()
                fields.append(self.datatype())
            self.take('}')
            return ('tuple', *fields)
        if value == 'Compress':
            self.take()
            return ('compress', self.atomic_type())
        return ('name', self.name())

    def program(self):
        commands = []
        while self.peek() != '<EOF>':
            decorations = []
            while self.peek() == '@':
                self.take()
                decorations.append(self.name())
            value = self.peek()
            if value == 'import':
                raise SourceError('Imports require explicit provenance and are unsupported')
            if value == 'Config':
                self.take()
                name = self.name()
                self.take('=')
                raw = self.take()
                if raw not in {'true','false'} and not re.fullmatch(r'-?\d+|"(?:[^"\\]|\\.)*"', raw):
                    raise SourceError('Invalid config value')
                commands.append(('config', name, raw))
            elif value == 'Inductive':
                self.take()
                while True:
                    name = self.name()
                    self.take('=')
                    constructors = []
                    while True:
                        cons = self.name()
                        constructors.append((cons, self.datatype()))
                        if self.peek() != '|':
                            break
                        self.take()
                    commands.append(('inductive', name, tuple(constructors)))
                    if self.peek() != 'with':
                        break
                    self.take()
            else:
                name = self.name()
                if name[0].isupper():
                    self.take('=')
                    commands.append(('alias', name, self.datatype()))
                elif self.peek() == ':':
                    self.take()
                    commands.append(('input', name, self.datatype(), tuple(decorations)))
                else:
                    self.take('=')
                    commands.append(('bind', name, self.expression(), tuple(decorations)))
            self.take(';')
        return tuple(commands)

    def expression(self):
        self.depth += 1
        if self.depth > 160:
            raise WorkLimit('AST nesting budget')
        try:
            return self._expression()
        finally:
            self.depth -= 1

    def _expression(self):
        head = self.peek()
        if head == 'if':
            self.take()
            condition = self.expression()
            self.take('then')
            yes = self.expression()
            self.take('else')
            return ('if', condition, yes, self.expression())
        if head in {'let', 'letrec'}:
            recursive = self.take() == 'letrec'
            name = self.name()
            if recursive:
                self.take(':')
                self.datatype()
            self.take('=')
            value = self.expression()
            self.take('in')
            return ('letrec' if recursive else 'let', name, value, self.expression())
        if head in {'\\', 'lambda'}:
            self.take()
            name = self.name()
            self.take(':')
            declared = self.datatype()
            self.take('.')
            return ('lambda', name, declared, self.expression())
        if head == 'match':
            self.take()
            subject = self.expression()
            self.take('with')
            cases = []
            while True:
                pattern = self.pattern()
                self.take('->')
                cases.append((pattern, self.expression()))
                if self.peek() != '|':
                    break
                self.take()
            self.take('end')
            return ('match', subject, tuple(cases))
        if head in {'fix','label','unlabel','align','not'}:
            self.take()
            result = (head, self.path())
        elif head in {'+','-','*','/','==','<','<=','>','>=','and','or'}:
            self.take()
            result = ('op', head, self.path(), self.path())
        else:
            result = self.path()
        while self.atom_start(self.peek()):
            result = ('apply', result, self.path())
        return result

    @staticmethod
    def atom_start(token):
        return (token in {'(', '{', 'true', 'false', 'unit'}
                or bool(re.fullmatch(r'-?\d+', token))
                or bool(IDENT.fullmatch(token) and token not in RESERVED))

    def path(self):
        result = self.atom()
        while self.peek() == '.':
            self.take()
            raw = self.take()
            if not re.fullmatch(r'[1-9]\d*', raw):
                raise SourceError('Tuple projections are one-based positive integers')
            result = ('project', result, int(raw))
        return result

    def atom(self):
        value = self.take()
        if value == '(':
            result = self.expression()
            while self.peek() == ';':
                self.take()
                result = ('sequence', result, self.expression())
            self.take(')')
            return result
        if value == '{':
            values = [self.expression()]
            while self.peek() == ',':
                self.take()
                values.append(self.expression())
            self.take('}')
            return ('tuple', *values)
        if value in {'true','false'}:
            return ('constant', value == 'true')
        if value == 'unit':
            return ('constant', None)
        if re.fullmatch(r'-?\d+', value):
            return ('constant', int(value))
        if IDENT.fullmatch(value) and value not in RESERVED:
            return ('variable', value)
        raise SourceError(f'Unexpected atom {value!r}')

    def pattern(self):
        value = self.take()
        if value == '(':
            result = self.pattern()
            self.take(')')
            return result
        if value == '{':
            fields = [self.pattern()]
            while self.peek() == ',':
                self.take()
                fields.append(self.pattern())
            self.take('}')
            return ('tuple', *fields)
        if value == '_':
            return ('wildcard',)
        if IDENT.fullmatch(value) and value not in RESERVED:
            if self.peek() in {'{','('} or (IDENT.fullmatch(self.peek()) and self.peek() not in RESERVED):
                return ('constructor', value, self.pattern())
            return ('variable', value)
        raise SourceError(f'Invalid pattern {value!r}')


def bind_pattern(pattern, value):
    kind = pattern[0]
    if kind == 'wildcard':
        return {}
    if kind == 'variable':
        return {pattern[1]: value}
    if kind == 'constructor':
        if not isinstance(value, Data) or value.constructor != pattern[1]:
            return None
        return bind_pattern(pattern[2], value.payload)
    if type(value) is not tuple or len(value) != len(pattern) - 1:
        return None
    result = {}
    for p, v in zip(pattern[1:], value):
        bindings = bind_pattern(p, v)
        if bindings is None:
            return None
        if result.keys() & bindings.keys():
            raise SourceError('Duplicate bindings in one pattern')
        result.update(bindings)
    return result


class Evaluator:
    def __init__(self, budget=200_000, signed_bits=None):
        if type(budget) is not int or budget < 1:
            raise SourceError('Invalid evaluation budget')
        if signed_bits is not None and signed_bits not in {32,64}:
            raise SourceError('Unsupported integer range contract')
        self.remaining = budget
        self.signed_bits = signed_bits

    def charge(self):
        self.remaining -= 1
        if self.remaining < 0:
            raise WorkLimit('Evaluation node budget')

    def integer(self, value):
        if type(value) is not int:
            raise SourceError('Integer operator received a non-integer')
        if self.signed_bits and not -(1 << (self.signed_bits-1)) <= value < (1 << (self.signed_bits-1)):
            raise SourceError('Outside declared signed integer range; no overflow equivalence claim')
        return value

    def boolean(self, value):
        if type(value) is not bool:
            raise SourceError('Boolean operator received a non-Boolean')
        return value

    def apply(self, function, argument):
        self.charge()
        if isinstance(function, Recursive):
            if function.value is None:
                raise SourceError('Recursive value forced before initialization')
            return self.apply(function.value, argument)
        if isinstance(function, Constructor):
            return Data(function.name, argument)
        if not isinstance(function, Closure):
            raise SourceError('Application of a non-function')
        return self.evaluate(function.body, {**function.env, function.name: argument})

    def evaluate(self, node, env):
        self.charge()
        kind = node[0]
        if kind == 'constant':
            return self.integer(node[1]) if type(node[1]) is int else node[1]
        if kind == 'variable':
            if node[1] not in env:
                raise SourceError(f'Unbound variable {node[1]!r}')
            return env[node[1]]
        if kind == 'lambda':
            return Closure(node[1], node[2], node[3], dict(env))
        if kind == 'apply':
            return self.apply(self.evaluate(node[1], env), self.evaluate(node[2], env))
        if kind == 'tuple':
            return tuple(self.evaluate(n, env) for n in node[1:])
        if kind == 'project':
            value = self.evaluate(node[1], env)
            if type(value) is not tuple or node[2] > len(value):
                raise SourceError('Invalid tuple projection')
            return value[node[2]-1]
        if kind == 'if':
            return self.evaluate(node[2] if self.boolean(self.evaluate(node[1], env)) else node[3], env)
        if kind in {'label','unlabel','align'}:
            return self.evaluate(node[1], env)
        if kind == 'not':
            return not self.boolean(self.evaluate(node[1], env))
        if kind == 'sequence':
            self.evaluate(node[1], env)
            return self.evaluate(node[2], env)
        if kind == 'let':
            return self.evaluate(node[3], {**env, node[1]: self.evaluate(node[2], env)})
        if kind == 'letrec':
            recursive = Recursive()
            nested = {**env, node[1]: recursive}
            recursive.value = self.evaluate(node[2], nested)
            if not isinstance(recursive.value, Closure):
                raise SourceError('Only functional recursive bindings are supported')
            return self.evaluate(node[3], nested)
        if kind == 'fix':
            function = self.evaluate(node[1], env)
            if not isinstance(function, Closure):
                raise SourceError('Fixpoint requires a lambda')
            recursive = Recursive()
            recursive.value = self.evaluate(function.body, {**function.env, function.name: recursive})
            if not isinstance(recursive.value, Closure):
                raise SourceError('Only functional fixpoints are supported')
            return recursive
        if kind == 'match':
            subject = self.evaluate(node[1], env)
            for pattern, body in node[2]:
                bindings = bind_pattern(pattern, subject)
                if bindings is not None:
                    return self.evaluate(body, {**env, **bindings})
            raise SourceError('Non-exhaustive match')
        if kind == 'op':
            op = node[1]
            a = self.evaluate(node[2], env)
            b = self.evaluate(node[3], env)
            if op in {'and','or'}:
                a, b = self.boolean(a), self.boolean(b)
                return a and b if op == 'and' else a or b
            a, b = self.integer(a), self.integer(b)
            if op == '+': return self.integer(a+b)
            if op == '-': return self.integer(a-b)
            if op == '*': return self.integer(a*b)
            if op == '/':
                if not b: raise SourceError('Division by zero')
                return self.integer((abs(a)//abs(b)) * (-1 if (a<0) != (b<0) else 1))
            if op == '==': return a == b
            if op == '<': return a < b
            if op == '<=': return a <= b
            if op == '>': return a > b
            if op == '>=': return a >= b
        raise SourceError(f'Unsupported expression kind {kind!r}')

    def load(self, commands, inputs=None):
        inputs = {} if inputs is None else dict(inputs)
        expected = {c[1] for c in commands if c[0] == 'input'}
        if set(inputs) != expected:
            raise SourceError(f'Input bindings differ: required {sorted(expected)}, supplied {sorted(inputs)}')
        env = {}
        for command in commands:
            if command[0] == 'inductive':
                for name, declared in command[2]:
                    env[name] = Constructor(name)
            elif command[0] == 'input':
                env[command[1]] = inputs[command[1]]
            elif command[0] == 'bind':
                env[command[1]] = self.evaluate(command[2], env)
        return env


def parse(text):
    try:
        return Parser(text).program()
    except RecursionError as error:
        raise WorkLimit('Parser recursion budget') from error


def execute(commands, arguments=(), inputs=None, name='main', budget=200_000, signed_bits=None):
    evaluator = Evaluator(budget, signed_bits)
    try:
        env = evaluator.load(commands, inputs)
        if name not in env:
            raise SourceError(f'Missing entrypoint {name!r}')
        result = env[name]
        for argument in arguments:
            result = evaluator.apply(result, argument)
        if isinstance(result, (Closure, Recursive, Constructor)):
            raise SourceError('Entrypoint remains a function; all arguments must be supplied')
        return result
    except RecursionError as error:
        raise WorkLimit('Evaluator recursion budget') from error
