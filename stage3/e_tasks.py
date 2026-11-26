"""3-E0 (stage3/DESIGN.md 9.1): the 15 tasks of Deletang et al. (ICLR 2023), ported from the public code.

Source: github.com/google-deepmind/neural_networks_chomsky_hierarchy, commit 2b8eb4bee872acf5b637fcc672f01c06939dc4ef
(2024-04-12), files tasks/{regular,dcf,cs}/*.py; task parameters from experiments/constants.py TASK_BUILDERS
(modular_arithmetic_brackets with mult=True; every other task with its default arguments).  Apache License 2.0.

Two layers:
  1 GEN[task](n, rng) -> (input, output) in the benchmark's own integer / character encoding.  The generation rules are
    the benchmark's, line by line (comments name the source function).  Only the random source differs: every draw
    (jax.random, np.random, random) is taken from one python random.Random, with the same bounds (np.random.randint
    and jax.random.randint: high exclusive -> rng.randrange; random.randint: inclusive -> rng.randint).
  2 FORMAT (9.1, one rule for every task):  <bos> input = output <eos>;  a classification task's output is its class as
    one token.  Token kinds: data symbols -> digit, operation / command symbols -> op, the separator between input and
    output -> '=', anything else -> other.  SYMBOLS[task] lists every benchmark symbol with its token and kind.
    The four 3-E0 format questions (QUESTIONS) were answered in DESIGN 10.1-1 (ANSWERS) and are applied; no entry is
    PENDING now.
Length (9.1): the benchmark's `length` argument n; training 1-10, in-distribution 1-10, out-of-distribution
11-20 / 21-30 / 31-40, n uniform in the range (one rng.randint draw, then the generator's draws, as l_tasks.draw).
Generation seeds: the stage-1 functions (tasks.train_set / eval_sets) through stage3/e0.py install().
"""
from __future__ import annotations
import math

SOURCE = {"repo": "github.com/google-deepmind/neural_networks_chomsky_hierarchy",
          "commit": "2b8eb4bee872acf5b637fcc672f01c06939dc4ef", "commit_date": "2024-04-12 10:58:08 +0100"}
LEVEL = {"modular_arithmetic": "regular", "parity_check": "regular", "even_pairs": "regular",
         "cycle_navigation": "regular", "modular_arithmetic_brackets": "dcf", "reverse_string": "dcf",
         "stack_manipulation": "dcf", "solve_equation": "dcf", "missing_duplicate_string": "cs",
         "compute_sqrt": "cs", "duplicate_string": "cs", "odds_first": "cs", "binary_addition": "cs",
         "binary_multiplication": "cs", "bucket_sort": "cs"}
SUITE = tuple(LEVEL)
CLASSIFICATION = ("modular_arithmetic", "parity_check", "even_pairs", "cycle_navigation",
                  "modular_arithmetic_brackets", "solve_equation", "missing_duplicate_string")
SPEC = {t: {"train": (1, 10), "id": (1, 10), "ood": [(11, 20), (21, 30), (31, 40)]} for t in SUITE}


# ============================================================== 1. generators (benchmark encoding)
def _bits(n, rng, vocab=2):
    return [rng.randrange(0, vocab) for _ in range(n)]


