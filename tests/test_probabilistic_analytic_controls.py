"""Goal/source mutations and exact native arithmetic, not performance evidence."""
from pathlib import Path
import unittest
from experiments import probabilistic_analytic_controls as c

BASE=Path(__file__).resolve().parent/'fixtures/probabilistic_native_controls'


class AnalyticNativeTests(unittest.TestCase):
    def bundle(self,kind):
        names={'coupon':('coupon','coupon.5-2.pgcl','coupon.props'),
               'egl':('egl','egl.prism','egl.props'),
               'herman15':('herman','herman.15.prism','herman.props'),
               'crowds':('crowds','crowds.prism','crowds.props')}
        family,model,props=names[kind]
        return (BASE/family/model).read_bytes(),(BASE/family/props).read_bytes()

    def test_two_exact_coupon_methods(self):
        # Arithmetic identities are fixtures, not new independent benchmark tasks.
        for n in range(1,9):
            for draws in range(1,5):
                self.assertEqual(c.coupon_batches(n,draws),c.coupon_occupancy(n,draws))

    def test_original_opened_goals(self):
        for kind,params,expected in [('coupon',{'B':5},'751/126'),
                                     ('egl',{'N':5,'L':2},'33/64'),
                                     ('herman15',{},'100/3')]:
            result=c.bound_native_control(kind,*self.bundle(kind),goal=c.GOALS[kind],parameters=params)
            self.assertEqual(result['output'],expected)
            self.assertFalse(result['learned_discovery'])
            self.assertEqual(result['performance'],'NOT_MEASURED')

    def test_original_transition_mutation_refused(self):
        model,props=self.bundle('egl')
        with self.assertRaises(ValueError):
            c.bound_native_control('egl',model.replace(b'0.5',b'0.4',1),props,goal='unfairA',parameters={'N':5,'L':2})

    def test_original_goal_and_property_mutation_refused(self):
        model,props=self.bundle('coupon')
        with self.assertRaises(ValueError):
            c.bound_native_control('coupon',model,props,goal='collect_all',parameters={'B':5})
        with self.assertRaises(ValueError):
            c.bound_native_control('coupon',model,props.replace(b'numberDraws',b'wrongReward'),goal='exp_draws',parameters={'B':5})

    def test_unknown_or_extra_parameters_refused(self):
        model,props=self.bundle('egl')
        for params in [{'N':1,'L':2},{'N':21,'L':2},{'N':5.0,'L':2},{'N':5,'L':0},{'N':5,'L':2,'accepted':True}]:
            with self.assertRaises(ValueError):
                c.bound_native_control('egl',model,props,goal='unfairA',parameters=params)

    def test_bound_is_not_exact_for_herman7(self):
        with self.assertRaises(ValueError): c.herman_max(7)
        model=(BASE/'herman/herman.7.prism').read_bytes()
        _,props=self.bundle('herman15')
        with self.assertRaises(ValueError): c.bound_native_control('herman15',model,props,goal='steps',parameters={})

    def test_caller_verdict_is_not_an_argument(self):
        with self.assertRaises(TypeError):
            c.bound_native_control('herman15',*self.bundle('herman15'),goal='steps',parameters={},accepted=True)

    def test_coupon_parameter_type_is_bound(self):
        for params in [{'B':5.0},{'B':True},[('B',5)]]:
            with self.assertRaises(ValueError):
                c.bound_native_control('coupon',*self.bundle('coupon'),goal='exp_draws',parameters=params)

    def test_original_crowds_requests_and_counter_sufficiency(self):
        for size,expected in [(5,'16406726260175797/309779851562500000'),
                              (10,'729411335557151611/19825910500000000000')]:
            result=c.bound_native_control('crowds',*self.bundle('crowds'),goal='positive',
                                         parameters={'TotalRuns':3,'CrowdSize':size})
            self.assertEqual(result['output'],expected)
        for runs in range(1,7):
            for size in (2,4,5,10,15,20):
                self.assertEqual(c.crowds_positive(runs,size),c.crowds_count_state(runs,size))

    def test_crowds_probabilities_goal_and_parameter_mutations_refused(self):
        model,props=self.bundle('crowds')
        with self.assertRaises(ValueError):
            c.bound_native_control('crowds',model.replace(b'0.8',b'0.7',1),props,
                                   goal='positive',parameters={'TotalRuns':3,'CrowdSize':5})
        with self.assertRaises(ValueError):
            c.bound_native_control('crowds',model,props,goal='false_positive',
                                   parameters={'TotalRuns':3,'CrowdSize':5})
        for params in [{'TotalRuns':3.0,'CrowdSize':5},{'TotalRuns':3,'CrowdSize':15},
                       {'TotalRuns':4,'CrowdSize':5},{'TotalRuns':3,'CrowdSize':3}]:
            with self.assertRaises(ValueError):
                c.bound_native_control('crowds',model,props,goal='positive',parameters=params)


if __name__=='__main__':unittest.main()
