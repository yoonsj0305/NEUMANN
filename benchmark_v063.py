"""Hash-pinned SEMI SMPS ingestion and independent extensive-form checks.

Only the observed SIPLIB SEMI subset is supported: two stages, additive RHS
scenario deltas, deterministic columns/matrix, and all scenarios at ROOT.
This is an enabling compiler, not a structural-compression result.
"""

from dataclasses import dataclass
from hashlib import sha256
import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter
from zipfile import ZipFile

import highspy
import numpy as np
from scipy.sparse import bmat, csc_matrix, vstack


ARCHIVE_SHA256 = "f43f9cb87c2ce9f133d05c46c9dd631d401aa440e2848312ad8e61bd4f89bff3"
FIRST_COLS = 612
FIRST_ROWS = 2
OFFICIAL_SHAPES = {2: (20216, 11686), 3: (30018, 17528), 4: (39820, 23370)}


@dataclass(frozen=True)
class SemiSource:
    core: object
    matrix: csc_matrix
    scenarios: tuple[tuple[str, float, dict[int, float]], ...]
    archive_sha256: str
    scenario_count: int


def _scenario_records(content: bytes, row_names: list[str]):
    lines = content.decode("ascii").replace("\x1a", "").splitlines()
    if not any(line.split()[:3] == ["SCENARIOS", "DISCRETE", "ADD"]
               for line in lines):
        raise ValueError("only additive discrete scenarios supported")
    mapping = {name: i for i, name in enumerate(row_names)}
    scenarios = []
    current = None
    for line in lines:
        words = line.split()
        if not words or words[0].startswith("*") or words[0] in {
                "STOCH", "SCENARIOS", "ENDATA"}:
            continue
        if words[0] == "SC":
            if len(words) != 5 or words[2] != "ROOT" or words[4] != "STG00002":
                raise ValueError("unsupported scenario tree")
            current = (words[1], float(words[3]), {})
            scenarios.append(current)
        elif words[0] == "RHS1":
            if current is None or len(words) != 3 or words[1] not in mapping:
                raise ValueError("unsupported scenario entry")
            row = mapping[words[1]]
            if row < FIRST_ROWS or row in current[2]:
                raise ValueError("invalid or duplicate RHS delta")
            current[2][row] = float(words[2])
        else:
            raise ValueError(f"unsupported SMPS record: {words[0]}")
    if not scenarios or abs(sum(p for _, p, _ in scenarios) - 1.0) > 1e-12:
        raise ValueError("scenario probabilities must sum to one")
    return tuple(scenarios)


def load_source(archive: Path, scenario_count: int) -> SemiSource:
    if scenario_count not in OFFICIAL_SHAPES:
        raise ValueError("unsupported scenario count")
    data = archive.read_bytes()
    digest = sha256(data).hexdigest()
    if digest != ARCHIVE_SHA256:
        raise ValueError("source archive hash mismatch")
    with ZipFile(archive) as z, TemporaryDirectory() as tmp:
        if set(z.namelist()) != {"semi.core", "semi.time", "semi2.stoch",
                                   "semi3.stoch", "semi4.stoch"}:
            raise ValueError("unexpected archive members")
        time_lines = [line.split() for line in z.read("semi.time").decode("ascii").splitlines()]
        if [words for words in time_lines if words and words[0].startswith("C")] != [
                ["C0000001", "R0000001", "STG00001"],
                ["C0000613", "R0000003", "STG00002"]]:
            raise ValueError("unexpected stage interface")
        core_path = Path(tmp) / "semi.mps"  # HiGHS selects its MPS reader by extension.
        core_path.write_bytes(z.read("semi.core"))
        solver = highspy.Highs()
        solver.setOptionValue("output_flag", False)
        if solver.readModel(str(core_path)) != highspy.HighsStatus.kOk:
            raise ValueError("core MPS parse failed")
        core = solver.getLp()
        if (core.num_col_, core.num_row_) != (10414, 5844):
            raise ValueError("unexpected core shape")
        if core.col_names_[FIRST_COLS] != "C0000613" or core.row_names_[FIRST_ROWS] != "R0000003":
            raise ValueError("stage names do not match core positions")
        if (sum(k != highspy.HighsVarType.kContinuous for k in core.integrality_[:FIRST_COLS])
                != FIRST_COLS or any(k != highspy.HighsVarType.kContinuous
                                     for k in core.integrality_[FIRST_COLS:])):
            raise ValueError("unexpected integrality interface")
        matrix = core.a_matrix_
        if matrix.format_ != highspy.MatrixFormat.kColwise:
            raise ValueError("expected column-wise MPS")
        a = csc_matrix((matrix.value_, matrix.index_, matrix.start_),
                       shape=(core.num_row_, core.num_col_))
        if a[:FIRST_ROWS, FIRST_COLS:].nnz:
            raise ValueError("second-stage variables in first-stage rows")
        scenarios = _scenario_records(z.read(f"semi{scenario_count}.stoch"),
                                      list(core.row_names_))
        if len(scenarios) != scenario_count:
            raise ValueError("scenario count mismatch")
    return SemiSource(core, a, scenarios, digest, scenario_count)


