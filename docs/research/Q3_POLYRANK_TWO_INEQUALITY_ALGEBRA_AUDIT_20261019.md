# Q3 PolyRank independent algebraic proof audit, 2026-10-19

Status: PASS_EXACT_ALGEBRA_ON_PUBLISHED_BRANCH_TRANSCRIPTION.
This is a posthoc audit of the already-opened original PolyRank poly2.sl (PR #290), NOT a new blind source result, neural structure-learning result, or new SMT run. The first Actions #39238471276 and all historical failures remain immutable.

Original SaswatPadhi/LoopInvGen commit 6ac90265b11431c9477dfbd33e3e3380234c0499, file benchmarks/LIA/2005.ICALP_PolyRank/poly2.sl, Git blob 17448225fffad0cef48634b9d68f4f9193d616d8.

## Two sufficient inequalities

Define D = x0 - y0 - c - x + y. Claim the source-only invariant I = (c >= 0) AND (D >= 0). This is a manually reduced *after-the-fact* certificate, NOT a change to the first run's 242 generated candidate atoms or eight surviving atoms.

INIT: Original Pre fixes c=0, x=x0, y=y0, so D=0 and c>=0.

STEP: Original Trans always leaves x0 and y0 fixed. It has exactly three cases.

1. If x<y, the values c,x,y remain fixed. Thus D'-D=0.
2. If x>=y, then c'=c+1, x'<=x-1, y'=y. Put dx=x-x'>=1. Exact subtraction gives D'-D=dx-1>=0.
3. If x>=y, then c'=c+1, x'=x, y'>=y+1. Put dy=y'-y>=1. Exact subtraction gives D'-D=dy-1>=0.

In all cases c' is c or c+1, hence c'>=0 whenever c>=0. Accordingly I and original Trans imply I' for all integer source states, including all nondeterministic successors.

SAFE: Whenever x>=y, the identity x0-y0 = c + (x-y) + D and nonnegativity of c, x-y, D imply x0>=y0 and c<=x0-y0. This satisfies the applicable branch of the published conditional original Post. The x0<y0 Post branch is impossible under I and x>=y. Thus I implies original Post.

Negative mutation control: relax x'<=x-1 to x'<=x. An initial state c=x=y=x0=y0=0 permits c'=1,x'=y'=0, yielding D'=-1. The certificate therefore fails for this weakened, different transition.

## Evidence and boundary

Local self-contained SymPy checker reproduced these exact arithmetic identities, producing PASS and script SHA256 eb01b1c70877cc13062baac74cc3e49ad2c967ede5beb26e6c3a3779e78e452a. It checked the manually transcribed published branches, not the original source Git blob locally (source_git_blob_verified_locally=false without the source file). Existing Actions #39238471276 performed the separate byte-SHA-bound original native Z3 and independent cvc5 3VC checks.

This is one after-the-fact, source-specific, classical algebraic proof. No new blind generalization, independent neural invention, resource dominance, or global Q1-Q7 closure is claimed. The 2 hand-selected sufficient inequalities are an explanatory reduction from the first experiment's 8 machine-verified inductive source constraints, not an automatically discovered minimal certificate.
