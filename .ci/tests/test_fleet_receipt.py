import datetime
import importlib.util
import json
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location('fleet_receipt', Path(__file__).resolve().parents[1] / 'fleet_receipt.py')
fleet = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fleet)

NOW = datetime.datetime(2026, 10, 15, 13, 30, 5, tzinfo=datetime.timezone.utc)
ENV = {'GITHUB_REPOSITORY': 'owner/repo', 'GITHUB_RUN_ID': '123', 'GITHUB_RUN_ATTEMPT': '1',
       'GITHUB_SHA': 'a' * 40, 'GITHUB_REF_NAME': 'main', 'GITHUB_EVENT_NAME': 'push'}
GREEN = {'fast': 'success', 'macos-fixture': 'success', 'macos-hermes': 'success',
         'linux-arm-fixture': 'success', 'acceptance': 'success'}


def test_green_run_is_one_success_row():
    doc = fleet.build(GREEN, ENV, NOW)
    assert (doc['routine'], doc['profile'], doc['period'], doc['run_id'], doc['commit']) == \
        ('ci-verify', 'dotfiles', '2026-10-15', '123', 'a' * 40)
    assert doc['conclusion'] == 'success' and doc['probe_exit'] == 0
    assert doc['jobs'] == dict(sorted(GREEN.items()))
    assert doc['url'] == 'https://github.com/owner/repo/actions/runs/123'


@pytest.mark.parametrize('state', ['failure', 'cancelled', 'skipped'])
def test_any_job_that_is_not_success_makes_the_run_red(state):
    doc = fleet.build({**GREEN, 'macos-hermes': state}, ENV, NOW)
    assert doc['conclusion'] == 'failure' and doc['probe_exit'] == 1
    assert doc['jobs']['macos-hermes'] == state


def test_no_job_results_is_an_error_not_a_green_run():
    with pytest.raises(ValueError):
        fleet.build({}, ENV, NOW)


def test_main_writes_the_file_and_reports_bad_input(tmp_path, monkeypatch):
    out = tmp_path / 'fleet-receipt.json'
    monkeypatch.setenv('FLEET_NEEDS', json.dumps(GREEN))
    assert fleet.main(['x', str(out)]) == 0
    assert json.loads(out.read_text())['conclusion'] == 'success'
    monkeypatch.setenv('FLEET_NEEDS', 'not json')
    assert fleet.main(['x', str(tmp_path / 'bad.json')]) == 1
    assert not (tmp_path / 'bad.json').exists()
