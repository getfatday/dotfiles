"""Hosted-runner-only pinned-role fixture; never run the production deploy playbook."""
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile
import yaml

root = Path(__file__).resolve().parents[1]
if len(sys.argv) != 2 or sys.argv[1] not in {'macos', 'linux-arm'}:
    raise SystemExit('Usage: platform_fixture.py {macos|linux-arm}')
profile = sys.argv[1]
if os.environ.get('GITHUB_ACTIONS') != 'true' or not os.environ.get('RUNNER_TEMP'):
    raise SystemExit('Refusing apply: this fixture is restricted to disposable GitHub-hosted runners.')
if profile == 'macos' and platform.system() != 'Darwin':
    raise SystemExit('macOS profile requires macOS')
if profile == 'linux-arm' and (platform.system() != 'Linux' or platform.machine().lower() not in {'arm64', 'aarch64'}):
    raise SystemExit('Linux ARM profile requires native ARM Linux')
role = root / '.ci/vendor/roles/ansible-role-dotmodules'
# The capability set this profile declares, the same list the machine-side `capabilities:` + platform resolve to. The
# macOS profile declares `hermes-host`, so the opt-in Hermes modules are selected (and only because of it).
caps = ['macos', 'brew', 'gui', 'hermes-host'] if profile == 'macos' else ['linux-arm', 'apt', 'headless']
sys.path.insert(0, str(root / 'modules/dotm/src'))
from dotm.modules import select_modules  # noqa: E402
# THIS checkout's profiles.yml: dotm's own lookup follows ~/.config/dotm (a machine's repo), which a runner lacks.
base_modules = yaml.safe_load((root / 'playbooks/profiles.yml').read_text())['base_modules']
selected = select_modules(base_modules, set(caps), root / 'modules')
print(f'{profile}: capabilities {caps}; {len(selected)} real modules selected (selection only, never applied here)')
if profile == 'macos':
    missing = {'hermes', 'hermes-platform'} - set(selected)
    if missing:
        raise SystemExit(f'hermes-host is declared but {sorted(missing)} not selected')
    without = set(select_modules(base_modules, set(caps) - {'hermes-host'}, root / 'modules'))
    if {'hermes', 'hermes-platform'} & without:
        raise SystemExit('hermes modules are selected without hermes-host: the capability gate is broken')
    print('macos: hermes, hermes-platform selected with hermes-host and not without it')
elif {'hermes', 'hermes-platform'} & set(selected):
    raise SystemExit('linux-arm must not select the macOS-only Hermes modules')
install_info = yaml.safe_load((role / 'meta/.galaxy_install_info').read_text())
if install_info.get('version') != '28cdf7a7d58ccd1b9b985d09a5d4387f120bc412':
    raise SystemExit('Unexpected role revision')
with tempfile.TemporaryDirectory(prefix='dotm-ci-', dir=os.environ['RUNNER_TEMP']) as temp:
    temp = Path(temp)
    home = temp / 'home'
    home.mkdir()
    modules = temp / 'modules'
    files = modules / 'ci-smoke/files'
    files.mkdir(parents=True)
    (files / '.dotm-ci-marker').write_text('dotm isolated role fixture\n')
    (modules / 'ci-smoke/config.yml').write_text('stow_dirs: [ci-smoke]\n')
    play = [{'name': 'Bounded dotmodules fixture', 'hosts': 'localhost', 'gather_facts': False,
             'vars': {'ansible_env': {'HOME': str(home), 'PATH': os.environ['PATH']},
                      'ansible_python_interpreter': sys.executable,
                      'dotmodules_repo': 'file://' + str(modules), 'dotmodules_dest': str(home / '.dotmodules'),
                      'dotmodules_install': ['ci-smoke'], 'dotmodules_skip_mas_role': True,
                      'dotm_platform': caps},
             'roles': ['ansible-role-dotmodules']}]
    playbook = temp / 'fixture.yml'
    playbook.write_text(yaml.safe_dump(play))
    cfg = temp / 'ansible.cfg'
    cfg.write_text('[defaults]\nretry_files_enabled = False\n')
    env = dict(os.environ, HOME=str(home), ANSIBLE_CONFIG=str(cfg),
               ANSIBLE_ROLES_PATH=str(root / '.ci/vendor/roles'),
               ANSIBLE_COLLECTIONS_PATH=str(root / '.ci/vendor/collections'),
               ANSIBLE_LOCAL_TEMP=str(temp / 'local'), ANSIBLE_REMOTE_TEMP=str(temp / 'remote'),
               ANSIBLE_NOCOLOR='1')
    # root-level marker avoids modifying real dotfiles and unrelated role conflict/merge paths.
    for pass_no in [1, 2]:
        p = subprocess.run(['ansible-playbook', '-i', 'localhost,', '-c', 'local', str(playbook)],
                           env=env, capture_output=True, text=True, timeout=180)
        print(p.stdout)
        if p.returncode:
            print(p.stderr)
            raise SystemExit(p.returncode)
        recaps = re.findall(r'localhost\s+:\s+ok=\d+\s+changed=(\d+)\s+unreachable=(\d+)\s+failed=(\d+)', p.stdout)
        if len(recaps) != 1 or any(int(n) for n in recaps[0][1:]):
            raise SystemExit('Missing or failed Ansible recap')
        if pass_no == 2 and int(recaps[0][0]) != 0:
            raise SystemExit('Second apply was not idempotent')
        marker = home / '.dotm-ci-marker'
        if not marker.is_symlink() or marker.resolve() != files / '.dotm-ci-marker' or marker.read_text() != 'dotm isolated role fixture\n':
            raise SystemExit('Target link/content verification failed')
    print(json.dumps({'profile': profile, 'state_verified': True, 'second_apply_changed': 0,
                      'scope': 'synthetic root-level dotfile via pinned role; no packages/services/hardware'}))
