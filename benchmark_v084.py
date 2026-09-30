"""Explicit first audit. Reserve output before any solve; never overwrite evidence."""
import argparse
import gzip
import json
from pathlib import Path
from neumann1.lp_portfolio_v084 import run_audit, validate_archive


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path, help='new .json.gz first-audit archive')
    args = parser.parse_args()
    if not args.output.name.endswith('.json.gz'):
        parser.error('output must end with .json.gz')
    try:
        stream = args.output.open('xb')
    except FileExistsError:
        parser.error('refusing to overwrite a retained or reserved attempt')
    with stream, gzip.GzipFile(fileobj=stream, mode='wb', mtime=0) as archive:
        try:
            report = run_audit()
        except Exception as exc:
            archive.write(json.dumps({'execution_failed': f'{type(exc).__name__}: {exc}',
                                      'do_not_overwrite': True}).encode())
            raise
        # Preserve completed measurement even if post-measurement replay fails.
        archive.write(json.dumps(report, separators=(',', ':'), allow_nan=False).encode())
    validate_archive(report)
    print(json.dumps(report['summary'].get('forms', report['summary']), indent=2))


if __name__ == '__main__':
    main()
