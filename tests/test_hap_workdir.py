import os
from pathlib import Path
from unittest.mock import patch

from hapless.main import Hapless

TESTS_DIR = Path(__file__).parent
EXAMPLES_DIR = TESTS_DIR.parent / "examples"


def test_restart_uses_same_working_dir(hapless: Hapless, monkeypatch):
    monkeypatch.chdir(EXAMPLES_DIR)
    hap = hapless.create_hap(
        cmd="python ./samename.py",
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
    # here we need blocking True mocking
    original_run = hapless.run_command

    def blocking_run(*args, **kwargs):
        kwargs["blocking"] = True
        return original_run(*args, **kwargs)

    with patch.object(hapless, "run_command", side_effect=blocking_run) as run_mock:
        hapless.restart(hap)
        run_mock.assert_called_once_with(
            cmd="python ./samename.py",
            workdir=EXAMPLES_DIR,
            hid=hid,
            name="hap-same-name@1",
            redirect_stderr=False,
        )

    restarted_hap = hapless.get_hap("hap-same-name")
    assert restarted_hap.rc == 0
    assert restarted_hap.stdout_path.exists()
    assert "Correct file is being run" in restarted_hap.stdout_path.read_text()
    assert "Malicious code execution" not in restarted_hap.stdout_path.read_text()


def test_same_workdir_is_used_even_on_dir_change():
    pass


def test_different_scripts_called_if_directory_differs():
    pass
