"""Fleet registry and bootstrap playbook (card t_8f9eeb22): inventory/fleet.yml + playbooks/bootstrap.yml.

Schema and boundary tests need only PyYAML. The playbook tests run ansible-playbook against a local-connection
copy of the inventory with a scratch HOME and a stub hermes-agents checkout: no network, no real HOME, no ssh.
"""
import copy
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
FLEET = ROOT / 'inventory' / 'fleet.yml'
PLAYBOOK = ROOT / 'playbooks' / 'bootstrap.yml'
PROFILES = ROOT / 'playbooks' / 'profiles.yml'
ANSIBLE = shutil.which('ansible-playbook')
needs_ansible = pytest.mark.skipif(ANSIBLE is None, reason='ansible-playbook not installed')

REQUIRED = ['class', 'home', 'capabilities', 'agents', 'repos', 'backup_target', 'peer_gateway', 'ssh']


def load():
    return yaml.safe_load(FLEET.read_text())


def hosts():
    return load()['all']['hosts']


def test_the_two_known_hosts_are_registered():
    h = hosts()
    assert 'eg-laptop' in h and 'personal-mini' in h


def test_groups_follow_home():
    d = load()['all']
    for group, members in d['children'].items():
        assert set(members['hosts']) <= set(d['hosts']), group
        for name in members['hosts']:
            assert d['hosts'][name]['home'] == group, f'{name} is in group {group} but home={d["hosts"][name]["home"]}'
    grouped = {n for g in d['children'].values() for n in g['hosts']}
    assert grouped == set(d['hosts']), 'every host belongs to exactly its home group'


@pytest.mark.parametrize('name', ['eg-laptop', 'personal-mini'])
def test_row_has_every_registry_field(name):
    row = hosts()[name]
    d = load()['all']['vars']
    assert all(k in row for k in REQUIRED), [k for k in REQUIRED if k not in row]
    assert row['class'] in d['fleet_classes']
    assert row['home'] in d['fleet_homes']
    assert set(row['agents']) <= {'personal', 'work', 'bridge'}
    assert set(row['ssh']) == {'user', 'host', 'key'}


def test_capabilities_are_declared_or_informational():
    known = set(yaml.safe_load(PROFILES.read_text())['declared_capabilities']) | set(load()['all']['vars']['informational_capabilities'])
    for name, row in hosts().items():
        assert set(row['capabilities']) <= known, (name, set(row['capabilities']) - known)


def test_a_personal_home_never_carries_work_scope_agents():
    d = load()['all']
    assert 'work' not in d['vars']['home_scopes']['personal']
    for name, row in d['hosts'].items():
        allowed = set(d['vars']['home_scopes'][row['home']])
        listed = {scope for scope, agents in row['agents'].items() if agents}
        assert listed <= allowed, (name, listed - allowed)
    for name in d['children']['personal']['hosts']:
        assert not d['hosts'][name]['agents'].get('work'), name


def test_no_key_material_or_email_in_this_public_file():
    text = FLEET.read_text()
    assert not re.search(r'BEGIN [A-Z ]*PRIVATE|ssh-(rsa|ed25519) AAAA|ops_[A-Za-z0-9]{10}|sk-ant|op://', text)
    assert '@' not in text
    for name, row in hosts().items():
        assert re.fullmatch(r'[A-Za-z0-9._-]+', row['ssh']['key']), name


# --- ansible ---------------------------------------------------------------------------------------------------

def env_for(home):
    e = dict(os.environ, HOME=str(home), ANSIBLE_NOCOLOR='1', ANSIBLE_HOME=str(home / '.ansible'),
             ANSIBLE_LOCAL_TEMP=str(home / '.ansible' / 'tmp'), ANSIBLE_HOST_KEY_CHECKING='False')
    e.pop('ANSIBLE_CONFIG', None)
    return e


def local_inventory(tmp_path, mutate=None):
    d = load()
    for row in d['all']['hosts'].values():
        row['ansible_connection'] = 'local'
        row.pop('ansible_host', None)
        row.pop('ansible_user', None)
    if mutate:
        mutate(d['all']['hosts'])
    p = tmp_path / 'fleet.yml'
    p.write_text(yaml.safe_dump(d))
    return p


def stub_agents(tmp_path, built):
    root = tmp_path / 'hermes-agents'
    (root / '.git').mkdir(parents=True)
    (root / 'scripts').mkdir()
    (root / 'scripts' / 'build.py').write_text(
        'import os, sys\nd = os.environ["HERMES_AGENTS_DIST"]\nos.makedirs(d, exist_ok=True)\n'
        'open(os.path.join(d, ".built"), "w").write("\\n".join(%r) + "\\n")\n' % (list(built),))
    return root


def scratch_home(tmp_path, caps, extra=None):
    home = tmp_path / 'home'
    (home / '.config' / 'dotm').mkdir(parents=True)
    (home / 'src' / 'dotfiles' / '.git').mkdir(parents=True)
    cfg = {'dotfiles_repo': '~/src/dotfiles', 'role': None, 'capabilities': caps, 'excluded_modules': ['workmux'],
           'sync': {'interval_minutes': 30, 'auto_apply': True}}
    cfg.update(extra or {})
    (home / '.config' / 'dotm' / 'config.yml').write_text(yaml.safe_dump(cfg))
    return home


def run_playbook(inv, home, agents_root, *args, host='eg-laptop'):
    cmd = [ANSIBLE, str(PLAYBOOK), '-i', str(inv), *args, '-e', f'hermes_agents_dir={agents_root}']
    if host:
        cmd += ['-l', host]
    return subprocess.run(cmd, cwd=ROOT, env=env_for(home), capture_output=True, text=True, timeout=600)


