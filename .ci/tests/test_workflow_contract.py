import json
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = json.loads((ROOT / '.ci/contract.json').read_text())
WORKFLOW = yaml.safe_load((ROOT / '.github/workflows/verify.yml').read_text())
JOBS = WORKFLOW['jobs']


def test_every_required_profile_has_a_job_that_runs_exactly_it():
    for profile in CONTRACT['required_profiles']:
        assert profile in JOBS, f'{profile} has no workflow job'
        runs = [s['run'] for s in JOBS[profile]['steps'] if 'run' in s and 'verify.py run' in s['run']]
        assert runs == [f'python .ci/verify.py run {profile}'], f'{profile} job runs {runs}'


def test_acceptance_needs_exactly_the_required_profiles_and_names_them_in_its_env():
    acceptance = JOBS['acceptance']
    assert set(acceptance['needs']) == set(CONTRACT['required_profiles'])
    step = next(s for s in acceptance['steps'] if 'env' in s and 'VERIFICATION_NEEDS' in s['env'])
    named = set(json.loads(step['env']['VERIFICATION_NEEDS'].replace('${{ ', '').replace(' }}', '').replace('needs.', '').replace('.result', '')))
    assert named == set(CONTRACT['required_profiles'])


def test_every_job_has_a_timeout_and_the_slow_profile_is_bounded_by_it():
    for name, job in JOBS.items():
        assert job.get('timeout-minutes'), f'{name} has no timeout'
    # a profile command may not outlive its job: the per-command cap, in minutes, fits inside the job timeout
    for profile, spec in CONTRACT['profiles'].items():
        cap = spec.get('command_timeout_seconds', CONTRACT['command_timeout_seconds']) / 60
        assert cap * len(spec['checks']) <= JOBS[profile]['timeout-minutes'] + 5, f'{profile}: command caps exceed the job timeout'


def test_fleet_receipt_sees_every_job_and_runs_even_when_they_fail():
    receipt = JOBS['fleet-receipt']
    assert receipt['if'] == 'always()'
    assert set(receipt['needs']) == set(JOBS) - {'fleet-receipt'}
    step = next(s for s in receipt['steps'] if 'env' in s and 'FLEET_NEEDS' in s['env'])
    for need in receipt['needs']:
        assert f'needs.{need}.result' in step['env']['FLEET_NEEDS']


def test_the_macos_fixture_declares_hermes_host():
    text = (ROOT / '.ci/platform_fixture.py').read_text()
    assert "'hermes-host'" in text and 'hermes-platform' in text
