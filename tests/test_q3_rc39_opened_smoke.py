"""Opened smoke only: not the 24 sealed first experimental tasks."""
import itertools
import unittest
from research.q3.rc39.active_mealy import ActiveMealyLearner,MealyProgram,UnknownStateStructure

def baseline_oracle(alphabet, reference):
    def member(w):return reference(w)
    def eq(model):
        for k in range(9):
            for v in itertools.product(alphabet,repeat=k):
                s=''.join(v)
                if model.run(s)!=reference(s):
                    return s
        return None
    return member,eq

class OpenedSmoke(unittest.TestCase):
    def test_one_state_constant_emitter(self):
        learner=ActiveMealyLearner('AB','01')
        member,eq=baseline_oracle('AB',lambda w:'1'*len(w))
        r=learner.learn(member,eq)
        self.assertEqual(r.status,'SCOPED_ALL_LENGTHS_PROVED')
        self.assertEqual(r.hypothesis_states,1)
        p=MealyProgram.from_source(r.source)
        self.assertEqual(p.run('BAABA'),'11111')

    def test_two_state_toggle_on_B_and_source_replay(self):
        def ref(w):
            state=0
            y=[]
            for x in w:
                if x=='B':state^=1
                y.append(str(state))
            return ''.join(y)
        learner=ActiveMealyLearner('AB','01')
        member,eq=baseline_oracle('AB',ref)
        r=learner.learn(member,eq)
        self.assertEqual(r.status,'SCOPED_ALL_LENGTHS_PROVED',str(r))
        self.assertEqual(r.hypothesis_states,2)
        self.assertEqual(MealyProgram.from_source(r.source).run('ABBABB'),ref('ABBABB'))

    def test_fail_closed_budget_and_tamper(self):
        r=ActiveMealyLearner('AB','01',max_membership=1).learn(
            lambda w:'0'*len(w),lambda _:None)
        self.assertTrue(r.status.startswith('UNKNOWN:'))
        self.assertIsNone(r.source)
        x={'schema':'neumann.rc39.mealy-ast.v1','alphabet':['A'],'outputs':['0'],
           'initial':0,'states':1,'transitions':[[19]],'emissions':[['0']]}
        with self.assertRaises(UnknownStateStructure):MealyProgram.from_source(x)
        with self.assertRaises(UnknownStateStructure):MealyProgram.from_source({'x':'eval()'})
if __name__=='__main__':unittest.main()