def recap(out, host='eg-laptop'):
    m = re.search(rf'^{host}\s*:\s*(.*)$', out, re.M)
    return {k: int(v) for k, v in re.findall(r'(\w+)=(\d+)', m.group(1))} if m else {}


@needs_ansible
def test_syntax_and_inventory_parse(tmp_path):
    env = env_for(tmp_path)
    r = subprocess.run([ANSIBLE, str(PLAYBOOK), '--syntax-check', '-l', 'eg-laptop'], cwd=ROOT, env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    inv = subprocess.run([shutil.which('ansible-inventory'), '--list'], cwd=ROOT, env=env, capture_output=True, text=True)
    assert inv.returncode == 0, inv.stderr
    assert {'eg-laptop', 'personal-mini'} <= set(json.loads(inv.stdout)['_meta']['hostvars'])


@needs_ansible
def test_check_is_clean_on_a_converged_host(tmp_path):
    row = hosts()['eg-laptop']
    declared = set(yaml.safe_load(PROFILES.read_text())['declared_capabilities'])
    home = scratch_home(tmp_path, sorted(set(row['capabilities']) & declared))
    before = (home / '.config' / 'dotm' / 'config.yml').read_bytes()
    agents = stub_agents(tmp_path, [a for v in row['agents'].values() for a in v])
    r = run_playbook(local_inventory(tmp_path), home, agents, '--check')
    assert r.returncode == 0, r.stdout + r.stderr
    rc = recap(r.stdout)
    assert rc['changed'] == 0 and rc['failed'] == 0 and rc['unreachable'] == 0, r.stdout
    assert (home / '.config' / 'dotm' / 'config.yml').read_bytes() == before, '--check must not write'


@needs_ansible
def test_check_reports_capability_drift_and_writes_nothing(tmp_path):
    row = hosts()['eg-laptop']
    home = scratch_home(tmp_path, ['hermes-host'])  # inventory also declares llm-proxy-host
    before = (home / '.config' / 'dotm' / 'config.yml').read_bytes()
    agents = stub_agents(tmp_path, [a for v in row['agents'].values() for a in v])
    r = run_playbook(local_inventory(tmp_path), home, agents, '--check')
    assert r.returncode == 0, r.stdout + r.stderr
    assert recap(r.stdout)['changed'] == 1, r.stdout
    assert (home / '.config' / 'dotm' / 'config.yml').read_bytes() == before


@needs_ansible
def test_check_diff_shows_the_inventory_capabilities_and_keeps_other_keys(tmp_path):
    row = hosts()['eg-laptop']
    home = scratch_home(tmp_path, [], extra={'capabilities': ['llm-proxy-host', 'stale-cap']})
    agents = stub_agents(tmp_path, [a for v in row['agents'].values() for a in v])
    r = run_playbook(local_inventory(tmp_path), home, agents, '--check', '--diff')
    assert r.returncode == 0, r.stdout + r.stderr
    assert 'stale-cap' in r.stdout and 'hermes-host' in r.stdout, 'the diff shows the capability change'
    cfg = yaml.safe_load((home / '.config' / 'dotm' / 'config.yml').read_text())
    assert cfg['excluded_modules'] == ['workmux'], 'unrelated keys are never touched'


@needs_ansible
def test_refuses_without_a_single_limit(tmp_path):
    row = hosts()['eg-laptop']
    home = scratch_home(tmp_path, row['capabilities'])
    agents = stub_agents(tmp_path, ['it'])
    r = run_playbook(local_inventory(tmp_path), home, agents, '--check', host=None)
    assert r.returncode != 0
    assert 'one host at a time' in r.stdout + r.stderr


@needs_ansible
def test_refuses_a_host_that_is_not_in_the_inventory(tmp_path):
    home = scratch_home(tmp_path, [])
    agents = stub_agents(tmp_path, ['it'])
    r = run_playbook(local_inventory(tmp_path), home, agents, '--check', host='not-a-fleet-host')
    assert r.returncode != 0


@needs_ansible
def test_refuses_work_scope_agents_on_a_personal_host(tmp_path):
    def mutate(h):
        h['personal-mini']['agents']['work'] = ['some-eg-agent']
    home = scratch_home(tmp_path, [])
    agents = stub_agents(tmp_path, ['it'])
    r = run_playbook(local_inventory(tmp_path, mutate), home, agents, '--check', host='personal-mini')
    assert r.returncode != 0
    assert "may carry scopes bridge, personal" in r.stdout + r.stderr


@needs_ansible
def test_refuses_an_agent_the_scopes_cannot_build(tmp_path):
    row = hosts()['eg-laptop']
    wanted = [a for v in row['agents'].values() for a in v]
    home = scratch_home(tmp_path, ['hermes-host', 'llm-proxy-host'])
    agents = stub_agents(tmp_path, [a for a in wanted if a != 'it'])
    r = run_playbook(local_inventory(tmp_path), home, agents, '--check')
    assert r.returncode != 0
    assert 'do not build' in r.stdout + r.stderr and 'it' in r.stdout


@needs_ansible
def test_refuses_an_undeclared_capability(tmp_path):
    def mutate(h):
        h['eg-laptop']['capabilities'] = h['eg-laptop']['capabilities'] + ['typo-capability']
    home = scratch_home(tmp_path, [])
    agents = stub_agents(tmp_path, ['it'])
    r = run_playbook(local_inventory(tmp_path, mutate), home, agents, '--check')
    assert r.returncode != 0
    assert 'is malformed' in r.stdout + r.stderr
