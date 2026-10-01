"""Once-only, untimed adapter diagnostic on the already-opened retained inputs."""
import argparse
import gzip
import json
from pathlib import Path

from neumann1.lp_program_parity_v085 import load_source, run_diagnostic, validate_archive


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path, help='new .json.gz first diagnostic')
    parser.add_argument('--source', type=Path,
                        default=Path('docs/experiments/results/v084_first_audit.manifest.json'))
    args = parser.parse_args()
    if not args.output.name.endswith('.json.gz'):
        parser.error('output must end with .json.gz')
    try:
        stream = args.output.open('xb')
    except FileExistsError:
        parser.error('refusing to overwrite a retained or reserved attempt')
    with stream, gzip.GzipFile(fileobj=stream, mode='wb', mtime=0) as archive:
        try:
            original = load_source(args.source)
            report = run_diagnostic(original)
        except Exception as exc:
            archive.write(json.dumps({'execution_failed': f'{type(exc).__name__}: {exc}',
                                      'do_not_overwrite': True}).encode())
            raise
        archive.write(json.dumps(report, separators=(',', ':'), allow_nan=False).encode())
    validate_archive(report, original)
    print(json.dumps(report['summary'], indent=2))


if __name__ == '__main__':
    main()
