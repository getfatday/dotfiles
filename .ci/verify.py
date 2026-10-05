"""Model-independent local/CI verifier. Receipts are evidence, not an auth boundary.

Protect this code/contract and require the aggregate GitHub check before merge.
Nothing here applies the production playbook or authorizes deployment.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def identity(root=ROOT):
    def git(*args):
        return subprocess.check_output(['git', '-C', str(root), *args], env={**os.environ, 'GIT_OPTIONAL_LOCKS': '0'})
    paths = sorted(set(git('ls-files', '-z', '--cached', '--others', '--exclude-standard').split(b'\0')) - {b''})
    inputs = hashlib.sha256()
    for name in paths:
        path = root / os.fsdecode(name)
        # Output/cache directories are not verification inputs, even before their ignore rules are committed.
        if any(part in {'__pycache__', '.pytest_cache'} for part in path.parts):
            continue
        if name.startswith((b'.ci/results/', b'.ci/vendor/', b'.ci/.venv/')):
            continue
        data = os.readlink(path).encode() if path.is_symlink() else path.read_bytes() if path.is_file() else b'<deleted>'
        executable = b'x' if path.is_file() and path.stat().st_mode & 0o111 else b'-'
        inputs.update(name + b'\0' + executable + b'\0' + digest(data).encode() + b'\0')
    return {'commit': git('rev-parse', 'HEAD').decode().strip(),
            'input_sha256': inputs.hexdigest(),
            'contract_sha256': digest((root / '.ci/contract.json').read_bytes())}


def contract():
    return json.loads((ROOT / '.ci/contract.json').read_text())


def validate_receipts(spec, expected, receipts, needs=None, now=None):
    now = time.time() if now is None else now
    required = spec['required_profiles']
    if len(receipts) != len(required) or {r.get('profile') for r in receipts} != set(required):
        raise ValueError('missing, duplicate or unexpected profile evidence')
    if needs is not None:
        if set(needs) != set(required) or any(v != 'success' for v in needs.values()):
            raise ValueError('required job failed, skipped, cancelled or is missing')
    for r in receipts:
        if r.get('identity') != expected:
            raise ValueError('stale commit, diff or contract evidence')
        if r.get('status') != 'passed' or r.get('inputs_unchanged') is not True:
            raise ValueError('failed or mutated verification inputs')
        age = now - r.get('finished_at', 0)
        if not 0 <= age <= spec['receipt_max_age_seconds']:
            raise ValueError('expired or future evidence')
        checks = r.get('checks', [])
        commands = spec['profiles'][r['profile']]['checks']
        if len(checks) != len(commands) or any(c.get('command') != cmd or c.get('exit_code') != 0 for c, cmd in zip(checks, commands)):
            raise ValueError('missing, altered or failing required command')
    return True


def run(profile):
    spec = contract()
    selected = spec['profiles'][profile]
    before = identity()
    if selected['system'] != 'any' and platform.system() != selected['system']:
        raise ValueError('wrong operating system for profile')
    if 'architecture' in selected and platform.machine().lower() not in selected['architecture']:
        raise ValueError('native ARM runner required; emulation is not hardware qualification')
    out = ROOT / '.ci/results'
    out.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(ROOT / 'modules/dotm/src'))
    checks = []
    for i, command in enumerate(selected['checks']):
        argv = [sys.executable if a == '{python}' else a for a in command]
        log = out / f'{profile}-{i}.log'
        try:
            p = subprocess.run(argv, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               timeout=spec['command_timeout_seconds'])
            code, data = p.returncode, p.stdout
        except subprocess.TimeoutExpired:
            code, data = 124, b'Command timed out; verification failed.\n'
        log.write_bytes(data)
        checks.append({'command': command, 'exit_code': code, 'log_sha256': digest(data)})
        print(data.decode(errors='replace'), end='')
        if code:
            break
    unchanged = before == identity()
    passed = unchanged and len(checks) == len(selected['checks']) and all(c['exit_code'] == 0 for c in checks)
    receipt = {'schema_version': 1, 'profile': profile, 'identity': before,
               'status': 'passed' if passed else 'failed', 'inputs_unchanged': unchanged,
               'finished_at': time.time(), 'checks': checks,
               'environment': {'python': platform.python_version(), 'system': platform.system(), 'architecture': platform.machine()},
               'run_id': os.environ.get('GITHUB_RUN_ID'), 'run_attempt': os.environ.get('GITHUB_RUN_ATTEMPT')}
    (out / f'{profile}.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return 0 if passed else 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['run', 'accept'])
    parser.add_argument('profile', nargs='?')
    args = parser.parse_args()
    if args.action == 'run':
        return run(args.profile)
    spec = contract()
    receipts = [json.loads(p.read_text()) for p in (ROOT / '.ci/results').glob('*.json')]
    needs = json.loads(os.environ['VERIFICATION_NEEDS']) if 'VERIFICATION_NEEDS' in os.environ else None
    validate_receipts(spec, identity(), receipts, needs)
    for r in receipts:
        if os.environ.get('GITHUB_RUN_ID') and (r.get('run_id') != os.environ['GITHUB_RUN_ID'] or r.get('run_attempt') != os.environ.get('GITHUB_RUN_ATTEMPT')):
            raise ValueError('receipt belongs to a different workflow run or attempt')
        for index, check in enumerate(r['checks']):
            log = ROOT / '.ci/results' / f"{r['profile']}-{index}.log"
            if not log.is_file() or digest(log.read_bytes()) != check.get('log_sha256'):
                raise ValueError('missing or altered command log')
    print('ACCEPTED: every required profile passed for this exact commit, input tree and contract.')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError) as exc:
        print(f'BLOCKED: {exc}', file=sys.stderr)
        raise SystemExit(1)
