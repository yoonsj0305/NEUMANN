"""Exact classical mathematics for five opened native comparison requests.

No learned discovery or generic probabilistic compiler. Source hashes bind the
manually reviewed original programs and their property files; altered programs
are refused. Published/manual proof trust is explicit, not a machine certificate.
"""
from fractions import Fraction
import hashlib
from math import comb
import re

SOURCE_PINS = {
    'coupon': ('56d8de789ad24225669923c5ef53cb1d04d0b74f0a949092d08956cda3726a63',
               '4fa808e94c0445abcd17b78c04829ef49df0b76ad0a2ca18923fceaaa8ab492d'),
    'egl': ('e5ff82590b1efa8bc76eec1f23e339f003f5f9f941ffa5a25f6100dfa7e876ba',
            '5777860ab98f29a7281b6d772a4855423f0893917c7daf555ffe7804bc72c9e1'),
    'herman15': ('ddbc749ed67c7869e5eae84ac233e2e4cc3bc1eddb373634c36557c3ef6c37e0',
                '0506879a7855fae7fd02a1c24ed29e9600c9bc4eec46a489cb4f90fb1ddc1415'),
    'crowds': ('a19979fdaae425e5dbd267c71796b4374eaccea5d3496e3033fc01d165796e97',
               '6770621b6fd686739a718e838b10d96742c597de70fc74c4329f2ee0c1fe8c59'),
}
GOALS = {'coupon':'exp_draws','egl':'unfairA','herman15':'steps','crowds':'positive'}


def positive_int(value, maximum):
    if type(value) is not int or not 1 <= value <= maximum:
        raise ValueError('Bounded positive integer required')
    return value


def coupon_batches(n, draws):
    """Tail sum + inclusion-exclusion; draws per batch are IID with replacement."""
    n=positive_int(n,64); draws=positive_int(draws,8)
    return sum(((-1)**(k+1)*comb(n,k) / (1-Fraction(n-k,n)**draws)
                for k in range(1,n+1)), Fraction(0))


def coupon_occupancy(n, draws):
    """Classic count-state dynamic program, independent arithmetic formulation."""
    n=positive_int(n,64); draws=positive_int(draws,8)
    expected=[Fraction(0)]*(n+1)
    for collected in range(n-1,-1,-1):
        probabilities=[]
        for new in range(min(draws,n-collected)+1):
            onto=sum((-1)**i*comb(new,i)*(collected+new-i)**draws for i in range(new+1))
            probabilities.append(Fraction(comb(n-collected,new)*onto,n**draws))
        if sum(probabilities)!=1 or any(p<0 for p in probabilities):
            raise ValueError('Invalid occupancy transition')
        expected[collected]=(1+sum(p*expected[collected+j] for j,p in enumerate(probabilities) if j))/(1-probabilities[0])
    return expected[0]


def egl_unfair_a(n, bits):
    n=positive_int(n,20); positive_int(bits,1_000_000)
    if n<2:
        raise ValueError('Original counter schedule requires N>=2')
    # B completes secret0 first, or A lacks every first-half secret.
    return Fraction(1,2)+Fraction(1,2**(n+1))


def herman_max(n):
    n=positive_int(n,1_000_000)
    if n%2==0 or n%3!=0:
        raise ValueError('Published bound is not an exact maximum for this N')
    return Fraction(4*n*n,27)


def crowds_single_path(crowd_size):
    crowd_size=positive_int(crowd_size,20)
    if crowd_size not in (2,4,5,10,15,20):
        raise ValueError('Original uniform branch not defined for this crowd size')
    bad=Fraction(91,1000); forward=Fraction(4,5)
    # After a good router, lastSeen is uniform. Subsequent good+forward loops
    # contribute a geometric series. At the start, lastSeen is the sender.
    uniform_success=bad/(crowd_size*(1-(1-bad)*forward))
    return bad+(1-bad)*forward*uniform_success


def crowds_positive(runs, crowd_size):
    runs=positive_int(runs,6); p=crowds_single_path(crowd_size)
    return 1-(1-p)**runs-runs*p*(1-p)**(runs-1)


def crowds_count_state(runs, crowd_size):
    runs=positive_int(runs,6); p=crowds_single_path(crowd_size)
    # Truncate the monotone count at2, preserving exactly the opened goal.
    zero,one,many=Fraction(1),Fraction(0),Fraction(0)
    for _ in range(runs):
        zero,one,many=zero*(1-p),one*(1-p)+zero*p,many+one*p
    return many


def bound_native_control(kind, model_bytes, property_bytes, *, goal, parameters):
    if type(parameters) is not dict:
        raise ValueError('Explicit original parameter dictionary required')
    if kind not in SOURCE_PINS or goal!=GOALS[kind]:
        raise ValueError('Unreviewed source or original goal')
    actual=tuple(hashlib.sha256(data).hexdigest() for data in (model_bytes,property_bytes))
    if actual!=SOURCE_PINS[kind]:
        raise ValueError('Original program/property source binding failed')
    if kind=='coupon':
        if set(parameters)!={'B'} or positive_int(parameters['B'],64)!=5:
            raise ValueError('Only the opened coupon source binding is admitted')
        clean=re.sub(r'//[^\n]*','',model_bytes.decode())
        n=len(re.findall(r'bool coup\d+\s*:=\s*false',clean))
        ranges=re.findall(r'draw\d+\s*:=\s*unif\(0,\s*(\d+)\)',clean)
        if not ranges or any(int(bound)!=n-1 for bound in ranges):
            raise ValueError('Uniform batch grammar differs')
        result=coupon_batches(n,len(ranges))
        if result!=coupon_occupancy(n,len(ranges)):
            raise ValueError('Independent count-state calculation disagrees')
    elif kind=='egl':
        if set(parameters)!={'N','L'}:
            raise ValueError('Original N/L binding required')
        result=egl_unfair_a(parameters['N'],parameters['L'])
    elif kind=='crowds':
        if set(parameters)!={'TotalRuns','CrowdSize'} or positive_int(parameters['TotalRuns'],6)!=3:
            raise ValueError('Only opened Crowds run-count binding admitted')
        size=positive_int(parameters['CrowdSize'],20)
        if size not in (5,10):
            raise ValueError('Only two opened Crowds source requests admitted')
        result=crowds_positive(parameters['TotalRuns'],size)
        if result!=crowds_count_state(parameters['TotalRuns'],size):
            raise ValueError('Independent count-state calculation disagrees')
    else:
        if parameters:
            raise ValueError('Herman source is fixed, not parameterized')
        n=max(map(int,re.findall(r'module process(\d+)',model_bytes.decode())))
        result=herman_max(n)
    return {'output':str(result),'kind':'STRONG_NATIVE_ANALYTIC_CONTROL',
            'model_sha256':actual[0],'properties_sha256':actual[1],
            'goal':goal,'parameters':parameters,
            'scope':'Published/manual source-bound derivation; original reference not an input',
            'machine_formal_proof':'NOT_EXECUTED','learned_discovery':False,
            'performance':'NOT_MEASURED','G1_admission':False}
