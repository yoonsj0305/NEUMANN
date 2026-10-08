# Strong analytic controls for opened probabilistic goals

**ENGINEERING PASS; PERFORMANCE NOT MEASURED; HOLD_LEARNING.** These five
source-bound outputs from four families are classical mathematical controls,
not a learned generator, new benchmark or proof of NEUMANN cost advantage.
The registered 125-job Storm diagnostic and all its failures remain unchanged.

`experiments/probabilistic_analytic_controls.py` uses exact rational arithmetic,
the pinned public original program/property bytes, an explicit goal and validated
parameters. A source, property, goal or parameter mutation is refused. Caller
verdicts cannot authorize a control. Original reference answers are not a function
input. Property comments are hashed for byte binding, never parsed as answers.

## Coupon: batches, not collecting each coupon twice

The pinned PGCL draws two independent uniform coupons with replacement per loop,
sets any drawn coupon's flag, and increments `numberDraws` once per batch. The
opened reward is expected batches until all five flags are true. For n coupons
and d draws per batch, the tail-sum identity and inclusion-exclusion give

    E[T] = sum(k=1..n) (-1)^(k+1) binom(n,k) /
                         (1 - ((n-k)/n)^d).

This follows by summing the probability that at least one coupon is still absent
after t batches, t>=0. It is not the double-Dixie-cup problem. A separate count-
state recurrence tracks k collected coupons, uses exact occupancy probabilities,
and solves its self-loop. Both produce **751/126** for the original n5/d2 source.
32 small arithmetic fixtures agree; they are not 32 independent research tasks.
The bound parameter B affects another property, not this expected reward.

The original model cites [Jansen et al., ATVA2016](https://arxiv.org/abs/1605.04477).
The formula here is an elementary derivation from that source's loop; it is not
claimed to be a quoted result or a new NEUMANN invention.

## EGL: retain only the choices affecting who learns a pair first

In phase1, each party independently obtains one secret of every pair with
probability1/2. No pair is yet fully known. Before the final bit round of phase2,
an initially unknown first-half secret has fewer than L bits, so neither party
knows a full pair. At that final round, the counter schedule is:

    A sends secret0 -> B sends all first-half secrets ->
    A sends remaining first-half secrets.

If B initially has second-half secret0, A's first transmission completes B's pair
before A can complete any pair. This event has probability1/2. Otherwise, A
becomes first during B's transmissions unless A initially holds every first-half
secret, an independent event of probability2^-N. If A holds them all, B becomes
first during A's remaining transmissions; if B also holds them all, B becomes
first at A's secret0 transmission in phase3. Thus

    P(F !knowA & knowB) = 1/2 + 2^-(N+1).

For N5/L2 this gives **33/64**. Positive L changes the number of bit transmissions
but not this ordering argument. The source schedule requires N>=2 and explicitly
supports N<=20; the control refuses other N. Source comments suggesting richer
nondeterminism are not used as semantics: the actual pinned model is a DTMC with
the displayed commands. Other fairness/reward goals are not authorized.

The protocol and related PRISM models are described in the primary
[PRISM overview](https://prismmodelchecker.org/papers/sfm07.pdf). The exact argument
above is our source-level review, not a machine-checked theorem or a claim that
all EGL variants share this probability.

## Crowds: remove unrelated observation counters

The pinned source resets path state between runs, starts `lastSeen=0`, selects
a bad router with beta=91/1000, and forwards a good router's message with
f=4/5. After a good router, `lastSeen` is uniform over H honest routers. Subsequent
good-and-forward loops give a geometric series. One run observes sender0 with

    p = beta + (1-beta)*f*beta / (H*(1-(1-beta)*f)).

Each run terminates almost surely because continuation probability is below1.
It yields at most one observation. Previous counters do not change router
probabilities. Their saturation guards cannot block a run: after j completed
runs, no counter exceeds j, so it is still below TotalRuns before another
observation. Path resets therefore make these Bernoulli trials independent.
The monotone goal `F observe0>1` is exactly the final count being at least2:

    P = 1-(1-p)^R-R*p*(1-p)^(R-1).

Alternatively, keep only count0/count1/count>=2 and propagate R trials. Both
exact formulations agree. For the two original R3 requests the outputs are
**16406726260175797/309779851562500000** (H5) and
**729411335557151611/19825910500000000000** (H10), matching retained exact Storm
outputs. Decimal `//RESULT` comments in the public property file are old numeric
approximations; they are not the authority for exact rational equality.

The original model and its Positive goal are documented by
[PRISM Crowds case study](https://www.prismmodelchecker.org/casestudies/crowds.php).
Our control derives the displayed fixed source, not every Crowds protocol or
the distinct false-positive/confidence goals. 36 arithmetic recurrence checks
are fixtures, not fresh public problems. Runtime binding admits only the two
already opened R3/H5 or H10 requests.

## Herman15: use the existing exact maximum theorem

[Bruna et al., ICALP2016](https://doi.org/10.4230/LIPIcs.ICALP.2016.104) bound expected
synchronous stabilization by4N^2/27. For odd N divisible by3, three equally spaced
tokens attain it. The pinned N15 model's `init true` includes those states, so
the original maximum reward is exactly **100/3**.

The paper keeps a bit when it differs from its predecessor; the source copies
the predecessor. Globally complementing the paper's next bit vector gives the
source's law: unequal deterministic bits flip and independent fair coins remain
fair. Adjacent equality and the token process are complement invariant. For odd
N, the equality-token count is odd; N15's three equally spaced tokens are
representable because its other12 inequality edges admit a consistent ring.
This binds the published token theorem to the actual synchronous fair-bit source.

N7 is refused:4N^2/27 is a bound there, not the exact requested maximum48/7.
A source probability or transition change invalidates this argument and fails
the hash check. No new full-state model checker or generic proof engine is built.

## Trust, economics and next decision

Trust consists of the published Herman theorem, manually inspected program
semantics, exact Fraction arithmetic, and the source hash binding. No formal
machine proof of these source abstractions was executed. Exact arithmetic and
agreement with retained Native outputs are engineering evidence; they do not
replace that missing formal proof or establish independent generalization.

Coupon and EGL were the first screen's strongest singleton optimistic warm
floors (22.55x and53.09x against its Storm portfolio). Crowds large showed16.21x,
but its registered two-size geometric mean was9.678x and failed the10x criterion.
All three have simpler applicable classical goal-specific methods. Herman15's
Storm timeouts likewise do not establish a native capability gap.
Operational timing of these analytic controls, full source-proof acquisition,
energy, memory and lifecycle costs have **not** been measured. Therefore this
report does not numerically replace any first ratio or claim a new no-headroom
theorem. It removes Storm-only gaps as sufficient grounds for learning admission.

10 engineering tests passed in0.023s: exact arithmetic, original outputs,
transition/goal/property/parameter mutations, rejected N7 bound, and caller
verdict rejection. Test suite wall time is not a performance benchmark. First
7-test code/receipt are retained separately, followed by the hardening and
Crowds contract. No GPU, new solver or model forward was used. **No G1/G2.**

Pinned QVBS source: [c7324a3 DTMC benchmarks](https://github.com/ahartmanns/qcomp/tree/c7324a311475ba1a3f40e36a324e32f91e766540/benchmarks/dtmc).
Portable original fixtures and negative tests are in
`tests/fixtures/probabilistic_native_controls` and
`tests/test_probabilistic_analytic_controls.py`. The four original source-pair
hashes are explicit in `SOURCE_PINS`; no original evidence was modified.
