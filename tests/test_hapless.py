def test_get_next_hap_id(hapless):
    result = hapless._get_next_hap_id()
    assert result == "1"


def test_get_hap_dirs_empty(hapless):
    result = hapless._get_hap_dirs()
    assert result == []


def test_get_hap_dirs_with_hap(hapless, hap):
    result = hapless._get_hap_dirs()
    assert result == [hap.hid]


def test_create_hap(hapless):
    result = hapless.create_hap("echo hello")
    assert result.cmd == "echo hello"
    assert result.hid == "1"
    assert result.name is not None
    assert isinstance(result.name, str)
    assert result.name.startswith("hap-")


def test_create_hap_custom_hid(hapless):
    result = hapless.create_hap(cmd="echo hello", hid="42", name="hap-name")
    assert result.cmd == "echo hello"
    assert result.hid == "42"
    assert result.name == "hap-name"


def test_get_hap_works_with_restarts(hapless):
    raw_name = "hap-name@2"
    hapless.create_hap(cmd="true", name=raw_name)
    hap = hapless.get_hap(hap_alias="hap-name")
    assert hap is not None
    assert hap.raw_name == raw_name
    assert hap.name == "hap-name"

    # Check ignoring restarts suffix
    no_hap = hapless.get_hap(hap_alias=raw_name)
    assert no_hap is None
