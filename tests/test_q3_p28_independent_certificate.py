import copy
import unittest
from experiments.q3_p28_verify_certificate import verify_certificate


def factored(x):
    h, w = len(x), len(x[0])
    return [[(x[i//h][j//w] != 0) * x[i%h][j%w] for j in range(w*w)]
            for i in range(h*h)]


class TestVerifier(unittest.TestCase):
    def setUp(self):
        a = [[0,2],[2,0]]
        b = [[0,4],[4,4]]
        self.cert = {
            'schema':'neumann.q3.p28.proof-certificate.v1',
            'ast':{'kind':'factorized-zero-conditional','selector':['inner','inner','outer','inner']},
            'train':[{'input':a,'output':factored(a)}],
            'test_inputs':[b], 'predicted_test':[factored(b)]
        }

    def test_correct_certificate(self):
        self.assertEqual(verify_certificate(self.cert)['status'],'EXECUTION_PROOF_PASS')

    def test_tampered_test_pred_rejected(self):
        c=copy.deepcopy(self.cert);c['predicted_test'][0][0][0]=9
        with self.assertRaises(ValueError):verify_certificate(c)

    def test_tampered_train_output_rejected(self):
        c=copy.deepcopy(self.cert);c['train'][0]['output'][0][0]=9
        with self.assertRaises(ValueError):verify_certificate(c)

    def test_invalid_ast_rejected(self):
        c=copy.deepcopy(self.cert);c['ast']['selector'][0]='eval'
        with self.assertRaises(ValueError):verify_certificate(c)

    def test_extra_fields_rejected(self):
        c=copy.deepcopy(self.cert);c['test_gold']=[[]]
        with self.assertRaises(ValueError):verify_certificate(c)

    def test_boolean_cell_rejected(self):
        c=copy.deepcopy(self.cert);c['train'][0]['input'][0][0]=False
        with self.assertRaises(ValueError):verify_certificate(c)

    def test_bad_cardinality_rejected(self):
        c=copy.deepcopy(self.cert);c['predicted_test']=[]
        with self.assertRaises(ValueError):verify_certificate(c)


if __name__ == '__main__':unittest.main()
