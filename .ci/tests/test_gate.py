import copy
import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location('verify', Path(__file__).resolve().parents[1] / 'verify.py')
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)


def fixture():
    contract = {'required_profiles': ['fast', 'mac'], 'receipt_max_age_seconds': 100,
                'profiles': {n: {'checks': [['python', 'test']]} for n in ['fast', 'mac']}}
    identity = {'commit': 'a'*40, 'input_sha256': 'b'*64, 'contract_sha256': 'c'*64}
    receipts = [{'profile': n, 'identity': identity.copy(), 'status': 'passed', 'inputs_unchanged': True,
                 'finished_at': 90, 'checks': [{'command': ['python','test'], 'exit_code': 0}]} for n in ['fast','mac']]
    return contract, identity, receipts


def test_all_required_checks_pass():
    c, i, r = fixture()
    assert verify.validate_receipts(c, i, r, {'fast':'success','mac':'success'}, now=100)


@pytest.mark.parametrize('field', ['commit','input_sha256','contract_sha256'])
def test_stale_identity_is_rejected(field):
    c,i,r=fixture(); r[0]['identity'][field]='different'
    with pytest.raises(ValueError): verify.validate_receipts(c,i,r,now=100)


@pytest.mark.parametrize('state', ['failure','skipped','cancelled','pending'])
def test_required_job_cannot_be_skipped(state):
    c,i,r=fixture()
    with pytest.raises(ValueError): verify.validate_receipts(c,i,r,{'fast':'success','mac':state},now=100)


@pytest.mark.parametrize('mutation', ['missing','duplicate','failed','empty','command','expired','future','mutated'])
def test_bad_receipts_fail_closed(mutation):
    c,i,r=fixture()
    if mutation=='missing': r.pop()
    if mutation=='duplicate': r[1]=copy.deepcopy(r[0])
    if mutation=='failed': r[0]['checks'][0]['exit_code']=1
    if mutation=='empty': r[0]['checks']=[]
    if mutation=='command': r[0]['checks'][0]['command']=['true']
    if mutation=='expired': r[0]['finished_at']=-1
    if mutation=='future': r[0]['finished_at']=101
    if mutation=='mutated': r[0]['inputs_unchanged']=False
    with pytest.raises(ValueError): verify.validate_receipts(c,i,r,now=100)


def test_identity_tracks_uncommitted_content_and_permissions(tmp_path, monkeypatch):
    (tmp_path / ".ci").mkdir()
    (tmp_path / ".ci/contract.json").write_text("{}")
    source = tmp_path / "new.py"
    source.write_text("first")
    def git(argv, **kwargs):
        return b"new.py\0.ci/contract.json\0" if "ls-files" in argv else b"a" * 40
    monkeypatch.setattr(verify.subprocess, "check_output", git)
    first = verify.identity(tmp_path)
    source.write_text("second")
    second = verify.identity(tmp_path)
    assert first["commit"] == second["commit"]
    assert first["input_sha256"] != second["input_sha256"]
    source.chmod(0o755)
    assert verify.identity(tmp_path)["input_sha256"] != second["input_sha256"]


def test_platform_fixture_refuses_non_ci_execution():
    import os
    import subprocess
    import sys
    path = Path(__file__).resolve().parents[1] / "platform_fixture.py"
    result = subprocess.run([sys.executable, str(path), "macos"],
                            env={**os.environ, "GITHUB_ACTIONS": "false"}, capture_output=True, text=True)
    assert result.returncode != 0
    assert "Refusing apply" in result.stderr
