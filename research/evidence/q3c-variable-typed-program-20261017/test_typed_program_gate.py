import importlib.util
import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('fgsr_q3c',ROOT/'typed_program_gate.py')
q=importlib.util.module_from_spec(spec)
spec.loader.exec_module(q)

class TypedProgramBoundary(unittest.TestCase):
    def test_variable_relation_count(self):
        for n in (1,2,6,7,15):
            schema={f'R{i}':(['Int','Bool'] if i%2 else ['~Mut<Int>']) for i in range(n)}
            candidate={'relations':{k:{'op':'bool','value':True} for k in schema}}
            self.assertEqual(len(q.compile_program(candidate,schema)),n)
    def test_type_checked_mutable_int_selector(self):
        expression={'op':'eq','args':[
            {'op':'selector','name':'~cur<Int>','arg':{'op':'arg','index':0}},
            {'op':'int','value':0}]}
        self.assertEqual(q.compile_ast(expression,['~Mut<Int>'],[0])[1],'Bool')
        with self.assertRaises(q.Reject):
            q.compile_ast(expression,['Bool'],[0])
    def test_missing_relation_denied(self):
        with self.assertRaises(q.Reject):
            q.compile_program({'relations':{'A':{'op':'bool','value':True}}},
                              {'A':['Int'],'B':['Bool']})
    def test_model_cannot_inject_raw_smt(self):
        with self.assertRaises(q.Reject):
            q.compile_ast({'op':'raw','formula':'(assert true)'},['Int'],[0])
    def test_an_original_source_can_be_parsed(self):
        data=b'(set-logic HORN)\n(declare-fun A (Int Bool) Bool)\n(assert (forall ((x Int)(b Bool)) (=> (= x 0) (A x b))))\n(check-sat)'
        _,relations,clauses=q.read_source(data)
        self.assertEqual(relations,{'A':['Int','Bool']})
        self.assertEqual(len(clauses),1)

if __name__=='__main__':unittest.main()
