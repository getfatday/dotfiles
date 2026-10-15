"""Hosted-runner-only restore proof for the Hermes platform modules; never run the production deploy playbook.

The `macos-fixture` profile proves the dotmodules role on a synthetic dotfile. This profile proves the part that
role never touched: that a machine which declares `hermes-host` gets the `hermes` and `hermes-platform` modules, and that
`hermes-platform` restores the Hermes install on a clean Mac from this repo alone:

  1. selection: with `hermes-host` both modules are selected, without it neither is;
  2. restore: clone NousResearch/hermes-agent at modules/hermes-platform/pin.txt, apply the vendored local patches
     (modules/hermes-platform/vendor/, a copy of the lab's patch ledger), run the official installer's dependency
     stages, into a throwaway HOME under RUNNER_TEMP;
  3. idempotence: a second setup changes nothing;
  4. `hermes doctor` and `modules/hermes-platform/check.sh --credentialless`.

No credentials: the child environment is built from an allow-list (no token, key or secret ever reaches it), and the
check reports `skipped-credential` for anything that needs one. Nothing outside the temp HOME is written; the stowed
gateway plist is stood in for by a symlink (dotm's stow is covered by the role fixture).
"""
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
import yaml

root = Path(__file__).resolve().parents[1]
if os.environ.get('GITHUB_ACTIONS') != 'true' or not os.environ.get('RUNNER_TEMP'):
    raise SystemExit('Refusing apply: this fixture is restricted to disposable GitHub-hosted runners.')
if platform.system() != 'Darwin':
    raise SystemExit('macos-hermes profile requires macOS')

CAPS = {'macos', 'brew', 'gui', 'hermes-host'}
MODULE = root / 'modules/hermes-platform'
SECRET_NAME = re.compile(r'(TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIAL|API_?KEY|PRIVATE|_KEY$|^SSH_)', re.I)
results = []


def step(name, argv, env, timeout, cwd=root):
    """Run one command, stream nothing until it ends, print its output and a one-line verdict. Never raises."""
    print(f'\n=== {name}\n$ {" ".join(str(a) for a in argv)}', flush=True)
    start = time.time()
    try:
        p = subprocess.run([str(a) for a in argv], cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, text=True, errors='replace', timeout=timeout)
        code, out = p.returncode, p.stdout
    except subprocess.TimeoutExpired as exc:
        code, out = 124, (exc.stdout or '') if isinstance(exc.stdout, str) else ''
        out += f'\n[timed out after {timeout}s]'
    secs = round(time.time() - start, 1)
    print(out.rstrip())
    print(f'--- {name}: exit {code} in {secs}s', flush=True)
    results.append({'step': name, 'exit_code': code, 'seconds': secs})
    return code, out


# 1. selection ---------------------------------------------------------------------------------------------------
sys.path.insert(0, str(root / 'modules/dotm/src'))
from dotm.modules import get_deploy_modules, select_modules  # noqa: E402

selected = set(select_modules(get_deploy_modules(), CAPS, root / 'modules'))
without = set(select_modules(get_deploy_modules(), CAPS - {'hermes-host'}, root / 'modules'))
print(f'=== selection\ncapabilities: {sorted(CAPS)}\nhermes modules selected: {sorted({"hermes", "hermes-platform"} & selected)}')
print(f'selected without hermes-host: {sorted({"hermes", "hermes-platform"} & without)}')
if {'hermes', 'hermes-platform'} - selected or {'hermes', 'hermes-platform'} & without:
    raise SystemExit('hermes-host does not gate exactly the hermes and hermes-platform modules')
results.append({'step': 'selection', 'exit_code': 0, 'seconds': 0})

