import json
import os
from pathlib import Path
from typing import Dict
from unittest.mock import Mock, PropertyMock, patch

import pytest

from hapless.hap import Hap

# from hapless.main import Hapless


@pytest.fixture
def write_env_factory():
    def write_env(target_path: Path, env_mapping: Dict[str, str]):
        with open(target_path, "w") as f:
            f.write(json.dumps(env_mapping))

    return write_env


def test_empty_env_provided_on_creation(tmp_path):
    hap = Hap(tmp_path, cmd="true", env={})
    assert hap.pid is None
    assert hap.proc is None
    assert hap.rc is None
    assert not hap.active
    assert hap.env == {}


@patch.dict(os.environ, {"ENV_KEY": "TEST_VALUE"}, clear=True)
def test_env_defaults_to_current_env_if_none(tmp_path):
    hap = Hap(tmp_path, cmd="false")
    assert hap.pid is None
    assert hap.proc is None
    assert hap.rc is None
    assert not hap.active
    assert hap.env == {"ENV_KEY": "TEST_VALUE"}


@pytest.mark.parametrize("env_mapping", [{}, {"ENV_KEY": "TEST_VALUE"}])
def test_fallsback_to_env_file_if_proc_returns_nothing(
    hap: Hap,
    write_env_factory,
    env_mapping,
):
    write_env_factory(hap._env_file, env_mapping)
    assert hap.proc is None
    proc_mock = Mock()
    proc_mock.environ = Mock(return_value={})
    prop_mock = PropertyMock(return_value=proc_mock)
    with patch.object(type(hap), "proc", prop_mock):
        assert hap.proc is proc_mock
        assert hap.env == env_mapping


def test_proc_env_is_used_as_primaty_source(hap: Hap, write_env_factory):
    write_env_factory(hap._env_file, {"ENV_KEY": "ENV_VALUE_FROM_FILE"})
    assert hap.proc is None
    proc_mock = Mock()
    proc_mock.environ = Mock(return_value={"ENV_KEY": "ENV_VALUE_FROM_PROC"})
    prop_mock = PropertyMock(return_value=proc_mock)
    with patch.object(type(hap), "proc", prop_mock):
        assert hap.proc is proc_mock
        assert hap.env == {"ENV_KEY": "ENV_VALUE_FROM_PROC"}


# def test_correct_env_is_picked_up():
#     hapless = Hapless()
# hap = hapless.create_hap(
#     cmd="python -c 'import os; print(os.getenv(\"HAPLESS_TEST_ENV_VAR\"))'",
#     name="hap-env-test",
#     env={"HAPLESS_TEST_ENV_VAR": "hapless_env_value"},
# )

# hapless.run_hap(hap, blocking=True)
# assert hap.rc == 0
# assert hap.stdout_path.exists()
# assert hap.stdout_path.read_text().strip() == "hapless_env_value"


# def test_env_preserved_on_restart(hapless: Hapless):
#     hap = hapless.create_hap(
#         cmd="python -c 'import os; print(os.getenv(\"HAPLESS_TEST_ENV_VAR\"))'",
#         name="hap-env-restart-test",
#         env={"HAPLESS_TEST_ENV_VAR": "hapless_env_value_restart"},
#     )

#     hapless.run_hap(hap, blocking=True)
#     assert hap.rc == 0
#     assert hap.stdout_path.exists()
#     assert hap.stdout_path.read_text().strip() == "hapless_env_value_restart"

#     hapless.restart(hap)
#     assert hap.rc == 0
#     assert hap.stdout_path.exists()
#     # The output will be appended on restart
#     outputs = hap.stdout_path.read_text().strip().splitlines()
#     assert outputs[-1] == "hapless_env_value_restart"


# def test_env_is_populated_on_empty_env(hapless: Hapless):
#     hap = hapless.create_hap(
#         cmd="python -c 'import os; print(os.getenv(\"HAPLESS_TEST_ENV_VAR\"))'",
#         name="hap-env-empty-test",
#         env={},
#     )

#     hapless.run_hap(hap, blocking=True)
#     assert hap.rc == 0
#     assert hap.stdout_path.exists()
#     # The variable should not be set
#     assert hap.stdout_path.read_text().strip() == "None"


# def test_restart_uses_same_working_dir(hapless: Hapless, monkeypatch):
#     monkeypatch.chdir(EXAMPLES_DIR)
#     hap = hapless.create_hap(
#         cmd="python ./samename.py",
#         name="hap-same-name",
#     )
#     hid = hap.hid
#     assert hap.workdir == EXAMPLES_DIR

#     hapless.run_hap(hap, blocking=True)
#     assert hap.rc == 0
#     assert hap.stdout_path.exists()
#     assert "Correct file is being run" in hap.stdout_path.read_text()

#     # Contains script with the same filename
#     monkeypatch.chdir(EXAMPLES_DIR / "nested")

#     original_run = hapless.run_command

#     def blocking_run(*args, **kwargs):
#         kwargs["blocking"] = True
#         return original_run(*args, **kwargs)

#     with patch.object(hapless, "run_command", side_effect=blocking_run) as run_mock:
#         hapless.restart(hap)
#         run_mock.assert_called_once_with(
#             cmd="python ./samename.py",
#             workdir=EXAMPLES_DIR,
#             hid=hid,
#             name="hap-same-name@1",
#             redirect_stderr=False,
#         )

#     restarted_hap = hapless.get_hap("hap-same-name")
#     assert restarted_hap is not None
#     assert restarted_hap.rc == 0
#     assert restarted_hap.stdout_path.exists()
#     assert "Correct file is being run" in restarted_hap.stdout_path.read_text()
#     assert "Malicious code execution" not in restarted_hap.stdout_path.read_text()
