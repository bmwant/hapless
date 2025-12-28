import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from hapless.main import Hapless

TESTS_DIR = Path(__file__).parent
EXAMPLES_DIR = TESTS_DIR.parent / "examples"


def test_restart_uses_same_working_dir(hapless: Hapless, monkeypatch):
    monkeypatch.chdir(EXAMPLES_DIR)
    python_exec = shutil.which("python")
    with patch.dict("os.environ", {"TESTING": "true"}, clear=True):
        hap = hapless.create_hap(
            cmd=f"{python_exec} ./samename.py",
            name="hap-same-name",
        )
    hid = hap.hid
    assert hap.workdir == EXAMPLES_DIR

    hapless.run_hap(hap, blocking=True)
    assert hap.rc == 0
    assert hap.stdout_path.exists()
    assert "Correct file is being run" in hap.stdout_path.read_text()

    # Contains script with the same filename
    monkeypatch.chdir(EXAMPLES_DIR / "nested")

    original_run = hapless.run_command

    def blocking_run(*args, **kwargs):
        kwargs["blocking"] = True
        return original_run(*args, **kwargs)

    with patch.object(hapless, "run_command", side_effect=blocking_run) as run_mock:
        hapless.restart(hap)
        run_mock.assert_called_once_with(
            cmd=f"{python_exec} ./samename.py",
            env={"TESTING": "true"},
            workdir=EXAMPLES_DIR,
            hid=hid,
            name="hap-same-name@1",
            redirect_stderr=False,
        )

    restarted_hap = hapless.get_hap("hap-same-name")
    assert restarted_hap is not None
    assert restarted_hap.rc == 0
    assert restarted_hap.stdout_path.exists()
    assert "Correct file is being run" in restarted_hap.stdout_path.read_text()
    assert "Malicious code execution" not in restarted_hap.stdout_path.read_text()


def test_same_workdir_is_used_even_on_dir_change(hapless: Hapless, monkeypatch):
    monkeypatch.chdir(EXAMPLES_DIR)
    hap = hapless.create_hap(
        cmd="python -c 'import os; print(os.getcwd())'",
        name="hap-workdir",
    )
    assert hap.workdir == EXAMPLES_DIR

    monkeypatch.chdir(TESTS_DIR)
    hapless.run_hap(hap, blocking=True)
    assert hap.rc == 0
    assert hap.stdout_path.exists()
    assert f"{EXAMPLES_DIR}" in hap.stdout_path.read_text()
    assert f"{TESTS_DIR}" not in hap.stdout_path.read_text()


def test_different_scripts_called_if_directory_differs(hapless: Hapless, monkeypatch):
    monkeypatch.chdir(EXAMPLES_DIR)
    same_cmd = "python ./samename.py"
    hap1 = hapless.create_hap(
        cmd=same_cmd,
        name="hap-same-cmd-1",
    )
    assert hap1.workdir == EXAMPLES_DIR

    hapless.run_hap(hap1, blocking=True)
    assert hap1.rc == 0
    assert hap1.stdout_path.exists()
    assert "Correct file is being run" in hap1.stdout_path.read_text()

    # Contains script with the same filename
    monkeypatch.chdir(EXAMPLES_DIR / "nested")
    hap2 = hapless.create_hap(
        cmd=same_cmd,
        name="hap-same-cmd-2",
    )
    assert hap2.workdir == EXAMPLES_DIR / "nested"

    hapless.run_hap(hap2, blocking=True)
    assert hap2.rc == 0
    assert hap2.stdout_path.exists()
    assert "Malicious code execution" in hap2.stdout_path.read_text()

    assert hap1.cmd == hap2.cmd
    assert hap1.workdir != hap2.workdir


def test_incorrect_workdir_provided(hapless: Hapless, tmp_path):
    not_a_dir = tmp_path / "filename"
    not_a_dir.touch()
    with pytest.raises(ValueError) as e:
        hap = hapless.create_hap(cmd="false", workdir=not_a_dir)  # noqa: F841

    assert str(e.value) == "Workdir should be a path to existing directory"


def test_fallback_workdir_to_current_dir(
    hapless: Hapless, monkeypatch, tmp_path_factory
):
    fallback_workdir = tmp_path_factory.mktemp("hap_fallback_workdir")
    monkeypatch.chdir(fallback_workdir)
    hap = hapless.create_hap(
        cmd="true",
        workdir=None,
        name="hap-workdir-fallback",
    )
    assert hap.workdir == fallback_workdir
    assert hapless.dir != hap.workdir
