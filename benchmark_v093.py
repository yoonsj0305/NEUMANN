"""First untimed selector diagnosis; reserve output, preserve failures."""
import argparse,gzip,json
from pathlib import Path


def main():
    parser=argparse.ArgumentParser();parser.add_argument('output',type=Path);args=parser.parse_args()
    try:args.output.mkdir()
    except FileExistsError:parser.error('refusing to overwrite first probe')
    from experiments.lp_selector_probe_v093 import run,validate
    counter=0
    def checkpoint(report):
        nonlocal counter
        with (args.output/f'{counter:04d}_{report["stage"]}.json.gz').open('xb') as stream:
            with gzip.GzipFile(fileobj=stream,mode='wb',mtime=0) as gz:
                gz.write(json.dumps(report,separators=(',',':'),allow_nan=False).encode())
        counter+=1
    try:report=run(checkpoint);validate(report)
    except BaseException as error:
        with (args.output/'execution_failed.json').open('x') as stream:
            json.dump({'error':f'{type(error).__name__}: {error}','rerun':False},stream)
        raise
    print(json.dumps(report['summary'],indent=2))


if __name__=='__main__':main()
