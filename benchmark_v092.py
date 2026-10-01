"""Explicit first late-pruning runner; never CI fitting or timing."""
import argparse,gzip,json
from pathlib import Path


def main():
    parser=argparse.ArgumentParser();parser.add_argument('output',type=Path);args=parser.parse_args()
    try:args.output.mkdir()
    except FileExistsError:parser.error('refusing to overwrite first late screen')
    from experiments.lp_late_screen_v092 import run,validate
    counter=0
    def checkpoint(report):
        nonlocal counter
        target=args.output/f'{counter:04d}_{report["stage"]}.json.gz'
        with target.open('xb') as stream,gzip.GzipFile(fileobj=stream,mode='wb',mtime=0) as gz:
            gz.write(json.dumps(report,separators=(',',':'),allow_nan=False).encode())
        counter+=1
    try:report=run(checkpoint);validate(report)
    except BaseException as error:
        with (args.output/'execution_failed.json').open('x') as stream:
            json.dump({'error':f'{type(error).__name__}: {error}','rerun':False},stream)
        raise
    print(json.dumps(report['summary'],indent=2))


if __name__=='__main__':main()