def extensive_form(source: SemiSource):
    p, a = source.core, source.matrix
    n, m = source.scenario_count, p.num_row_ - FIRST_ROWS
    # One shared first stage; a distinct recourse block for each scenario.
    top = a[:FIRST_ROWS, :FIRST_COLS]
    linking = a[FIRST_ROWS:, :FIRST_COLS]
    recourse = a[FIRST_ROWS:, FIRST_COLS:]
    first = vstack([top] + [linking] * n, format="csc")
    second = bmat([[None if k != j else recourse for j in range(n)]
                   for k in range(n)], format="csc")
    from scipy.sparse import hstack
    matrix = hstack([first, vstack([csc_matrix((FIRST_ROWS, second.shape[1])),
                                   second], format="csc")], format="csc")
    result = highspy.HighsLp()
    result.num_row_, result.num_col_ = matrix.shape
    result.sense_, result.offset_ = p.sense_, p.offset_
    result.col_cost_ = list(p.col_cost_[:FIRST_COLS]) + [
        probability * cost for _, probability, _ in source.scenarios
        for cost in p.col_cost_[FIRST_COLS:]]
    result.col_lower_ = list(p.col_lower_[:FIRST_COLS]) + list(p.col_lower_[FIRST_COLS:]) * n
    result.col_upper_ = list(p.col_upper_[:FIRST_COLS]) + list(p.col_upper_[FIRST_COLS:]) * n
    result.integrality_ = list(p.integrality_[:FIRST_COLS]) + list(p.integrality_[FIRST_COLS:]) * n
    low = np.asarray(p.row_lower_[FIRST_ROWS:], dtype=float)
    high = np.asarray(p.row_upper_[FIRST_ROWS:], dtype=float)
    row_lower = list(p.row_lower_[:FIRST_ROWS])
    row_upper = list(p.row_upper_[:FIRST_ROWS])
    for _, _, deltas in source.scenarios:
        shifts = np.zeros(m)
        for row, delta in deltas.items():
            shifts[row - FIRST_ROWS] = delta
        row_lower.extend(np.where(np.isfinite(low), low + shifts, low))
        row_upper.extend(np.where(np.isfinite(high), high + shifts, high))
    result.row_lower_, result.row_upper_ = row_lower, row_upper
    result.a_matrix_.format_ = highspy.MatrixFormat.kColwise
    result.a_matrix_.num_row_, result.a_matrix_.num_col_ = matrix.shape
    result.a_matrix_.start_ = matrix.indptr.tolist()
    result.a_matrix_.index_ = matrix.indices.tolist()
    result.a_matrix_.value_ = matrix.data.tolist()
    if (result.num_col_, result.num_row_) != OFFICIAL_SHAPES[n]:
        raise ValueError("deterministic-equivalent size differs from source")
    return result


