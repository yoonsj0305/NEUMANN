"""First retraining/screen runner; reserve output and preserve every checkpoint."""
import argparse,gzip,json
from pathlib import Path


def main():
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);args=p.parse_args()
    try:args.output.mkdir()
    except FileExistsError:p.error('refusing to overwrite first screen')
    from experiments.lp_cheap_screen_v091 import run,validate
    counter=0
    def checkpoint(report):
        nonlocal counter
        target=args.output/f'{counter:04d}_{report["stage"]}.json.gz'
        with target.open('xb') as stream,gzip.GzipFile(fileobj=stream,mode='wb',mtime=0) as gz:
            gz.write(json.dumps(report,separators=(',',':'),allow_nan=False).encode())
        counter+=1
    try:report=run(checkpoint);validate(report)
    except BaseException as e:
        with (args.output/'execution_failed.json').open('x') as f:
            json.dump({'error':f'{type(e).__name__}: {e}','rerun':False},f)
        raise
    print(json.dumps(report['summary'],indent=2))


if __name__=='__main__':main()
