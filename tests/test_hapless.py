def test_get_next_hap_id(hapless):
    result = hapless._get_next_hap_id()
    assert result == 1


def test_get_hap_dirs_empty(hapless):
    result = hapless._get_hap_dirs()
    assert result == []


def test_get_hap_dirs_with_hap(hapless, hap):
    result = hapless._get_hap_dirs()
    assert result == [hap.hid]
