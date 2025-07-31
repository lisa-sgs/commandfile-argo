import json
from pathlib import Path

from pytest import MonkeyPatch

from commandfile_argo.generator import generate_commandfile


def test_generate_commandfile(monkeypatch: MonkeyPatch, tmp_path: Path):
    argo_template = {
        "inputs": {"artifacts": [{"name": "input1", "path": "/path/to/input1"}]},
        "outputs": {"artifacts": [{"name": "output1", "path": "/path/to/output1"}]},
    }
    parameters = [
        {"name": "param1", "value": "value1"},
        {"name": "param2", "value": '["file1", "file2"]'},
    ]
    monkeypatch.setenv("ARGO_TEMPLATE", json.dumps(argo_template))
    monkeypatch.setenv("INPUTS_PARAMETERS", json.dumps(parameters))

    filename = tmp_path / "commandfile.yaml"
    generate_commandfile(filename)

    assert filename.exists()