# ---- regular
def modular_arithmetic(length, rng, modulus=5):
    """tasks/regular/modular_arithmetic.py ModularArithmetic.sample_batch (operators default ('+', '*', '-'));
    input ints: residues 0..4, operators modulus + OP_BY_CHARACTER {'+': 0, '-': 1, '*': 2}"""
    op_by_character = {'+': 0, '-': 1, '*': 2, '_': 3}
    if length % 2 != 1:                                          # "Subtracting one to the length if it's not odd"
        length -= 1
    remainders = [rng.randrange(0, modulus) for _ in range(length // 2 + 1)]
    ops = [modulus + op_by_character[o] for o in ('+', '*', '-')]
    operations = [rng.choice(ops) for _ in range(length // 2)]
    expr = [0] * length
    expr[::2] = remainders
    expr[1::2] = operations
    return expr, [_evaluate_expression(expr, modulus, op_by_character)]


def _evaluate_expression(expression, modulus, op_by_character):
    """_replace_blanks (no blanks: '_' is never sampled), _replace_subtractions, _perform_multiplications, sum mod"""
    e = list(expression)
    plus, minus = modulus + op_by_character['+'], modulus + op_by_character['-']
    if len(e) >= 2:                                              # _replace_subtractions
        mask = [x == minus for x in e]
        e = [plus if m else x for x, m in zip(e, mask)]
        e = e[:2] + [x * (1 - 2 * mask[i + 1]) for i, x in enumerate(e[2:])]
    terms, cur = [], e[0]                                        # _perform_multiplications (segment products)
    for i in range(1, len(e), 2):
        if e[i] == plus:
            terms.append(cur)
            cur = e[i + 1]
        else:                                                    # '*'
            cur = cur * e[i + 1]
    terms.append(cur)
    return sum(terms) % modulus


def parity_check(length, rng):
    """tasks/regular/parity_check.py: class = number of 1s mod 2"""
    s = _bits(length, rng)
    return s, [sum(s) % 2]


def even_pairs(length, rng):
    """tasks/regular/even_pairs.py: class = number of unequal adjacent pairs ('01' and '10') mod 2"""
    s = _bits(length, rng)
    return s, [sum(a != b for a, b in zip(s[:-1], s[1:])) % 2]


def cycle_navigation(length, rng, cycle_length=5):
    """tasks/regular/cycle_navigation.py: actions are the ints 0, 1, 2 and action a moves by a - 1 on the circle
    (final_states = sum(actions - 1) % 5; the docstring calls the moves -1 left, 0 stay, 1 right)"""
    actions = [rng.randrange(0, 3) for _ in range(length)]
    return actions, [sum(a - 1 for a in actions) % cycle_length]


# ---- deterministic context-free
def _mab_expression(rng, modulus, length, mult):
    """tasks/dcf/modular_arithmetic_brackets.py generate_one_expression_and_result"""
    def gen_terminal():
        terminal = rng.randrange(0, modulus)
        return str(terminal), terminal
    if length < 1:
        raise ValueError("length < 1")
    if length == 1:
        return gen_terminal()
    if length == 2:
        s, v = gen_terminal()
        return f'-{s}', -v % modulus
    if length == 3:
        s, v = gen_terminal()
        return f'({s})', v % modulus
    if length == 4:
        s, v = gen_terminal()
        return f'(-{s})', -v % modulus
    left_length = rng.randrange(1, length - 3)
    right_length = length - (left_length + 3)
    ls, lv = _mab_expression(rng, modulus, left_length, mult)
    rs, rv = _mab_expression(rng, modulus, right_length, mult)
    maxop = 3 if mult else 2
    op = rng.randrange(0, maxop)
    if op == 0:
        return '(' + ls + '+' + rs + ')', (lv + rv) % modulus
    if op == 1:
        return '(' + ls + '-' + rs + ')', (lv - rv) % modulus
    return '(' + ls + '*' + rs + ')', (lv * rv) % modulus


def modular_arithmetic_brackets(length, rng, modulus=5, mult=True):
    """ModularArithmeticBrackets(mult=True) (constants.py); input: characters of the expression"""
    s, v = _mab_expression(rng, modulus, length, mult)
    return list(s), [v]


def reverse_string(length, rng):
    """tasks/dcf/reverse_string.py (DuplicateString's sampling, vocab 2): output = reversed input"""
    s = _bits(length, rng)
    return s, s[::-1]


def solve_equation(length, rng, modulus=5):
    """tasks/dcf/solve_equation.py; length < 3: input zeros, class 0 (SolveEquation.sample_batch)"""
    if length < 3:
        return [0] * length, [0]
    expr, val = _mab_expression(rng, modulus, length - 2, mult=False)
    idx = rng.randrange(0, len(expr))
    digits = [str(n) for n in range(modulus)]
    while expr[idx] not in digits:
        idx = (idx + 1) % (length - 2)
    solution = int(expr[idx])
    equation = f'{expr[:idx]}x{expr[idx + 1:]}={val}'
    return list(equation), [solution]


def stack_manipulation(length, rng):
    """tasks/dcf/stack_manipulation.py: input = stack (0/1, bottom to top) then actions 2 POP / 3 PUSH 0 / 4 PUSH 1;
    output = final stack top to bottom, then the termination token 2, then 0s up to length + 1"""
    if length == 1:
        value = [rng.randrange(0, 2)]
        expression, result = value, list(value)
    else:
        stack_length = rng.randrange(1, length)
        stack = [rng.randrange(0, 2) for _ in range(stack_length)]
        actions = [rng.randrange(2, 5) for _ in range(length - stack_length)]
        cur = list(stack)
        for a in actions:
            if a == 2:
                if cur:
                    cur.pop()
            elif a in (3, 4):
                cur.append(a - 3)
        expression, result = stack + actions, cur[::-1]
    result = result + [2]
    result = result + [0] * (length + 1 - len(result))
    return expression, result


# ---- context-sensitive
def _variable_length_binary(numbers, lengths, little_endian=True):
    """tasks/cs/binary_addition.py numbers_to_variable_length_binary"""
    out = [f'{num:b}'.zfill(ln) for num, ln in zip(numbers, lengths)]
    if little_endian:
        out = [b[::-1] for b in out]
    return [list(map(int, b)) for b in out]


def _fixed_length_binary(numbers, length, little_endian=True):
    return _variable_length_binary(numbers, [length] * len(numbers), little_endian)


def binary_addition(length, rng):
    """tasks/cs/binary_addition.py: input n + m (little endian, '+' = 2); output = sum (little endian, no leading
    zeros), the termination token 2, then 0s up to length + 1"""
    if length <= 2:
        number = rng.randrange(0, 2 ** length - 1)
        expression = _fixed_length_binary([number], length)[0]
        result = _fixed_length_binary([number], 0)[0]
    else:
        length_n = rng.randrange(1, length - 1)
        length_m = length - 1 - length_n
        integer_n = rng.randint(1, 2 ** length_n - 1)
        integer_m = rng.randint(1, 2 ** length_m - 1)
        bn = _variable_length_binary([integer_n], [length_n])[0]
        bm = _variable_length_binary([integer_m], [length_m])[0]
        expression = bn + [2] + bm
        result = _fixed_length_binary([integer_n + integer_m], 0)[0]
    return expression, result + [2] + [0] * (length - len(result))


def binary_multiplication(length, rng):
    """tasks/cs/binary_multiplication.py: input n * m ('*' = 2); output = product (little endian, no leading zeros),
    termination token 2, 0s up to length; length <= 2: the result is set to [] (length 1) or [0] (length 2)"""
    if length <= 2:
        number = rng.randrange(0, 2 ** length - 1)
        expression = _fixed_length_binary([number], length)[0]
        result = [0] * (length - 1)
    else:
        length_n = rng.randrange(1, length - 1)
        length_m = length - 1 - length_n
        integer_n = rng.randint(1, 2 ** length_n - 1)
        integer_m = rng.randint(1, 2 ** length_m - 1)
        bn = _variable_length_binary([integer_n], [length_n])[0]
        bm = _variable_length_binary([integer_m], [length_m])[0]
        expression = bn + [2] + bm
        result = _fixed_length_binary([integer_n * integer_m], 0)[0]
    return expression, result + [2] + [0] * (length - 1 - len(result))


def compute_sqrt(length, rng):
    """tasks/cs/compute_sqrt.py: input big endian, output floor(sqrt) big endian, fixed length ceil(length / 2)"""
    number = rng.randint(1, 2 ** length - 1)
    x = _fixed_length_binary([number], length, little_endian=False)[0]
    y = _fixed_length_binary([math.isqrt(number)], math.ceil(length / 2), little_endian=False)[0]
    return x, y


def duplicate_string(length, rng):
    """tasks/cs/duplicate_string.py (vocab 2): output = s s"""
    s = _bits(length, rng)
    return s, s + s


def missing_duplicate_string(length, rng):
    """tasks/cs/missing_duplicate_string.py: s s (|s| = length // 2) with one position replaced by 2, padded with 3
    when length is odd; class = the replaced value.  length 1: input [1], class 1"""
    if length == 1:
        return [1], [1]
    s = [rng.randrange(0, 2) for _ in range(length // 2)]
    d = s + s
    index = rng.randrange(0, len(d))
    out = d[index]
    d[index] = 2
    return d + [3] * (length % 2), [out]


def odds_first(length, rng):
    """tasks/cs/odds_first.py (vocab 2): output = s[1::2] + s[::2]"""
    s = _bits(length, rng)
    return s, s[1::2] + s[::2]


def bucket_sort(length, rng, vocab_size=5):
    """tasks/cs/bucket_sort.py (vocab 5): output = sorted input"""
    s = _bits(length, rng, vocab_size)
    return s, sorted(s)


GEN = {"modular_arithmetic": modular_arithmetic, "parity_check": parity_check, "even_pairs": even_pairs,
       "cycle_navigation": cycle_navigation, "modular_arithmetic_brackets": modular_arithmetic_brackets,
       "reverse_string": reverse_string, "solve_equation": solve_equation, "stack_manipulation": stack_manipulation,
       "binary_addition": binary_addition, "binary_multiplication": binary_multiplication,
       "compute_sqrt": compute_sqrt, "duplicate_string": duplicate_string,
       "missing_duplicate_string": missing_duplicate_string, "odds_first": odds_first, "bucket_sort": bucket_sort}
assert set(GEN) == set(SUITE)


# ============================================================== 2. format (9.1)
PENDING = "PENDING"
NEW_TOKENS = ["<missing>", "<empty>", "<pop>", "<push0>", "<push1>", "(", ")", "x", "<eq_in>"]


def _digit(v):
    return (str(v), "digit")


# SYMBOLS[task] = {"input": {benchmark symbol: (token, kind)}, "output": {benchmark symbol: token},
#                  "output_rule": text, "pending": [question ids]}
BIN_IN = {0: _digit(0), 1: _digit(1)}
BIN_OUT = {0: "0", 1: "1"}
M5_IN = {v: _digit(v) for v in range(5)}
M5_OUT = {v: str(v) for v in range(5)}
SYMBOLS = {
    "parity_check": {"input": BIN_IN, "output": BIN_OUT, "output_rule": "class token", "pending": []},
    "even_pairs": {"input": BIN_IN, "output": BIN_OUT, "output_rule": "class token", "pending": []},
    "modular_arithmetic": {"input": M5_IN | {5: ("+", "op"), 6: ("-", "op"), 7: ("*", "op")},
                           "output": M5_OUT, "output_rule": "class token", "pending": []},
    "cycle_navigation": {"input": {0: _digit(0), 1: _digit(1), 2: _digit(2)},
                         "output": M5_OUT, "output_rule": "class token", "pending": []},
    "modular_arithmetic_brackets": {"input": dict({str(v): _digit(v) for v in range(5)},
                                                  **{"+": ("+", "op"), "-": ("-", "op"), "*": ("*", "op"),
                                                     "(": ("(", "op"), ")": (")", "op")}),
                                    "output": M5_OUT, "output_rule": "class token", "pending": []},
    "reverse_string": {"input": BIN_IN, "output": BIN_OUT, "output_rule": "sequence", "pending": []},
    "solve_equation": {"input": {str(v): _digit(v) for v in range(5)} | {0: _digit(0)}
                                 | {"+": ("+", "op"), "-": ("-", "op"), "(": ("(", "op"),
                                    ")": (")", "op"), "x": ("x", "op"), "=": ("<eq_in>", "op")},
                       "output": M5_OUT, "output_rule": "class token", "pending": []},
    "stack_manipulation": {"input": {0: _digit(0), 1: _digit(1), 2: ("<pop>", "op"), 3: ("<push0>", "op"),
                                     4: ("<push1>", "op")},
                           "output": BIN_OUT, "output_rule": "terminated", "pending": []},
    "binary_addition": {"input": {0: _digit(0), 1: _digit(1), 2: ("+", "op")}, "output": BIN_OUT,
                        "output_rule": "terminated", "pending": []},
    "binary_multiplication": {"input": {0: _digit(0), 1: _digit(1), 2: ("*", "op")}, "output": BIN_OUT,
                              "output_rule": "terminated", "pending": []},
    "compute_sqrt": {"input": BIN_IN, "output": BIN_OUT, "output_rule": "sequence", "pending": []},
    "duplicate_string": {"input": BIN_IN, "output": BIN_OUT, "output_rule": "sequence", "pending": []},
    "missing_duplicate_string": {"input": {0: _digit(0), 1: _digit(1), 2: ("<missing>", "other"),
                                           3: ("<empty>", "other")},
                                 "output": BIN_OUT, "output_rule": "class token", "pending": []},
    "odds_first": {"input": BIN_IN, "output": BIN_OUT, "output_rule": "sequence", "pending": []},
    "bucket_sort": {"input": M5_IN, "output": M5_OUT, "output_rule": "sequence", "pending": []},
}
assert set(SYMBOLS) == set(SUITE)
# QUESTIONS: the 3-E0 format questions; answered 2026-11-26 (DESIGN 10.1-1): Q1 one op kind (the L1 '+' kind, a PF
# separator, as G-0), Q2 digit, Q3 op ("an input symbol that is neither data nor the separator -> op"), Q4 termination
# -> <eos>, padding dropped.  Kept for the record.
ANSWERS = {"Q1": "one op kind", "Q2": "digit", "Q3": "op", "Q4": "termination -> <eos>, padding dropped"}
QUESTIONS = {
    "Q1": "op kind: one 'op' kind for every operation / command symbol (the L1 kind '+', a PF separator, as G-0's "
          "'-', '*', '^'), or a separate kind per symbol (more than the 7 kinds of DESIGN 3)?",
    "Q2": "cycle_navigation actions 0/1/2 (stay/right/left in the docstring): data symbols (digit) or command "
          "symbols (op)?",
    "Q3": "'(' ')' (brackets), 'x' (the unknown) and the '=' inside a solve_equation input: op or other?  (The "
          "inner '=' cannot be the separator token: answer_phase starts at the first '='.)",
    "Q4": "termination token 2 and the 0 padding after it (binary_addition, binary_multiplication, "
          "stack_manipulation; the benchmark masks everything after the termination token): termination -> <eos> "
          "and padding dropped, or the whole padded output before <eos>?",
}


def encode_symbols(task, inp, out):
    """benchmark (input, output) -> (prompt tokens, answer tokens) without <eos> (tasks.encode adds it)"""
    sy = SYMBOLS[task]
    if sy["pending"]:
        raise ValueError("%s: format pending design-chat answer(s) %s" % (task, sy["pending"]))
    prompt = ["<bos>"] + [sy["input"][v][0] for v in inp] + ["="]
    if sy["output_rule"] == "terminated":                  # 10.1-1 Q4: termination token 2 -> <eos>, padding dropped
        out = out[:out.index(2)]
    answer = [sy["output"][v] for v in out]
    return prompt, answer


def kind_of_token(task):
    """{token: kind} of the task's input symbols (+ the format tokens)"""
    out = {"<bos>": "other", "=": "="}
    for tok, kd in SYMBOLS[task]["input"].values():
        out[tok] = kd
    return out


def draw(task, rng, lo, hi, train_dist=False):
    """one example (prompt, answer, n): n = rng.randint(lo, hi) then the generator (l_tasks.draw convention)"""
    n = rng.randint(lo, hi)
    inp, out = GEN[task](n, rng)
    p, a = encode_symbols(task, inp, out)
    return p, a, n


def raw_draw(task, rng, lo, hi):
    """benchmark-encoded example (input, output, n) with the same draws as draw (no format)"""
    n = rng.randint(lo, hi)
    inp, out = GEN[task](n, rng)
    return inp, out, n
