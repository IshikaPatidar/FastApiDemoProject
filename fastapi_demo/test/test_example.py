import pytest

def test_equals_or_not():
    assert 3 == 3


def test_is_instance():
    assert isinstance('thi is string', str)
    assert not isinstance('10', int)


def test_boolean():
    validated = True
    assert validated is True
    assert ('hello' == 'world') is False


def test_type():
    assert type('hello' is str)
    assert type('10' is not int)


def test_greater_and_less_than():
    assert 7 < 9
    assert 3 > 1


def test_list():
    num_list = [1, 2, 3, 4, 5]
    any_list = [False, False]
    assert 1 in num_list
    assert 7 not in num_list
    assert all(num_list)
    assert not any(any_list)

