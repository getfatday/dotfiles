"""Aggregate CI result for the lab's fleet ledger: one JSON document per workflow run.

Reads the `needs` results as JSON in FLEET_NEEDS ({"job": "success"|"failure"|"cancelled"|"skipped"}) and the
GitHub run environment, writes fleet-receipt.json. It reports; it does not decide, alarm or touch any ledger.
The lab's daily ci-receipt reconciler (docs/design/routines/dotfiles/ci-receipt.yaml in the lab repo) reads
the same facts from `gh run list` and appends the ledger row; this file is the run's own copy of them.
"""
import datetime
import json
import os
from pathlib import Path
import sys


def build(needs, env, now=None):
    now = now or datetime.datetime.now(datetime.timezone.utc)
    jobs = dict(sorted(needs.items()))
    if not jobs:
        raise ValueError('no job results supplied')
    ok = all(v == 'success' for v in jobs.values())
    repo = env.get('GITHUB_REPOSITORY', '')
    run_id = env.get('GITHUB_RUN_ID', '')
    return {'schema_version': 1, 'routine': 'ci-verify', 'profile': 'dotfiles',
            'period': now.strftime('%Y-%m-%d'), 'ts': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'run_id': run_id, 'run_attempt': env.get('GITHUB_RUN_ATTEMPT', ''),
            'commit': env.get('GITHUB_SHA', ''), 'ref': env.get('GITHUB_REF_NAME', ''),
            'event': env.get('GITHUB_EVENT_NAME', ''),
            'url': f'https://github.com/{repo}/actions/runs/{run_id}' if repo and run_id else '',
            'jobs': jobs, 'conclusion': 'success' if ok else 'failure', 'probe_exit': 0 if ok else 1}


def main(argv):
    out = Path(argv[1] if len(argv) > 1 else 'fleet-receipt.json')
    try:
        needs = json.loads(os.environ['FLEET_NEEDS'])
        doc = build(needs, os.environ)
    except (KeyError, ValueError) as exc:
        print(f'fleet-receipt: {exc}', file=sys.stderr)
        return 1
    out.write_text(json.dumps(doc, indent=2) + '\n')
    print(json.dumps(doc, indent=2))
    # The receipt is evidence of the run, not a gate: the verdict already lives in the jobs' own results.
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
