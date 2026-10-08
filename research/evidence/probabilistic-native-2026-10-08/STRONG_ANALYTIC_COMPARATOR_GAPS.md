# Missing strong analytic comparator — source-level finding

This review follows registration of the native CPU diagnostic. It does not
replace that first contract or its receipts. No new performance measurement or
learned inference was performed in this review.

The Herman15 request is already covered by a published exact mathematical
method. Bruna, Grigore, Kiefer, Ouaknine and Worrell's ICALP2016 theorem bounds
expected synchronous stabilization by `4*N^2/27` for every odd-token initial
configuration. For odd N divisible by3, three equally spaced tokens attain
the bound. Thus the maximum over all initial states is exactly this formula,
not an assumption based on the benchmark's reference answer.

For N15 the formula gives `100/3`. The N7 request is NOT covered by this exact
maximum formula: `4*7^2/27` is only an upper bound, while the public exact
reference is `48/7`. Do not substitute a bound for an exact goal.

## Binding to the original PRISM request

- Pinned QVBS commit: `c7324a311475ba1a3f40e36a324e32f91e766540`.
- `herman.15.prism` SHA256:
  `ddbc749ed67c7869e5eae84ac233e2e4cc3bc1eddb373634c36557c3ef6c37e0`.
- `herman.props` SHA256:
  `0506879a7855fae7fd02a1c24ed29e9600c9bc4eec46a489cb4f90fb1ddc1415`.
- Original source is a synchronous15-module DTMC, independent fair random
  bit assignments, all bit states initially allowed, reward1 per transition
  until `num_tokens=1`, and the requested filter is the maximum over `init`.

An important semantic detail needs justification. The published bit protocol
keeps a bit when it differs from its predecessor. The PRISM source instead
copies that predecessor, thereby flipping the bit. When the bits agree, both
versions choose a fair random bit. Globally complementing the paper protocol's
next bit vector gives the PRISM next-vector distribution: deterministic unequal
bits flip, and independent fair choices remain fair under complement. Adjacent
bit equality, hence the token vector and stabilization reward, is unchanged by
global complement. The induced token processes therefore have the same law.
This argument relies on the source's fair probability and synchronous semantics.

For odd ring size the number of adjacent unequal pairs is even, so the number
of equality tokens is odd. Three equally spaced tokens can be represented by
a bit state when N15: the remaining12 inequality edges admit a consistent ring
assignment. Since `init true` includes that state, the theorem's lower bound is
attained within this original request, not just in an enlarged token model.

## Decision

Storm state expansion/quotient methods are useful native controls, but they are
not the strongest applicable method for this request. The theorem is an existing
reusable algorithm, not NEUMANN's learned discovery and not an answer cache.
If the native portfolio times out on Herman15, that is a limitation of the tested
portfolio, not evidence that NEUMANN exceeds strong native capability.

No operational timing for a source-bound analytic adapter has been measured.
No independent formal proof checker for this published theorem was executed.
The trust assumptions here are the published theorem and the inspected source
binding above. Do not report a timed speedup or a formal machine certificate.
Herman15 is excluded from any claim of an unresolved discovery gap based only on
Storm timings. The registered first cohort remains unchanged.

Primary sources: [ICALP2016 paper](https://drops.dagstuhl.de/opus/volltexte/2016/6239/pdf/LIPIcs-ICALP-2016-104.pdf),
[DOI](https://doi.org/10.4230/LIPIcs.ICALP.2016.104),
[pinned QVBS source](https://github.com/ahartmanns/qcomp/tree/c7324a311475ba1a3f40e36a324e32f91e766540/benchmarks/dtmc/herman).