def verify_original(source: SemiSource, x) -> tuple[float, float, float]:
    """Check each original scenario against the core, independently of expanded LP."""
    p, a = source.core, source.matrix
    n = source.scenario_count
    x = np.asarray(x)
    if len(x) != FIRST_COLS + n * (p.num_col_ - FIRST_COLS) or not np.isfinite(x).all():
        return float("inf"), float("inf"), float("nan")
    first = x[:FIRST_COLS]
    values = a[:FIRST_ROWS, :FIRST_COLS] @ first
    violations = []
    cost = float(np.dot(p.col_cost_[:FIRST_COLS], first) + p.offset_)
    for side, observed in zip((p.row_lower_[:FIRST_ROWS], p.row_upper_[:FIRST_ROWS]),
                              (values, values)):
        violations.append((np.asarray(side), observed))
    integrality = float(np.max(np.abs(first - np.rint(first))))
    column_checks = []
    for s, (_, prob, deltas) in enumerate(source.scenarios):
        recourse = x[FIRST_COLS + s * (p.num_col_ - FIRST_COLS):
                     FIRST_COLS + (s + 1) * (p.num_col_ - FIRST_COLS)]
        row_values = a[FIRST_ROWS:, :FIRST_COLS] @ first + a[FIRST_ROWS:, FIRST_COLS:] @ recourse
        shifts = np.zeros(p.num_row_ - FIRST_ROWS)
        for row, delta in deltas.items():
            shifts[row - FIRST_ROWS] = delta
        violations.extend(((np.asarray(p.row_lower_[FIRST_ROWS:]) + shifts, row_values),
                           (np.asarray(p.row_upper_[FIRST_ROWS:]) + shifts, row_values)))
        cost += prob * float(np.dot(p.col_cost_[FIRST_COLS:], recourse))
        for bounds, sign in ((p.col_lower_[FIRST_COLS:], -1), (p.col_upper_[FIRST_COLS:], 1)):
            observed = sign * (recourse - np.asarray(bounds))
            column_checks.append((np.zeros(len(recourse)), observed))
    violations.extend(column_checks)
    for bounds, sign in ((p.col_lower_[:FIRST_COLS], -1), (p.col_upper_[:FIRST_COLS], 1)):
        violations.append((np.zeros(len(first)), sign * (first - np.asarray(bounds))))
    # First 2(n+1) entries are row lower/upper pairs; remaining entries are bounds.
    max_error = 0.0
    for i, (bound, observed) in enumerate(violations):
        if i < 2 + 2 * n:
            direction = 1 if i % 2 else -1
            error = direction * (observed - bound)
        else:
            error = observed
        finite = np.isfinite(error)
        if finite.any():
            max_error = max(max_error, float(np.max(np.maximum(0.0, error[finite]) /
                            np.maximum(1.0, np.abs(bound[finite])))))
    return max_error, integrality, cost


def audit(archive: Path, sanity_time_limit: float = 3.0) -> dict:
    cases = []
    for n in OFFICIAL_SHAPES:
        source = load_source(archive, n)
        lp = extensive_form(source)
        solver = highspy.Highs()
        solver.setOptionValue("output_flag", False)
        solver.setOptionValue("threads", 1)
        if solver.passModel(lp) != highspy.HighsStatus.kOk:
            raise ValueError(f"expanded SEMI{n} rejected by HiGHS")
        cases.append({"scenario_count": n, "probabilities": [p for _, p, _ in source.scenarios],
                      "rhs_delta_counts": [len(d) for _, _, d in source.scenarios],
                      "variables": lp.num_col_, "rows": lp.num_row_,
                      "integer_variables": sum(k != highspy.HighsVarType.kContinuous
                                               for k in lp.integrality_),
                      "nonzeros": len(lp.a_matrix_.value_)})
    source = load_source(archive, 2)
    lp = extensive_form(source)
    solver = highspy.Highs()
    solver.setOptionValue("output_flag", False)
    solver.setOptionValue("threads", 1)
    solver.setOptionValue("time_limit", sanity_time_limit)
    start = perf_counter()
    if solver.passModel(lp) != highspy.HighsStatus.kOk:
        raise ValueError("sanity model transfer failed")
    status = solver.run()
    elapsed = perf_counter() - start
    solution = solver.getSolution()
    if not solution.value_valid:
        raise ValueError("no incumbent for independent verifier sanity check")
    primal, integrality, objective = verify_original(source, solution.col_value)
    info = solver.getInfo()
    agreement = abs(objective - info.objective_function_value)
    if primal > 1e-7 or integrality > 1e-6 or agreement > 1e-6:
        raise ValueError("original SMPS verification failed")
    changed = list(solution.col_value)
    changed[0] += 0.5
    if verify_original(source, changed)[1] < 0.49:
        raise ValueError("integrality negative control failed")
    changed = list(solution.col_value)
    changed[FIRST_COLS] += 1000
    if verify_original(source, changed)[0] <= 1e-7:
        raise ValueError("primal negative control failed")
    return {"protocol": "v0.0.63 nonblind SEMI input and verifier audit",
            "archive_sha256": source.archive_sha256, "highs_version": solver.version(),
            "source": "SIPLIB SEMI source ZIP; no redistribution",
            "cases": cases,
            "sanity": {"scenario_count": 2, "solver_time_limit_s": sanity_time_limit,
                       "full_path_elapsed_s": elapsed, "run_status": str(status),
                       "solver_status": str(solver.getModelStatus()),
                       "objective": objective, "dual_bound": info.mip_dual_bound,
                       "relative_gap": info.mip_gap, "objective_agreement": agreement,
                       "original_primal_violation": primal,
                       "original_integrality_violation": integrality,
                       "negative_controls": "primal and integrality rejected"},
            "scope": "input and verifier sanity only; no candidate or iso-capability comparison"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.archive)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"cases": len(result["cases"]), "sanity": result["sanity"]}, indent=2))
