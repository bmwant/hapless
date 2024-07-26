from hapless.hap import Hap


def all_equal(iterable):
    return len(set(iterable)) <= 1


def test_random_name_generation():
    name_length = 8
    name_count = 4
    names = []
    for _ in range(name_count):
        new_name = Hap.get_random_name(length=name_length)
        assert len(new_name) == name_length
        names.append(new_name)

    assert not all_equal(names)


def test_runtime_():
    pass
