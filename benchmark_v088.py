"""Explicit immutable first-fit/final runner. Not a CI smoke test."""
import argparse
import gzip
import json
from pathlib import Path


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('output_directory',type=Path)
    args=parser.parse_args()
    try: args.output_directory.mkdir()
    except FileExistsError: parser.error('refusing to overwrite first study directory')
    from experiments.lp_model_study_v088 import run_study, validate_report
    counter=0
    def checkpoint(report):
        nonlocal counter
        path=args.output_directory/f'{counter:02d}_{report["stage"]}.json.gz'
        with path.open('xb') as stream, gzip.GzipFile(fileobj=stream,mode='wb',mtime=0) as archive:
            archive.write(json.dumps(report,separators=(',',':'),allow_nan=False).encode())
        counter+=1
    try: report=run_study(checkpoint)
    except BaseException as exc:
        failure=args.output_directory/'execution_failed.json'
        with failure.open('x') as stream: json.dump({'error':f'{type(exc).__name__}: {exc}',
                                                   'do_not_rerun_or_overwrite':True},stream)
        raise
    if report['stage']=='completed': validate_report(report)
    print(json.dumps(report['summary'],indent=2))


if __name__=='__main__': main()
