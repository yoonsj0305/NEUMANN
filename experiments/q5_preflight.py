"""Exact-runtime compatibility preflight: zero new sources/forwards/solves.

This is not a cold-start sample or a Q5 benchmark. Scientific inference and
registration are never enabled by its CI workflow.
"""
import argparse
import json

from experiments.q5_register import evidence_module, parent_authority, preflight


def run(output, frozen_head):
    ev = evidence_module()
    attempt = ev.Attempt(output, "authority_preflight_only", frozen_head)
    try:
        from threadpoolctl import threadpool_limits
        import torch
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        with threadpool_limits(1):
            manifest, archived_training = parent_authority()
            environment = preflight()
            from experiments.lp_frozen_support_expansion_v101 import restore_frozen_quotient
            models, training = restore_frozen_quotient()
            canonical_training = {str(k): v for k, v in training.items()}
            if canonical_training != {str(k): v for k, v in archived_training.items()}:
                raise ValueError("Q5 restored parent training identity drift")
            ev.contract.validate_authority(manifest, training)
            if set(models) != set(ev.contract.SEEDS):
                raise ValueError("Q5 restored model seed drift")
            report = {"status": "authority_preflight_pass_not_evidence", "environment": environment,
                      "training_identity": canonical_training, "new_sources": 0,
                      "model_forwards": 0, "solver_calls": 0, "route_observations": 0}
            attempt.append("authority", report)
            attempt.finish(report["status"])
            return report
    except BaseException as exc:
        attempt.finish("authority_preflight_failed_zero_observations", error=f"{type(exc).__name__}: {exc}")
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--frozen-head", required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.output, args.frozen_head), sort_keys=True))


if __name__ == "__main__":
    main()
