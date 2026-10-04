"""New authored opened tasks, fixed before any validation scores.

Literal answers/tests are source-construction records, never model views.
All twelve are retained; no score-informed selection or regeneration.
"""
from neumann1.control_plane_v1 import snapshot


def catalog():
    rows = []; references = []
    def add(view, family, private, witness, kind, route):
        task_id = 'p12v_%02d' % (len(rows)+1)
        rows.append({'task_id':task_id, 'view':view})
        references.append({'task_id':task_id, 'family':family, 'private':private,
                           'witness':witness, 'semantic_kind':kind, 'compatible_route':route})
    math = [
        ('((x-y)/(z+u))*v', {'x':31,'y':7,'z':5,'u':3,'v':2,'extra':81}, '6', 'nested_divide_then_multiply'),
        ('-(a/(b-c))+d/e', {'a':17,'b':11,'c':5,'d':7,'e':9,'extra':-31}, '-37/18', 'unary_rational_sum'),
        ('(a+b)*(c-d)/(e*f)', {'a':4,'b':9,'c':15,'d':6,'e':7,'f':5,'extra':10}, '117/35', 'product_of_two_sums'),
        ('(a/(b+c)-d)/e', {'a':23,'b':4,'c':5,'d':2,'e':7,'extra':35}, '5/63', 'nested_rational_difference')]
    for expression, bindings, exact, kind in math:
        add({'instruction':'Return the exact rational value.', 'public':{
            'expression':expression, 'bindings':bindings, 'background':'The worksheet has a silver border.'}},
            'math_logic', {'exact':exact}, exact, kind, 'ARITHMETIC')
    code = [
        ('Return the list of inclusive prefix sums of items, a list of integers. Empty input returns an empty list.',
         'def solve(items):\n    result = []\n    total = 0\n    for value in items:\n        total += value\n        result = result + [total]\n    return result\n',
         [([],[]),([3,-5,2],[3,-2,0]),([0,0],[0,0]),([-1],[-1]),([2,2,2],[2,4,6])], 'prefix_sums'),
        ('Run-length encode consecutive equal integers in items. Return a list of [value, count] pairs in encounter order; empty input returns [].',
         'def solve(items):\n    result = []\n    for value in items:\n        if len(result) == 0 or result[-1][0] != value:\n            result = result + [[value, 1]]\n        else:\n            result[-1][1] += 1\n    return result\n',
         [([],[]),([2,2,-1,-1,-1,2],[[2,2],[-1,3],[2,1]]),([0],[[0,1]]),([1,2,1],[[1,1],[2,1],[1,1]]),([-3,-3],[[-3,2]])], 'consecutive_run_encoding'),
        ('Return the length of the longest strictly increasing contiguous run in items, a list of integers. Return 0 for empty input; equal adjacent values break a run.',
         'def solve(items):\n    best = 0\n    current = 0\n    for i in range(len(items)):\n        if i > 0 and items[i] > items[i-1]:\n            current += 1\n        else:\n            current = 1\n        best = max(best, current)\n    return best\n',
         [([],0),([1,2,2,3,4],3),([5,4,3],1),([-3,-2,-1,0],4),([7],1)], 'longest_increasing_contiguous_run'),
        ('Count unordered index pairs i < j in items whose two integer values sum to zero. Repeated values occupy different indices and each index pair counts separately.',
         'def solve(items):\n    count = 0\n    for i in range(len(items)):\n        for j in range(i+1, len(items)):\n            if items[i] + items[j] == 0:\n                count += 1\n    return count\n',
         [([],0),([1,-1,1,-1,0,0],5),([0,0,0],3),([2,-2,-2],2),([1,2,3],0)], 'zero_sum_index_pairs')]
    for requirement, source, tests, kind in code:
        private = {'tests':[{'input':i,'output':o} for i,o in tests]}
        add({'instruction':'Return Python source defining solve(items).', 'public':{
            'requirement':requirement,'examples':[private['tests'][1]], 'background':'The specification is stored in a beige folder.'}},
            'coding', private, source, kind, 'PYTHON')
    plans = [
        ({'A':[0,1,2],'B':[0,1,2],'C':[0,1,2],'D':[0,1,2]},
         [['ne','A','B'],['ne','B','C'],['ne','A','C'],['eq','D','A']],
         {'A':0,'B':1,'C':2,'D':0}, 'triangle_coloring_with_alias'),
        ({n:[1,2,3,4] for n in 'ABCD'},
         [['ne','A','B'],['ne','A','C'],['ne','A','D'],['ne','B','C'],['ne','B','D'],['ne','C','D'],
          ['ne','A',1],['ne','B',2],['ne','C',3],['ne','D',4]],
         {'A':2,'B':1,'C':4,'D':3}, 'finite_derangement'),
        ({'P':[-3,0,2],'Q':[-1,1,4],'R':[0,3,5],'S':[-2,2,6]},
         [['lt','P','Q'],['lt','Q','R'],['ne','S','P'],['le','S','R'],['ne','Q',1],['eq','R',5]],
         {'P':0,'Q':4,'R':5,'S':2}, 'nonuniform_domains_with_constants'),
        ({n:[0,1] for n in 'ABCD'},
         [['ne','A','B'],['ne','B','C'],['ne','C','D'],['ne','D','A'],['eq','A',0]],
         {'A':0,'B':1,'C':0,'D':1}, 'anchored_even_cycle')]
    for domains, constraints, witness, kind in plans:
        add({'instruction':'Return a complete assignment meeting every original constraint.', 'public':{
            'domains':domains,'constraints':constraints,'background':'A spare pen lies beside the worksheet.'}},
            'constraint_planning', {}, witness, kind, 'CSP')
    return snapshot(rows), snapshot(references)
