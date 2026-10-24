"""Q3 evidence-gated, model-agnostic program library.

This uses externally GENERATED operator code; it contains NO neural generator.
Finite source demonstrations are NOT a global correctness proof.
The AST guard is NOT a complete Python security sandbox.
"""
from __future__ import annotations
import ast, hashlib, json
from dataclasses import dataclass
from contextual_operator import bind_operator, UnknownContext

@dataclass(frozen=True)
class LibraryItem:
    id: str
    code: str
    function: str
    sha256: str
    origin: str

class VerifiedLibrary:
    def __init__(self):
        self.items = []
        self.events = []
        self.stats = dict(proposal_requests=0, registered=0, reuse_calls=0,
                          candidate_checks=0, refused=0, ambiguous=0)

    def _matching(self, demos):
        matched = []
        for item in self.items:
            self.stats['candidate_checks'] += 1
            try:
                op = bind_operator(item.code, demos)
            except (UnknownContext, ValueError, TypeError, NameError, IndexError, StopIteration):
                continue
            if all(op(d['input']) == d['output'] for d in demos):
                matched.append((item, op))
        return matched

    @staticmethod
    def _explicit_example_lookup(source):
        """Block literal grid tables; this is NOT a general nonmemorization proof."""
        try:
            t = ast.parse(source)
        except SyntaxError:
            return True
        for q in ast.walk(t):
            if isinstance(q, ast.Compare):
                args = [q.left, *q.comparators]
                names = any(isinstance(a, ast.Name) and a.id in ('grid', 'xs', 'data', 'x') for a in args)
                literals = any(isinstance(a, (ast.List, ast.Tuple, ast.Dict, ast.Set)) for a in args)
                if names and literals:
                    return True
        return False

    def admit(self, name, source, function, demos, heldout, origin):
        """Registration requires ≥2 demos + at least one independent evidence row.

        The held-out output is used only for admission, never model fitting.
        A failing candidate is rejected and never silently repaired from gold.
        """
        if len(demos) < 2 or not heldout or self._explicit_example_lookup(source):
            self.stats['refused'] += 1
            self.events.append(dict(event='REFUSE_INSUFFICIENT_OR_LOOKUP', id=name))
            return False
        sha = hashlib.sha256(source.encode()).hexdigest()
        if any(i.sha256 == sha for i in self.items):
            self.stats['refused'] += 1
            return False
        if self._matching(demos):
            self.stats['refused'] += 1
            self.events.append(dict(event='REFUSE_OBSERVED_EQUIVALENCE', id=name))
            return False
        try:
            op = bind_operator(source, demos)
            accepted = all(op(d['input']) == d['output'] for d in heldout)
        except (UnknownContext, ValueError, TypeError, NameError, IndexError, StopIteration):
            accepted = False
        if not accepted:
            self.stats['refused'] += 1
            self.events.append(dict(event='REFUSE_HELDOUT', id=name))
            return False
        self.items.append(LibraryItem(name, source, function, sha, origin))
        self.stats['registered'] += 1
        self.events.append(dict(event='ADMIT_FINITE_EVIDENCE_ONLY', id=name,
                                sha256=sha, origin=origin))
        return True

    def reuse(self, demos, query):
        """Returns an explicitly unverified prediction or UNKNOWN, never invented proof."""
        self.stats['reuse_calls'] += 1
        if len(demos) < 2:
            self.stats['refused'] += 1
            return {'status':'UNKNOWN', 'matching_count':0}
        matches = self._matching(demos)
        if len(matches) != 1:
            self.stats['ambiguous'] += int(len(matches) > 1)
            self.stats['refused'] += 1
            return {'status':'UNKNOWN', 'matching_count':len(matches)}
        item, op = matches[0]
        output = op(query)
        self.events.append(dict(event='PREDICT', library_id=item.id,
            prediction_sha256=hashlib.sha256(json.dumps(output, sort_keys=True).encode()).hexdigest()))
        return {'status':'PREDICTED_UNVERIFIED', 'operator_id':item.id,
                'output':output, 'code_sha256':item.sha256}

    def snapshot(self):
        return {'operators':[dict(id=i.id, sha256=i.sha256, origin=i.origin)
                             for i in self.items],
                'stats':dict(self.stats), 'events':list(self.events)}
