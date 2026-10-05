"""Fast syntax/config checks; no installation, shell execution or secret scanning."""
import ast
from pathlib import Path
import sys
import yaml

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'modules/dotm/src'))
from dotm.modules import module_requires

for folder in [root / 'modules/dotm/src', root / '.ci']:
    for path in folder.rglob('*.py'):
        if any(p in {'.venv', 'vendor', 'results'} for p in path.parts):
            continue
        ast.parse(path.read_text(), filename=str(path))
for path in list((root / 'modules').glob('*/config.yml')) + list((root / 'playbooks').glob('*.yml')) + list((root / '.ci').glob('*.yml')) + list((root / '.github/workflows').glob('*.yml')):
    data = yaml.safe_load(path.read_text())
    if path.name == 'config.yml':
        if not isinstance(data, dict):
            raise ValueError(f'{path}: module config must be a mapping')
        module_requires(data, path.parent.name)
print('Python syntax and repository YAML/module configuration checks passed.')