# 2. prerequisites the module declares, installed the way the dotm role would (real HOME, real brew) -----------------
wanted = ['jq'] + [str(p) for p in (yaml.safe_load((MODULE / 'config.yml').read_text()).get('homebrew_packages') or [])]
real_env = dict(os.environ, HOMEBREW_NO_AUTO_UPDATE='1', HOMEBREW_NO_INSTALL_CLEANUP='1', HOMEBREW_NO_ENV_HINTS='1')
for pkg in wanted:
    if shutil.which(pkg) is None:
        step(f'brew install {pkg}', ['brew', 'install', pkg], real_env, 600)
    else:
        print(f'\n=== prerequisite {pkg}: present at {shutil.which(pkg)}')

# 3. the throwaway machine -----------------------------------------------------------------------------------------
with tempfile.TemporaryDirectory(prefix='dotm-hermes-', dir=os.environ['RUNNER_TEMP']) as temp:
    home = Path(temp) / 'home'
    la = home / 'Library/LaunchAgents'
    la.mkdir(parents=True)
    (la / 'ai.hermes.gateway.plist').symlink_to(MODULE / 'files/Library/LaunchAgents/ai.hermes.gateway.plist')
    keep = {'PATH', 'LANG', 'LC_ALL', 'TERM', 'TMPDIR', 'GITHUB_ACTIONS', 'RUNNER_TEMP'}
    env = {k: v for k, v in os.environ.items() if k in keep and not SECRET_NAME.search(k)}
    env.update(HOME=str(home), GIT_TERMINAL_PROMPT='0', PYTHONDONTWRITEBYTECODE='1', CI='1',
               HERMES_PLATFORM_LEDGER=str(MODULE / 'vendor/ledger/local-patches.jsonl'))
    leaked = sorted(k for k in env if SECRET_NAME.search(k))
    print(f'\n=== environment\nchild env names: {sorted(env)}\ncredential-like names in child env: {leaked or "none"}')
    if leaked:
        raise SystemExit('credential-like variable in the child environment')
    install = home / '.hermes/hermes-agent'

    step('check --dry-run (module structure, vendored ledger and patch files)', [MODULE / 'check.sh', '--dry-run'], env, 120)
    step('offline module tests (fixture upstream, no network)', ['bash', MODULE / 'tests/run.sh'], env, 600)
    step('setup (clone at the pin, patch branch, official installer stages)', [MODULE / 'setup.sh'], env, 1200)
    head1 = subprocess.run(['git', '-C', str(install), 'rev-parse', 'HEAD'], env=env, capture_output=True, text=True).stdout.strip()
    code, out = step('setup again (idempotent)', [MODULE / 'setup.sh'], env, 600)
    head2 = subprocess.run(['git', '-C', str(install), 'rev-parse', 'HEAD'], env=env, capture_output=True, text=True).stdout.strip()
    idem = code == 0 and head1 and head1 == head2 and 'patches_applied=0' in out
    print(f'--- idempotent: {"yes" if idem else "NO"} (HEAD {head1[:10]} -> {head2[:10]})')
    results.append({'step': 'idempotent second setup', 'exit_code': 0 if idem else 1, 'seconds': 0})

    hbin = install / '.hermes/bin/hermes'
    denv = dict(env, HERMES_HOME=str(home / '.hermes'))
    if hbin.exists():
        # The line the proof is read by: `hermes doctor` and its real exit code, whatever check.sh then makes of it.
        step('hermes doctor', [hbin, 'doctor'], denv, 600)
    else:
        print('\n=== hermes doctor: no hermes binary (the installer did not produce .hermes/bin/hermes)')
        results.append({'step': 'hermes doctor', 'exit_code': 127, 'seconds': 0})
    # doctor's own exit is a finding the check classifies; the verdict below is check.sh's.
    results[-1]['informational'] = True
    step('check --credentialless (install, patch branch, plist, hermes doctor)', [MODULE / 'check.sh', '--credentialless'], env, 900)

bad = [r for r in results if r['exit_code'] != 0 and not r.get('informational')]
print('\n=== summary')
print(json.dumps({'profile': 'macos-hermes', 'steps': results, 'failed': [r['step'] for r in bad]}, indent=2))
raise SystemExit(1 if bad else 0)
